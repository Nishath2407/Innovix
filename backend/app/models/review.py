from app.extensions import db
from app.models.base import BaseModel


class Review(BaseModel):
    __tablename__ = "reviews"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    therapist_id = db.Column(db.String(36), db.ForeignKey("therapists.id"), nullable=False)
    appointment_id = db.Column(db.String(36), db.ForeignKey("appointments.id"), nullable=False, unique=True)

    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, default="")
    is_flagged = db.Column(db.Boolean, default=False)  # for admin review queue
