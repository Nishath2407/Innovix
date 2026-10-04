"""Everything a logged-in therapist can do. Clients are only ever identified by
their display name — never email — and private client content is never returned."""
from datetime import datetime, timedelta, time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func
from app.extensions import db
from app.constants import CONCERNS, LANGUAGES, SESSION_MODES
from app.models.user import User
from app.models.therapist import Therapist, TherapistSpecialization, TherapistLanguage, TherapistAvailability, TherapistCredential
from app.models.appointment import Appointment
from app.models.payment import Payment
from app.models.emotion_result import EmotionResult
from app.models.risk_assessment import RiskAssessment
from app.models.review import Review
from app.sessions.service import ensure_session, join_state
from app.utils.decorators import role_required
from app.utils.notify import notify
from app.utils.timeutils import utcnow, utc_to_local

portal_bp = Blueprint("therapist_portal", __name__)


def _me():
    return Therapist.query.filter_by(user_id=get_jwt_identity()).first()


def _profile(t):
    d = t.to_card_dict()
    d.update(bio=t.bio, approach=t.approach, gender=t.gender, is_accepting_clients=t.is_accepting_clients,
             verification_status=t.verification_status,
             credentials=[{"type": c.credential_type, "details": c.details, "status": c.verification_status} for c in t.credentials])
    return d


@portal_bp.route("/me", methods=["GET"])
@role_required("therapist")
def me():
    t = _me()
    return jsonify({"therapist": _profile(t)})


@portal_bp.route("/me", methods=["PUT"])
@role_required("therapist")
def update_me():
    t, data = _me(), request.get_json(silent=True) or {}
    for field, limit in (("display_name", 120), ("qualification", 255), ("bio", 2000), ("approach", 2000)):
        if field in data:
            val = (data[field] or "").strip()[:limit]
            if field in ("display_name", "qualification") and not val:
                return jsonify({"error": "validation_error", "message": f"{field.replace('_', ' ').capitalize()} can't be empty."}), 422
            setattr(t, field, val)
    if "display_name" in data:
        t.user.profile.display_name = t.display_name
    if "session_price" in data:
        try:
            price = int(data["session_price"]); assert 100 <= price <= 20000
            t.session_price = price
        except (TypeError, ValueError, AssertionError):
            return jsonify({"error": "validation_error", "message": "Price must be between 100 and 20000."}), 422
    if "years_experience" in data:
        try:
            t.years_experience = max(0, min(60, int(data["years_experience"])))
        except (TypeError, ValueError):
            pass
    if data.get("gender") in ("female", "male", "non_binary"):
        t.gender = data["gender"]
    if "is_accepting_clients" in data:
        t.is_accepting_clients = bool(data["is_accepting_clients"])
    if isinstance(data.get("session_modes"), list):
        modes = [m for m in data["session_modes"] if m in SESSION_MODES]
        if not modes:
            return jsonify({"error": "validation_error", "message": "Offer at least one session type."}), 422
        t.session_modes_json = modes
    if isinstance(data.get("specializations"), list):
        specs = [s for s in data["specializations"] if s in CONCERNS]
        if not specs:
            return jsonify({"error": "validation_error", "message": "Choose at least one specialization."}), 422
        TherapistSpecialization.query.filter_by(therapist_id=t.id).delete()
        db.session.add_all(TherapistSpecialization(therapist_id=t.id, name=s) for s in specs)
    if isinstance(data.get("languages"), list):
        langs = [l for l in data["languages"] if l in LANGUAGES]
        if not langs:
            return jsonify({"error": "validation_error", "message": "Choose at least one language."}), 422
        TherapistLanguage.query.filter_by(therapist_id=t.id).delete()
        db.session.add_all(TherapistLanguage(therapist_id=t.id, language=l) for l in langs)
    db.session.commit()
    db.session.refresh(t)
    return jsonify({"message": "Profile saved.", "therapist": _profile(t)})


@portal_bp.route("/availability", methods=["GET"])
@role_required("therapist")
def get_availability():
    rows = TherapistAvailability.query.filter_by(therapist_id=_me().id, is_blocked=False).order_by(
        TherapistAvailability.weekday, TherapistAvailability.start_time).all()
    return jsonify({"availability": [{"weekday": r.weekday, "start": r.start_time.strftime("%H:%M"), "end": r.end_time.strftime("%H:%M")} for r in rows],
                    "timezone": "Asia/Kolkata"})


@portal_bp.route("/availability", methods=["PUT"])
@role_required("therapist")
def set_availability():
    t, items = _me(), (request.get_json(silent=True) or {}).get("availability")
    if not isinstance(items, list) or len(items) > 60:
        return jsonify({"error": "validation_error", "message": "Send a list of availability windows."}), 422
    clean = []
    for it in items:
        try:
            wd = int(it["weekday"]); s = datetime.strptime(it["start"], "%H:%M").time(); e = datetime.strptime(it["end"], "%H:%M").time()
            assert 0 <= wd <= 6 and s < e
        except (KeyError, ValueError, TypeError, AssertionError):
            return jsonify({"error": "validation_error", "message": "Each window needs a weekday and a start time earlier than its end time."}), 422
        clean.append((wd, s, e))
    TherapistAvailability.query.filter_by(therapist_id=t.id).delete()
    db.session.add_all(TherapistAvailability(therapist_id=t.id, weekday=wd, start_time=s, end_time=e) for wd, s, e in clean)
    db.session.commit()
    return jsonify({"message": "Availability saved."})


