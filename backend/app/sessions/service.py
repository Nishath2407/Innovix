from datetime import timedelta
from flask import current_app
from app.extensions import db
from app.models.therapy_session import TherapySession
from app.models.therapist import Therapist
from app.utils.timeutils import utcnow


def ensure_session(appt):
    s = TherapySession.query.filter_by(appointment_id=appt.id).first()
    if not s:
        s = TherapySession(appointment_id=appt.id, user_id=appt.user_id, therapist_id=appt.therapist_id, status="scheduled")
        db.session.add(s)
        db.session.flush()
    return s


def participant_role(session, user_id):
    """'user' | 'therapist' | None. Note session.therapist_id is a Therapist row id,
    so it must be resolved to that therapist's user id before comparing."""
    if session.user_id == user_id:
        return "user"
    t = db.session.get(Therapist, session.therapist_id)
    if t and t.user_id == user_id:
        return "therapist"
    return None


def join_state(appt):
    """(can_join, reason)"""
    if appt.status != "confirmed":
        return False, "Session isn't confirmed yet."
    cfg = current_app.config
    now = utcnow()
    if now > appt.scheduled_end + timedelta(minutes=15):
        return False, "This session window has ended."
    if cfg["DEV_ALLOW_EARLY_JOIN"]:
        return True, ""
    if now < appt.scheduled_start - timedelta(minutes=cfg["SESSION_JOIN_EARLY_MINUTES"]):
        return False, f"You can join {cfg['SESSION_JOIN_EARLY_MINUTES']} minutes before the start time."
    return True, ""
