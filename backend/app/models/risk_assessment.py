from app.extensions import db
from app.models.base import BaseModel


class RiskAssessment(BaseModel):
    """Internal risk scoring. NEVER surface the raw numeric score to end
    users — always translate to a supportive tier + recommended next step."""

    __tablename__ = "risk_assessments"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    check_in_text_ref = db.Column(db.String(36), nullable=True)  # link to emotion_results.id if applicable

    score = db.Column(db.Integer, nullable=False)  # 0-100, internal only
    tier = db.Column(db.String(20), nullable=False)  # low | moderate | high
    signals = db.Column(db.JSON, default=list)  # e.g. ["repeated_distress", "fear"]

    def to_user_facing_dict(self):
        """What the frontend is allowed to receive — no raw score."""
        tier_copy = {
            "low": {"headline": "You seem to be doing okay", "next_step": "Continue self-reflection or explore resources."},
            "moderate": {"headline": "Some signs of distress detected", "next_step": "Consider speaking with a professional soon."},
            "high": {"headline": "High concern detected", "next_step": "Professional support and safety resources are recommended."},
        }
        return {
            "tier": self.tier,
            "signals": self.signals,
            **tier_copy.get(self.tier, tier_copy["low"]),
            "disclaimer": "This is an automated support indicator, not a medical diagnosis.",
        }
