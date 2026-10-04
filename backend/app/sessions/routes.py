import secrets
from datetime import timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.therapy_session import TherapySession
from app.models.appointment import Appointment
from app.models.therapist import Therapist
from app.models.user import User
from app.sessions.service import participant_role, join_state, ensure_session
from app.utils.timeutils import utcnow
from app.utils.notify import notify

sessions_bp = Blueprint("sessions", __name__)


def _load(session_id, uid):
    s = db.session.get(TherapySession, session_id)
    if not s:
        return None, None, (jsonify({"error": "not_found", "message": "Session not found."}), 404)
    role = participant_role(s, uid)
    if not role:
        return None, None, (jsonify({"error": "forbidden", "message": "You don't have access to this session."}), 403)
    return s, role, None


def _view(s, role):
    appt = db.session.get(Appointment, s.appointment_id)
    t = db.session.get(Therapist, s.therapist_id)
    client = db.session.get(User, s.user_id)
    can_join, reason = join_state(appt)
    return {
        "id": s.id, "status": s.status, "role": role, "mode": appt.session_mode,
        "scheduled_start": appt.scheduled_start.isoformat() + "Z", "scheduled_end": appt.scheduled_end.isoformat() + "Z",
        "started_at": s.started_at.isoformat() + "Z" if s.started_at else None,
        "counterpart_name": t.display_name if role == "user" else client.profile.display_name,
        "can_join": can_join, "join_hint": reason, "appointment_status": appt.status,
        "notes": s.therapist_notes if role == "therapist" else None,
    }


@sessions_bp.route("/by-appointment/<appt_id>", methods=["GET"])
@jwt_required()
def by_appointment(appt_id):
    uid = get_jwt_identity()
    appt = db.session.get(Appointment, appt_id)
    if not appt:
        return jsonify({"error": "not_found", "message": "Appointment not found."}), 404
    t = db.session.get(Therapist, appt.therapist_id)
    if uid not in (appt.user_id, t.user_id):
        return jsonify({"error": "forbidden", "message": "You don't have access to this session."}), 403
    if appt.status not in ("confirmed", "completed"):
        return jsonify({"error": "conflict", "message": "This appointment hasn't been confirmed yet."}), 409
    s = ensure_session(appt)
    db.session.commit()
    return jsonify({"session": _view(s, participant_role(s, uid))})


@sessions_bp.route("/<session_id>", methods=["GET"])
@jwt_required()
def get_session(session_id):
    s, role, err = _load(session_id, get_jwt_identity())
    if err:
        return err
    return jsonify({"session": _view(s, role)})


@sessions_bp.route("/<session_id>/start", methods=["POST"])
@jwt_required()
def start_session(session_id):
    s, role, err = _load(session_id, get_jwt_identity())
    if err:
        return err
    appt = db.session.get(Appointment, s.appointment_id)
    if s.status == "ended":
        return jsonify({"error": "conflict", "message": "This session has already ended."}), 409
    can_join, reason = join_state(appt)
    if not can_join:
        return jsonify({"error": "too_early", "message": reason}), 409
    if s.status != "live":
        s.status, s.started_at, s.webrtc_room_token = "live", utcnow(), secrets.token_urlsafe(24)
        db.session.commit()
    return jsonify({"session": _view(s, role)})


@sessions_bp.route("/<session_id>/end", methods=["POST"])
@jwt_required()
def end_session(session_id):
    s, role, err = _load(session_id, get_jwt_identity())
    if err:
        return err
    if s.status != "ended":
        s.status, s.ended_at, s.webrtc_room_token = "ended", utcnow(), None
        appt = db.session.get(Appointment, s.appointment_id)
        if appt.status == "confirmed":
            appt.status = "completed"
        other = db.session.get(Therapist, s.therapist_id).user_id if role == "user" else s.user_id
        notify(other, "session_ended", "Session ended", "Your SafeVoice session has ended.")
        db.session.commit()
    return jsonify({"message": "Session ended.", "session": _view(s, role)})


@sessions_bp.route("/<session_id>/notes", methods=["PUT"])
@jwt_required()
def save_notes(session_id):
    s, role, err = _load(session_id, get_jwt_identity())
    if err:
        return err
    if role != "therapist":
        return jsonify({"error": "forbidden", "message": "Only the therapist can write session notes."}), 403
    s.therapist_notes = ((request.get_json(silent=True) or {}).get("notes") or "")[:10000]
    db.session.commit()
    return jsonify({"message": "Notes saved."})
