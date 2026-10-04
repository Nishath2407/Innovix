from app.extensions import db
from app.models.base import BaseModel


class RecoveryProgress(BaseModel):
    """One row per completed day of the 7-day starter journey."""

    __tablename__ = "recovery_progress"
    __table_args__ = (db.UniqueConstraint("user_id", "day", name="uq_user_recovery_day"),)

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    day = db.Column(db.Integer, nullable=False)  # 1..7
    note = db.Column(db.String(500), default="")
