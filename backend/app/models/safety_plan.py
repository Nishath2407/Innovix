from app.extensions import db
from app.models.base import BaseModel


class SafetyPlan(BaseModel):
    __tablename__ = "safety_plans"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)
    safe_locations = db.Column(db.JSON, default=list)
    personal_reminders = db.Column(db.Text, default="")

    trusted_contacts = db.relationship("TrustedContact", backref="safety_plan", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "safe_locations": self.safe_locations,
            "personal_reminders": self.personal_reminders,
            "trusted_contacts": [c.to_dict() for c in self.trusted_contacts],
        }


class TrustedContact(BaseModel):
    __tablename__ = "trusted_contacts"

    safety_plan_id = db.Column(db.String(36), db.ForeignKey("safety_plans.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    relationship = db.Column(db.String(60), nullable=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "phone": self.phone, "relationship": self.relationship}
