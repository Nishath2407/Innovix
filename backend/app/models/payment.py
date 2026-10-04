from app.extensions import db
from app.models.base import BaseModel


class Payment(BaseModel):
    __tablename__ = "payments"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    appointment_id = db.Column(db.String(36), nullable=True, index=True)  # plain reference; avoids a circular FK with appointments.payment_id

    razorpay_order_id = db.Column(db.String(120), nullable=True)
    razorpay_payment_id = db.Column(db.String(120), nullable=True)
    razorpay_signature = db.Column(db.String(255), nullable=True)

    amount = db.Column(db.Integer, nullable=False)  # smallest currency unit (paise)
    currency = db.Column(db.String(10), default="INR")
    mode = db.Column(db.String(10), default="razorpay")  # razorpay | test
    status = db.Column(db.String(20), default="created")  # created | paid | failed | refund_pending | refunded

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "mode": self.mode,
            "created_at": self.created_at.isoformat() + "Z",
        }
