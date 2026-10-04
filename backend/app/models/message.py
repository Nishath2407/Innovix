from app.extensions import db
from app.models.base import BaseModel


class Message(BaseModel):
    __tablename__ = "messages"

    session_id = db.Column(db.String(36), db.ForeignKey("therapy_sessions.id"), nullable=False, index=True)
    sender_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "sender_user_id": self.sender_user_id,
            "body": self.body,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }
