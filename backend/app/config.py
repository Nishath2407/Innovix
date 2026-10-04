import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
_is_prod = os.environ.get("FLASK_ENV") == "production"


def _bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes")


class Config:
    """Base configuration. Everything sensitive comes from environment
    variables — see backend/.env.example."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, '..', 'safevoice_dev.db')}"
    ).replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth cookies ---
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)
    JWT_COOKIE_SECURE = _is_prod
    # Frontend and API live on different domains in production, so cookies
    # must be SameSite=None (+Secure). Locally, Lax is fine.
    JWT_COOKIE_SAMESITE = "None" if _is_prod else "Lax"
    JWT_COOKIE_CSRF_PROTECT = True

    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")]

    # --- Mail (if MAIL_SERVER is empty, links are printed to the backend console) ---
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@safevoice.app")
    REQUIRE_EMAIL_VERIFICATION = _bool("REQUIRE_EMAIL_VERIFICATION", False)

    # --- Payments ---
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    # "test" = clearly-labelled sandbox confirmation, no real charge.
    # Automatically disabled when real Razorpay keys are set or in production.
    PAYMENTS_TEST_MODE = _bool("PAYMENTS_TEST_MODE", not _is_prod)

    # --- Sessions ---
    SESSION_LENGTH_MINUTES = 1000
    SESSION_JOIN_EARLY_MINUTES = int(os.environ.get("SESSION_JOIN_EARLY_MINUTES", 10))
    # Development convenience: lets you open a session room right after
    # booking instead of waiting for the scheduled time. Never enable in prod.
    DEV_ALLOW_EARLY_JOIN = _bool("DEV_ALLOW_EARLY_JOIN", not _is_prod)
    PENDING_PAYMENT_HOLD_MINUTES = 15

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_ENABLED = True
    DEFAULT_TIMEZONE = "Asia/Kolkata"


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    BCRYPT_LOG_ROUNDS = 4  # fast hashing for tests only
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_COOKIE_CSRF_PROTECT = False
    RATELIMIT_ENABLED = False
    PAYMENTS_TEST_MODE = True
    DEV_ALLOW_EARLY_JOIN = True
    RAZORPAY_KEY_ID = ""
    RAZORPAY_KEY_SECRET = "test_secret_for_signature_tests"


class TestingCsrfConfig(TestingConfig):
    JWT_COOKIE_CSRF_PROTECT = True


class ProductionConfig(Config):
    DEBUG = False
    PAYMENTS_TEST_MODE = False
    DEV_ALLOW_EARLY_JOIN = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "testing_csrf": TestingCsrfConfig,
    "production": ProductionConfig,
}
RATELIMIT_ENABLED = False
