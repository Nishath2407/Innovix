from app.extensions import db
from app.models.base import BaseModel


class Therapist(BaseModel):
    __tablename__ = "therapists"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)

    display_name = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, default="")
    approach = db.Column(db.Text, default="")
    years_experience = db.Column(db.Integer, default=0)
    gender = db.Column(db.String(20), nullable=True)

    session_price = db.Column(db.Integer, nullable=False, default=0)  # stored in rupees
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_accepting_clients = db.Column(db.Boolean, default=True, nullable=False)
    session_modes_json = db.Column(db.JSON, default=lambda: ["video", "audio", "text"])
    verification_status = db.Column(db.String(20), default="pending", nullable=False)  # pending | approved | rejected

    rating_avg = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)

    credentials = db.relationship("TherapistCredential", backref="therapist", cascade="all, delete-orphan")
    specializations = db.relationship("TherapistSpecialization", backref="therapist", cascade="all, delete-orphan")
    languages = db.relationship("TherapistLanguage", backref="therapist", cascade="all, delete-orphan")
    availability_slots = db.relationship("TherapistAvailability", backref="therapist", cascade="all, delete-orphan")

    def to_card_dict(self):
        """Public-facing therapist card — safe to expose to any visitor."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "qualification": self.qualification,
            "is_verified": self.is_verified,
            "years_experience": self.years_experience,
            "session_price": self.session_price,
            "rating_avg": self.rating_avg,
            "rating_count": self.rating_count,
            "specializations": [s.name for s in self.specializations],
            "languages": [l.language for l in self.languages],
            "session_modes": self.session_modes(),
        }

    def session_modes(self):
        return self.session_modes_json or ["video", "audio", "text"]


class TherapistCredential(BaseModel):
    __tablename__ = "therapist_credentials"

    therapist_id = db.Column(db.String(36), db.ForeignKey("therapists.id"), nullable=False)
    credential_type = db.Column(db.String(120), nullable=False)  # e.g. "License", "Degree"
    file_path = db.Column(db.String(500), nullable=True)  # stored privately, never public
    details = db.Column(db.Text, default="")  # e.g. registration number, issuing body
    verification_status = db.Column(db.String(20), default="pending")  # pending | approved | rejected
    reviewed_by_admin_id = db.Column(db.String(36), nullable=True)


class TherapistSpecialization(BaseModel):
    __tablename__ = "therapist_specializations"

    therapist_id = db.Column(db.String(36), db.ForeignKey("therapists.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g. "anxiety", "workplace_burnout"


class TherapistLanguage(BaseModel):
    __tablename__ = "therapist_languages"

    therapist_id = db.Column(db.String(36), db.ForeignKey("therapists.id"), nullable=False)
    language = db.Column(db.String(50), nullable=False)  # e.g. "en", "hi", "te"


class TherapistAvailability(BaseModel):
    __tablename__ = "therapist_availability"

    therapist_id = db.Column(db.String(36), db.ForeignKey("therapists.id"), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0=Monday ... 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(64), default="Asia/Kolkata")
    is_blocked = db.Column(db.Boolean, default=False)  # for one-off blocked slots
