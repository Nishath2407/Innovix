import re
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies, jwt_required, get_jwt_identity, get_csrf_token,
)
from app.extensions import db, limiter
from app.constants import CONCERNS, LANGUAGES, SESSION_MODES
from app.models.user import User, UserProfile
from app.models.therapist import Therapist, TherapistSpecialization, TherapistLanguage, TherapistCredential
from app.utils.mailer import send_email
from app.utils.audit import log_action
from app.utils.timeutils import utcnow

auth_bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PORTAL_ROLES = {"user": "user", "therapist": "therapist", "admin": "admin"}


def _password_error(pw):
    if len(pw) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        return "Password must include at least one letter and one number."
    return None


def _validate_therapist(data):
    errors, clean = {}, {}
    clean["display_name"] = (data.get("display_name") or "").strip()[:120]
    clean["qualification"] = (data.get("qualification") or "").strip()[:255]
    if not clean["display_name"]:
        errors["display_name"] = "Enter the name clients will see."
    if not clean["qualification"]:
        errors["qualification"] = "Enter your professional qualification."
    try:
        clean["years_experience"] = int(data.get("years_experience", 0))
        assert 0 <= clean["years_experience"] <= 60
    except (TypeError, ValueError, AssertionError):
        errors["years_experience"] = "Enter years of experience (0-60)."
    try:
        clean["session_price"] = int(data.get("session_price"))
        assert 100 <= clean["session_price"] <= 20000
    except (TypeError, ValueError, AssertionError):
        errors["session_price"] = "Enter a session price between 100 and 20000."
    specs = [s for s in (data.get("specializations") or []) if s in CONCERNS]
    langs = [l for l in (data.get("languages") or []) if l in LANGUAGES]
    modes = [m for m in (data.get("session_modes") or list(SESSION_MODES)) if m in SESSION_MODES]
    if not specs:
        errors["specializations"] = "Choose at least one specialization."
    if not langs:
        errors["languages"] = "Choose at least one language."
    if not modes:
        errors["session_modes"] = "Choose at least one session type."
    reg = (data.get("registration_number") or "").strip()[:100]
    body = (data.get("issuing_body") or "").strip()[:150]
    if not reg or not body:
        errors["registration_number"] = "Registration number and issuing body are needed for verification."
    clean.update(
        specializations=specs, languages=langs, session_modes=modes,
        gender=data.get("gender") if data.get("gender") in ("female", "male", "non_binary") else None,
        bio=(data.get("bio") or "").strip()[:2000], approach=(data.get("approach") or "").strip()[:2000],
        registration_number=reg, issuing_body=body)
    return errors, clean


def _csrf(token):
    try:
        return get_csrf_token(token)
    except KeyError:  # CSRF protection disabled (tests)
        return None


