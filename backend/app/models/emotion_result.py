from app.extensions import db
from app.models.base import BaseModel


class EmotionResult(BaseModel):
    __tablename__ = "emotion_results"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    input_text = db.Column(db.Text, nullable=False)  # treat as sensitive; never included in normal logs

    primary_emotion = db.Column(db.String(30), nullable=False)
    emotion_scores = db.Column(db.JSON, default=dict)  # {"anxiety": 0.82, "sadness": 0.11, ...}

    is_shared_with_therapist = db.Column(db.Boolean, default=False)  # private by default — user opts in to share
