import uuid
from app.extensions import db
from app.utils.timeutils import utcnow


def gen_uuid():
    return str(uuid.uuid4())


class BaseModel(db.Model):
    """Abstract base: every table gets a UUID primary key (never a guessable
    incrementing int) plus created/updated timestamps."""

    __abstract__ = True

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
