import secrets
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.constants import LANGUAGES, CONCERNS
from app.models.user import User
from app.models.journal_entry import JournalEntry
from app.models.emotion_result import EmotionResult
from app.models.risk_assessment import RiskAssessment
from app.models.safety_plan import SafetyPlan
from app.models.notification import Notification
from app.models.recovery import RecoveryProgress
from app.utils.audit import log_action

users_bp = Blueprint("users", __name__)


def _me():
    return db.session.get(User, get_jwt_identity())


@users_bp.route("/me/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user = _me()
    if not user or not user.profile:
        return jsonify({"error": "not_found", "message": "Profile not found."}), 404
    return jsonify({"profile": user.profile.to_dict(), "user": user.to_self_dict()})


@users_bp.route("/me/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = _me()
    data = request.get_json(silent=True) or {}
    profile = user.profile
    if "display_name" in data:
        name = (data["display_name"] or "").strip()
        if not 1 <= len(name) <= 64:
            return jsonify({"error": "validation_error", "message": "Display name must be 1-64 characters."}), 422
        profile.display_name = name
    if "privacy_mode_enabled" in data:
        profile.privacy_mode_enabled = bool(data["privacy_mode_enabled"])
    if data.get("preferred_language") in LANGUAGES:
        profile.preferred_language = data["preferred_language"]
    if isinstance(data.get("concerns"), list):
        profile.concerns = [c for c in data["concerns"] if c in CONCERNS][:10]
    db.session.commit()
    return jsonify({"message": "Saved.", "profile": profile.to_dict(), "user": user.to_self_dict()})


@users_bp.route("/me", methods=["DELETE"])
@jwt_required()
def delete_account():
    """Removes private content and anonymises the account. Payment and
    appointment records are kept (legal/financial), detached from the person."""
    user = _me()
    if user.role == "admin":
        return jsonify({"error": "forbidden", "message": "Admin accounts can't be deleted here."}), 403
    if not user.check_password((request.get_json(silent=True) or {}).get("password") or ""):
        return jsonify({"error": "unauthorized", "message": "Enter your password to confirm."}), 403

    uid = user.id
    for model in (JournalEntry, EmotionResult, RiskAssessment, Notification, RecoveryProgress):
        model.query.filter_by(user_id=uid).delete()
    plan = SafetyPlan.query.filter_by(user_id=uid).first()
    if plan:
        db.session.delete(plan)
    user.email = f"deleted-{uid}@deleted.invalid"
    user.set_password(secrets.token_urlsafe(24))
    user.is_active = False
    if user.profile:
        user.profile.display_name = "Deleted user"
        user.profile.concerns = []
    log_action(uid, "account_deleted", "user", uid)
    db.session.commit()
    from flask import jsonify as j
    from flask_jwt_extended import unset_jwt_cookies
    resp = j({"message": "Your account and private data were deleted."})
    unset_jwt_cookies(resp)
    return resp
