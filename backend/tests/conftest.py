import hashlib
import hmac
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, UserProfile

PW = "StrongPass123"
ALL_DAYS = [{"weekday": d, "start": "09:00", "end": "21:00"} for d in range(7)]


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_client(app):
    return lambda: app.test_client()


class Helpers:
    @staticmethod
    def register(c, email="user@example.com", **extra):
        return c.post("/api/auth/register", json={"email": email, "password": PW, **extra})

    @staticmethod
    def login(c, email="user@example.com", portal="user", password=PW):
        return c.post("/api/auth/login", json={"email": email, "password": password, "portal": portal})

    @staticmethod
    def therapist_payload(email="doc@example.com", **over):
        base = dict(email=email, password=PW, role="therapist", display_name="Dr. Test", qualification="M.Phil Clinical Psychology",
                    years_experience=6, session_price=1200, specializations=["anxiety", "stress"],
                    languages=["en", "te"], session_modes=["video", "audio", "text"], gender="female",
                    registration_number="RCI-12345", issuing_body="RCI", bio="Helps with workplace stress.")
        base.update(over)
        return base

    @staticmethod
    def make_admin(app, c, email="admin@example.com"):
        with app.app_context():
            u = User(email=email, role="admin", is_email_verified=True)
            u.set_password(PW)
            db.session.add(u)
            db.session.flush()
            db.session.add(UserProfile(user_id=u.id, display_name="Admin"))
            db.session.commit()
        assert Helpers.login(c, email, "admin").status_code == 200

    @staticmethod
    def approved_therapist(app, make_client, email="doc@example.com", **over):
        """Registers a therapist, has an admin approve them, sets availability. Returns (client, therapist_id)."""
        t = make_client()
        assert t.post("/api/auth/register", json=Helpers.therapist_payload(email, **over)).status_code == 201
        assert Helpers.login(t, email, "therapist").status_code == 200
        tid = t.get("/api/therapist/me").get_json()["therapist"]["id"]
        admin = make_client()
        Helpers.make_admin(app, admin, f"admin-{email}")
        assert admin.post(f"/api/admin/therapists/{tid}/verify", json={"approve": True}).status_code == 200
        assert t.put("/api/therapist/availability", json={"availability": ALL_DAYS}).status_code == 200
        return t, tid

    @staticmethod
    def first_slot(c, tid, skip=0):
        days = c.get(f"/api/therapists/{tid}/slots?days=3").get_json()["days"]
        slots = [s for d in days for s in d["slots"]]
        return slots[skip]

    @staticmethod
    def sign(order_id, payment_id, secret):
        return hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()


@pytest.fixture
def h():
    return Helpers
