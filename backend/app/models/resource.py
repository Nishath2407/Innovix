from app.extensions import db
from app.models.base import BaseModel


class Resource(BaseModel):
    __tablename__ = "resources"

    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(60), nullable=False)  # anxiety | stress | womens_safety | ...
    body = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(500), nullable=True)  # link to verified official resource
    is_published = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "category": self.category,
            "body": self.body, "source_url": self.source_url,
        }
