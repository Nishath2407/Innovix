from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.safety_plan import SafetyPlan, TrustedContact

safety_bp = Blueprint("safety", __name__)


@safety_bp.route("/safety-plan", methods=["GET"])
@jwt_required()
def get_safety_plan():
    user_id = get_jwt_identity()
    plan = SafetyPlan.query.filter_by(user_id=user_id).first()
    if not plan:
        return jsonify({"safety_plan": None})
    return jsonify({"safety_plan": plan.to_dict()})


@safety_bp.route("/safety-plan", methods=["PUT"])
@jwt_required()
def update_safety_plan():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    plan = SafetyPlan.query.filter_by(user_id=user_id).first()
    if not plan:
        plan = SafetyPlan(user_id=user_id)
        db.session.add(plan)

    if "safe_locations" in data and isinstance(data["safe_locations"], list):
        plan.safe_locations = data["safe_locations"][:20]
    if "personal_reminders" in data:
        plan.personal_reminders = (data["personal_reminders"] or "")[:2000]

    if "trusted_contacts" in data and isinstance(data["trusted_contacts"], list):
        # Replace wholesale for simplicity in Phase 1.
        for c in list(plan.trusted_contacts):
            db.session.delete(c)
        for c in data["trusted_contacts"][:10]:
            db.session.add(TrustedContact(
                safety_plan=plan,
                name=(c.get("name") or "").strip()[:120],
                phone=(c.get("phone") or "").strip()[:30],
                relationship=(c.get("relationship") or "").strip()[:60],
            ))

    db.session.commit()
    return jsonify({"safety_plan": plan.to_dict()})
