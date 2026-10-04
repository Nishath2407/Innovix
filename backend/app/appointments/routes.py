from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.appointment import Appointment
from app.models.therapist import Therapist
from app.models.therapy_session import TherapySession
from app.models.payment import Payment
from app.models.review import Review
from app.appointments.service import create_appointment, is_bookable, release_stale_pending
from app.sessions.service import join_state
from app.utils.timeutils import parse_iso_utc, utcnow
from app.utils.notify import notify
from app.utils.audit import log_action

appointments_bp = Blueprint("appointments", __name__)

ERRORS = {
    "slot_unavailable": (409, "That time is no longer available. Please pick another slot."),
    "slot_taken": (409, "That slot was just booked by someone else. Please pick another."),
    "mode_unavailable": (422, "This therapist doesn't offer that session type."),
}
REFUND_WINDOW_HOURS = 4


def serialize(appt):
    t = db.session.get(Therapist, appt.therapist_id)
    data = appt.to_dict(t)
    session = TherapySession.query.filter_by(appointment_id=appt.id).first()
    can_join, reason = join_state(appt)
    data.update(session_id=session.id if session else None, can_join=can_join, join_hint=reason)
    pay = db.session.get(Payment, appt.payment_id) if appt.payment_id else None
    data["payment_status"] = pay.status if pay else None
    data["reviewed"] = Review.query.filter_by(appointment_id=appt.id).first() is not None
    return data


def _mine(appt_id, user_id):
    appt = db.session.get(Appointment, appt_id)
    return appt if appt and appt.user_id == user_id else None


@appointments_bp.route("", methods=["GET"])
@jwt_required()
def list_appointments():
    release_stale_pending()
    uid = get_jwt_identity()
    appts = Appointment.query.filter_by(user_id=uid).order_by(Appointment.scheduled_start.desc()).all()
    return jsonify({"appointments": [serialize(a) for a in appts]})


@appointments_bp.route("", methods=["POST"])
@jwt_required()
def book():
    uid = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    therapist = db.session.get(Therapist, data.get("therapist_id") or "")
    if not therapist or not therapist.is_verified or not therapist.is_accepting_clients:
        return jsonify({"error": "not_found", "message": "Therapist not found."}), 404
    try:
        start = parse_iso_utc(data.get("scheduled_start"))
    except (TypeError, ValueError):
        return jsonify({"error": "validation_error", "message": "Choose a valid time slot."}), 422

    appt, err = create_appointment(uid, therapist, start, data.get("session_mode"))
    if err:
        code, msg = ERRORS[err]
        return jsonify({"error": err, "message": msg}), code
    appt.share_ai_summary_with_therapist = bool(data.get("share_ai_summary", False))
    db.session.commit()
    return jsonify({"message": "Slot held for 15 minutes. Complete payment to send your request.", "appointment": serialize(appt)}), 201


@appointments_bp.route("/<appt_id>", methods=["GET"])
@jwt_required()
def get_one(appt_id):
    appt = _mine(appt_id, get_jwt_identity())
    if not appt:
        return jsonify({"error": "not_found", "message": "Appointment not found."}), 404
    return jsonify({"appointment": serialize(appt)})


def _cancel(appt, uid, reason="Cancelled by client"):
    if appt.status not in ("pending", "requested", "confirmed"):
        return jsonify({"error": "conflict", "message": "This appointment can't be cancelled."}), 409
    hours_left = (appt.scheduled_start - utcnow()).total_seconds() / 3600
    pay = db.session.get(Payment, appt.payment_id) if appt.payment_id else None
    note = "Appointment cancelled."
    if pay and pay.status == "paid":
        if appt.status == "requested" or hours_left >= REFUND_WINDOW_HOURS:
            pay.status = "refund_pending"
            note = "Appointment cancelled. Your refund has been queued."
        else:
            note = f"Appointment cancelled. Cancellations within {REFUND_WINDOW_HOURS} hours of the start aren't refundable."
    appt.status = "cancelled"
    appt.cancel_reason = reason
    t = db.session.get(Therapist, appt.therapist_id)
    notify(t.user_id, "appointment_cancelled", "An appointment was cancelled", "A client cancelled an upcoming SafeVoice appointment.")
    log_action(uid, "appointment_cancelled", "appointment", appt.id)
    db.session.commit()
    return jsonify({"message": note, "appointment": serialize(appt)})


