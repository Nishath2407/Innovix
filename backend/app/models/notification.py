from app.extensions import db
from app.models.base import BaseModel


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(40), nullable=False)  # appointment_confirmed | reminder | payment | ...
    title = db.Column(db.String(200), nullable=False)  # keep generic — never include sensitive topic details
    body = db.Column(db.String(300), nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id, "type": self.type, "title": self.title,
            "body": self.body, "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }
