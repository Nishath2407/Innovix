from app.extensions import db
from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Tracks security-relevant actions (admin actions, verification
    decisions, account suspensions). Never store therapy content here."""

    __tablename__ = "audit_logs"

    actor_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. "therapist_verified", "user_suspended"
    target_type = db.Column(db.String(50), nullable=True)  # "user" | "therapist" | "appointment" ...
    target_id = db.Column(db.String(36), nullable=True)
    metadata_json = db.Column(db.JSON, default=dict)
    ip_address = db.Column(db.String(64), nullable=True)