@appointments_bp.route("/<appt_id>", methods=["PUT"])
@jwt_required()
def update(appt_id):
    uid = get_jwt_identity()
    appt = _mine(appt_id, uid)
    if not appt:
        return jsonify({"error": "not_found", "message": "Appointment not found."}), 404
    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if action == "cancel":
        return _cancel(appt, uid)

    if action == "share_summary":
        appt.share_ai_summary_with_therapist = bool(data.get("share"))
        db.session.commit()
        return jsonify({"message": "Sharing preference saved.", "appointment": serialize(appt)})

    if action == "reschedule":
        if appt.status not in ("pending", "requested", "confirmed"):
            return jsonify({"error": "conflict", "message": "This appointment can't be rescheduled."}), 409
        if appt.status == "confirmed" and (appt.scheduled_start - utcnow()).total_seconds() < REFUND_WINDOW_HOURS * 3600:
            return jsonify({"error": "conflict", "message": f"Confirmed sessions can only be rescheduled {REFUND_WINDOW_HOURS}+ hours ahead."}), 409
        try:
            new_start = parse_iso_utc(data.get("scheduled_start"))
        except (TypeError, ValueError):
            return jsonify({"error": "validation_error", "message": "Choose a valid time slot."}), 422
        t = db.session.get(Therapist, appt.therapist_id)
        if not is_bookable(t, new_start):
            return jsonify({"error": "slot_unavailable", "message": ERRORS["slot_unavailable"][1]}), 409
        appt.scheduled_start = new_start
        appt.scheduled_end = new_start + timedelta(minutes=50)
        notify(t.user_id, "appointment_rescheduled", "An appointment was rescheduled", "A client moved an upcoming SafeVoice appointment.")
        db.session.commit()
        return jsonify({"message": "Appointment rescheduled.", "appointment": serialize(appt)})

    return jsonify({"error": "bad_request", "message": "Unsupported action."}), 400


@appointments_bp.route("/<appt_id>", methods=["DELETE"])
@jwt_required()
def delete(appt_id):
    uid = get_jwt_identity()
    appt = _mine(appt_id, uid)
    if not appt:
        return jsonify({"error": "not_found", "message": "Appointment not found."}), 404
    return _cancel(appt, uid)


@appointments_bp.route("/<appt_id>/review", methods=["POST"])
@jwt_required()
def review(appt_id):
    uid = get_jwt_identity()
    appt = _mine(appt_id, uid)
    if not appt:
        return jsonify({"error": "not_found", "message": "Appointment not found."}), 404
    if appt.status != "completed":
        return jsonify({"error": "conflict", "message": "You can review a session after it's completed."}), 409
    if Review.query.filter_by(appointment_id=appt.id).first():
        return jsonify({"error": "conflict", "message": "You've already reviewed this session."}), 409
    data = request.get_json(silent=True) or {}
    try:
        rating = int(data.get("rating"))
        assert 1 <= rating <= 5
    except (TypeError, ValueError, AssertionError):
        return jsonify({"error": "validation_error", "message": "Choose a rating from 1 to 5."}), 422
    db.session.add(Review(user_id=uid, therapist_id=appt.therapist_id, appointment_id=appt.id,
                          rating=rating, comment=(data.get("comment") or "").strip()[:1000]))
    db.session.flush()
    t = db.session.get(Therapist, appt.therapist_id)
    rows = Review.query.filter_by(therapist_id=t.id).all()
    t.rating_count = len(rows)
    t.rating_avg = round(sum(r.rating for r in rows) / len(rows), 2)
    db.session.commit()
    return jsonify({"message": "Thanks for your feedback."}), 201
