from app.extensions import db
from app.models.base import BaseModel


class JournalEntry(BaseModel):
    __tablename__ = "journal_entries"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), default="")
    body = db.Column(db.Text, nullable=False)
    mood_tag = db.Column(db.String(30), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "mood_tag": self.mood_tag,
            "created_at": self.created_at.isoformat(),
        }
