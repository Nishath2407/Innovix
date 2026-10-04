from app.extensions import db
from app.models.base import BaseModel


class TherapySession(BaseModel):
    __tablename__ = "therapy_sessions"

    appointment_id = db.Column(db.String(36), db.ForeignKey("appointments.id"), nullable=False, unique=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    therapist_id = db.Column(db.String(36), db.ForeignKey("therapists.id"), nullable=False, index=True)

    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="scheduled")  # scheduled | live | ended | expired

    webrtc_room_token = db.Column(db.String(128), nullable=True)  # short-lived, issued at session start

    therapist_notes = db.Column(db.Text, nullable=True)  # visible to therapist + admin only