def _session_response(user, message):
    access = create_access_token(identity=user.id, additional_claims={"role": user.role})
    refresh = create_refresh_token(identity=user.id, additional_claims={"role": user.role})
    resp = jsonify({"message": message, "user": user.to_self_dict(), "csrf_token": _csrf(access)})
    set_access_cookies(resp, access)
    set_refresh_cookies(resp, refresh)
    return resp


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = "therapist" if data.get("role") == "therapist" else "user"  # admins are never self-registered

    errors = {}
    if not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."
    pw_err = _password_error(password)
    if pw_err:
        errors["password"] = pw_err
    therapist_clean = {}
    if role == "therapist":
        t_errors, therapist_clean = _validate_therapist(data)
        errors.update(t_errors)
    if errors:
        return jsonify({"error": "validation_error", "message": next(iter(errors.values())), "fields": errors}), 422

    if User.query.filter_by(email=email).first():
        # Deliberately vague so registration can't be used to discover which emails exist.
        return jsonify({"error": "conflict", "message": "We couldn't create an account with these details. Try logging in instead."}), 409

    user = User(email=email, role=role)
    user.set_password(password)
    token = user.generate_email_verify_token()
    db.session.add(user)
    db.session.flush()

    display = (data.get("display_name") or "").strip()[:64] or f"Anonymous User #{user.id[:4].upper()}"
    if role == "therapist":
        display = therapist_clean["display_name"]
    db.session.add(UserProfile(user_id=user.id, display_name=display,
                               preferred_language=data.get("preferred_language") if data.get("preferred_language") in LANGUAGES else "en"))

    if role == "therapist":
        t = Therapist(
            user_id=user.id, display_name=therapist_clean["display_name"], qualification=therapist_clean["qualification"],
            bio=therapist_clean["bio"], approach=therapist_clean["approach"], years_experience=therapist_clean["years_experience"],
            gender=therapist_clean["gender"], session_price=therapist_clean["session_price"],
            session_modes_json=therapist_clean["session_modes"], is_verified=False, verification_status="pending")
        db.session.add(t)
        db.session.flush()
        for s in therapist_clean["specializations"]:
            db.session.add(TherapistSpecialization(therapist_id=t.id, name=s))
        for l in therapist_clean["languages"]:
            db.session.add(TherapistLanguage(therapist_id=t.id, language=l))
        db.session.add(TherapistCredential(
            therapist_id=t.id, credential_type=f"Registration — {therapist_clean['issuing_body']}",
            details=therapist_clean["registration_number"], verification_status="pending"))

    db.session.commit()

    link = f"{current_app.config['FRONTEND_URL']}/verify-email?token={token}"
    send_email(email, "Verify your SafeVoice email", f"Welcome to SafeVoice. Confirm your email: {link}")

    msg = ("Application received. Our team will review your credentials before your profile goes live."
           if role == "therapist" else "Account created.")
    return jsonify({"message": msg, "user": user.to_self_dict()}), 201


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    token = (request.get_json(silent=True) or {}).get("token")
    user = User.query.filter_by(email_verify_token=token).first() if token else None
    if not user:
        return jsonify({"error": "bad_request", "message": "This verification link is invalid or has already been used."}), 400
    user.is_email_verified = True
    user.email_verify_token = None
    db.session.commit()
    return jsonify({"message": "Email verified. You're all set."})


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20 per hour")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    portal = PORTAL_ROLES.get(data.get("portal", "user"), "user")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "unauthorized", "message": "Incorrect email or password."}), 401
    if user.role != portal:
        where = {"user": "the client login", "therapist": "the therapist login", "admin": "the admin login"}[user.role]
        return jsonify({"error": "wrong_portal", "message": f"This account uses {where}."}), 403
    if not user.is_active:
        return jsonify({"error": "forbidden", "message": "This account has been suspended. Contact support for help."}), 403
    if current_app.config["REQUIRE_EMAIL_VERIFICATION"] and not user.is_email_verified:
        return jsonify({"error": "unverified", "message": "Please verify your email before logging in."}), 403

    user.last_login_at = utcnow()
    db.session.commit()
    return _session_response(user, "Logged in.")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    resp = jsonify({"message": "Logged out."})
    unset_jwt_cookies(resp)
    return resp


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = db.session.get(User, get_jwt_identity())
    if not user or not user.is_active:
        return jsonify({"error": "unauthorized", "message": "Please log in again."}), 401
    token = request.cookies.get("access_token_cookie")
    return jsonify({"user": user.to_self_dict(), "csrf_token": _csrf(token) if token else None})


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")
def forgot_password():
    email = ((request.get_json(silent=True) or {}).get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user and user.is_active:
        token = user.generate_password_reset_token()
        db.session.commit()
        link = f"{current_app.config['FRONTEND_URL']}/reset-password?token={token}"
        send_email(user.email, "Reset your SafeVoice password", f"Use this link within 30 minutes: {link}")
    return jsonify({"message": "If that email is registered, a reset link is on its way."})


@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("10 per hour")
def reset_password():
    data = request.get_json(silent=True) or {}
    err = _password_error(data.get("password") or "")
    if err:
        return jsonify({"error": "validation_error", "message": err, "fields": {"password": err}}), 422
    token = data.get("token")
    user = User.query.filter_by(password_reset_token=token).first() if token else None
    if not user or not user.password_reset_expires or user.password_reset_expires < utcnow():
        return jsonify({"error": "bad_request", "message": "This reset link is invalid or has expired."}), 400
    user.set_password(data["password"])
    user.password_reset_token = None
    user.password_reset_expires = None
    db.session.commit()
    return jsonify({"message": "Password updated. You can log in now."})


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    data = request.get_json(silent=True) or {}
    user = db.session.get(User, get_jwt_identity())
    if not user.check_password(data.get("current_password") or ""):
        return jsonify({"error": "unauthorized", "message": "Your current password is incorrect."}), 403
    err = _password_error(data.get("new_password") or "")
    if err:
        return jsonify({"error": "validation_error", "message": err, "fields": {"new_password": err}}), 422
    user.set_password(data["new_password"])
    db.session.commit()
    return jsonify({"message": "Password changed."})
