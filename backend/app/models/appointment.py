from sqlalchemy import text
from app.extensions import db
from app.models.base import BaseModel

# A slot is "held" by any appointment in one of these states. Cancelled,
# declined or expired bookings release the slot so it can be booked again.
ACTIVE_STATUSES = ("pending", "requested", "confirmed")


class Appointment(BaseModel):
    __tablename__ = "appointments"
    __table_args__ = (
        db.Index(
            "uq_therapist_active_slot", "therapist_id", "scheduled_start", unique=True,
            sqlite_where=text("status IN ('pending','requested','confirmed')"),
            postgresql_where=text("status IN ('pending','requested','confirmed')"),
        ),
    )

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    therapist_id = db.Column(db.String(36), db.ForeignKey("therapists.id"), nullable=False, index=True)

    scheduled_start = db.Column(db.DateTime, nullable=False)  # naive UTC
    scheduled_end = db.Column(db.DateTime, nullable=False)
    session_mode = db.Column(db.String(10), nullable=False)  # video | audio | text

    # pending (unpaid) -> requested (paid, awaiting therapist) -> confirmed -> completed
    # side exits: declined, cancelled, no_show, expired
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)

    price = db.Column(db.Integer, nullable=False)
    payment_id = db.Column(db.String(36), db.ForeignKey("payments.id"), nullable=True)

    share_ai_summary_with_therapist = db.Column(db.Boolean, default=False)  # private unless the user opts in
    cancel_reason = db.Column(db.String(200), nullable=True)

    def to_dict(self, therapist=None):
        data = {
            "id": self.id,
            "therapist_id": self.therapist_id,
            "scheduled_start": self.scheduled_start.isoformat() + "Z",
            "scheduled_end": self.scheduled_end.isoformat() + "Z",
            "session_mode": self.session_mode,
            "status": self.status,
            "price": self.price,
            "share_ai_summary": self.share_ai_summary_with_therapist,
        }
        if therapist is not None:
            data["therapist_name"] = therapist.display_name
        return data