def _appt_view(a):
    client = db.session.get(User, a.user_id)
    can_join, reason = join_state(a)
    from app.models.therapy_session import TherapySession
    s = TherapySession.query.filter_by(appointment_id=a.id).first()
    d = a.to_dict()
    d.update(client_name=client.profile.display_name, can_join=can_join, join_hint=reason, session_id=s.id if s else None)
    return d


@portal_bp.route("/appointments", methods=["GET"])
@role_required("therapist")
def appointments():
    t = _me()
    q = Appointment.query.filter(Appointment.therapist_id == t.id, Appointment.status != "pending")
    status = request.args.get("status")
    if status:
        q = q.filter(Appointment.status == status)
    rows = q.order_by(Appointment.scheduled_start.asc()).all()
    return jsonify({"appointments": [_appt_view(a) for a in rows]})


@portal_bp.route("/appointments/<appt_id>/respond", methods=["POST"])
@role_required("therapist")
def respond(appt_id):
    t = _me()
    a = db.session.get(Appointment, appt_id)
    if not a or a.therapist_id != t.id:
        return jsonify({"error": "not_found", "message": "Appointment not found."}), 404
    action = (request.get_json(silent=True) or {}).get("action")
    pay = db.session.get(Payment, a.payment_id) if a.payment_id else None

    if action == "accept" and a.status == "requested":
        a.status = "confirmed"
        ensure_session(a)
        notify(a.user_id, "appointment_confirmed", "Appointment confirmed", "Your SafeVoice appointment has been confirmed.")
    elif action == "decline" and a.status in ("requested", "confirmed"):
        a.status, a.cancel_reason = "declined", "Declined by therapist"
        if pay and pay.status == "paid":
            pay.status = "refund_pending"
        notify(a.user_id, "appointment_declined", "Appointment update", "Your therapist couldn't take this slot. A full refund has been queued.")
    elif action == "no_show" and a.status == "confirmed" and a.scheduled_end < utcnow():
        a.status = "no_show"
    elif action == "complete" and a.status == "confirmed":
        a.status = "completed"
    else:
        return jsonify({"error": "conflict", "message": "That action isn't available for this appointment right now."}), 409
    db.session.commit()
    return jsonify({"message": "Updated.", "appointment": _appt_view(a)})


@portal_bp.route("/appointments/<appt_id>/pre-session", methods=["GET"])
@role_required("therapist")
def pre_session(appt_id):
    """Returns the client's AI check-in summary ONLY if they opted in for this appointment."""
    a = db.session.get(Appointment, appt_id)
    if not a or a.therapist_id != _me().id:
        return jsonify({"error": "not_found", "message": "Appointment not found."}), 404
    if not a.share_ai_summary_with_therapist:
        return jsonify({"shared": False, "message": "The client hasn't chosen to share a pre-session summary."})
    emo = EmotionResult.query.filter_by(user_id=a.user_id).order_by(EmotionResult.created_at.desc()).first()
    risk = RiskAssessment.query.filter_by(user_id=a.user_id).order_by(RiskAssessment.created_at.desc()).first()
    if not emo:
        return jsonify({"shared": True, "summary": None, "message": "No check-in has been completed yet."})
    return jsonify({"shared": True, "summary": {
        "primary_emotion": emo.primary_emotion,
        "concern_level": risk.tier if risk else None,
        "note": "Automated support indicator — not a diagnosis. You are responsible for clinical assessment.",
    }})


@portal_bp.route("/earnings", methods=["GET"])
@role_required("therapist")
def earnings():
    t = _me()
    paid = Appointment.query.filter(Appointment.therapist_id == t.id, Appointment.status == "completed").all()
    by_month = {}
    for a in paid:
        key = a.scheduled_start.strftime("%Y-%m")
        by_month[key] = by_month.get(key, 0) + a.price
    pending = Appointment.query.filter(Appointment.therapist_id == t.id, Appointment.status.in_(("requested", "confirmed"))).all()
    return jsonify({
        "total_earned": sum(a.price for a in paid), "completed_sessions": len(paid),
        "upcoming_value": sum(a.price for a in pending),
        "by_month": [{"month": k, "amount": v} for k, v in sorted(by_month.items())],
        "note": "Amounts are gross session fees before any platform fee or payout processing.",
    })


@portal_bp.route("/overview", methods=["GET"])
@role_required("therapist")
def overview():
    t = _me()
    now = utcnow()
    local_today = utc_to_local(now).date()
    all_appts = Appointment.query.filter(Appointment.therapist_id == t.id, Appointment.status != "pending").all()
    today = [a for a in all_appts if utc_to_local(a.scheduled_start).date() == local_today and a.status in ("confirmed", "requested")]
    return jsonify({
        "profile": _profile(t),
        "today": [_appt_view(a) for a in sorted(today, key=lambda x: x.scheduled_start)],
        "counts": {
            "requests": sum(1 for a in all_appts if a.status == "requested"),
            "upcoming": sum(1 for a in all_appts if a.status == "confirmed" and a.scheduled_end > now),
            "completed": sum(1 for a in all_appts if a.status == "completed"),
        },
        "rating": {"avg": t.rating_avg, "count": t.rating_count},
    })
