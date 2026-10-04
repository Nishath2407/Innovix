from app.extensions import db
from app.models.notification import Notification


def notify(user_id, type_, title, body):
    """Creates an in-app notification. Titles/bodies are deliberately generic —
    they never mention the reason someone is seeking support."""
    db.session.add(Notification(user_id=user_id, type=type_, title=title[:200], body=body[:300]))
