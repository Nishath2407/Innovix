import secrets
from datetime import datetime
from app.extensions import db, bcrypt
from app.models.base import BaseModel


class User(BaseModel):
    """The authentication identity. Email lives ONLY here — it must never be
    joined into therapist-facing queries. Therapists interact with the
    `display_name` on UserProfile instead."""

    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # user | therapist | admin

    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verify_token = db.Column(db.String(64), nullable=True)
    password_reset_token = db.Column(db.String(64), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    profile = db.relationship("UserProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    therapist = db.relationship("Therapist", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def generate_email_verify_token(self):
        self.email_verify_token = secrets.token_urlsafe(32)
        return self.email_verify_token

    def generate_password_reset_token(self, expires_minutes=30):
        from datetime import timedelta
        from app.utils.timeutils import utcnow
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = utcnow() + timedelta(minutes=expires_minutes)
        return self.password_reset_token

    def to_public_dict(self):
        """Never include email/password here for therapist-facing contexts."""
        return {
            "id": self.id,
            "role": self.role,
            "display_name": self.profile.display_name if self.profile else None,
        }

    def to_self_dict(self):
        """Full-ish dict for the user's own account view."""
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_email_verified": self.is_email_verified,
            "display_name": self.profile.display_name if self.profile else None,
            "privacy_mode_enabled": self.profile.privacy_mode_enabled if self.profile else True,
            "preferred_language": self.profile.preferred_language if self.profile else "en",
            "therapist_status": self.therapist.verification_status if self.therapist else None,
        }


class UserProfile(BaseModel):
    """Everything therapist-facing and display-related lives here, separate
    from the auth identity in User."""

    __tablename__ = "user_profiles"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)

    display_name = db.Column(db.String(64), nullable=False)  # e.g. "Anonymous User #A72F"
    privacy_mode_enabled = db.Column(db.Boolean, default=True, nullable=False)

    preferred_language = db.Column(db.String(10), default="en")
    concerns = db.Column(db.JSON, default=list)  # e.g. ["anxiety", "workplace_burnout"]
    timezone = db.Column(db.String(64), default="Asia/Kolkata")

    def to_dict(self):
        return {
            "display_name": self.display_name,
            "privacy_mode_enabled": self.privacy_mode_enabled,
            "preferred_language": self.preferred_language,
            "concerns": self.concerns,
        }
