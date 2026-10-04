import os
import click
from flask import Flask, jsonify, request
from flask_jwt_extended import decode_token, unset_jwt_cookies
from werkzeug.exceptions import HTTPException
from app.config import config_by_name
from app.extensions import db, migrate, cors, jwt, bcrypt, limiter, socketio


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    if config_name == "production" and app.config["SECRET_KEY"].startswith("dev-"):
        raise RuntimeError("Set SECRET_KEY and JWT_SECRET_KEY before running in production.")

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, supports_credentials=True, origins=app.config["CORS_ORIGINS"])
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config["CORS_ORIGINS"])

    from app.models import (  # noqa: F401  (imported so migrations/create_all see every table)
        user, therapist, appointment, therapy_session, message, payment, risk_assessment,
        emotion_result, journal_entry, safety_plan, resource, review, notification, audit_log, recovery,
    )

    from app.auth.routes import auth_bp
    from app.users.routes import users_bp
    from app.therapists.routes import therapists_bp, matching_bp
    from app.therapists.portal import portal_bp
    from app.appointments.routes import appointments_bp
    from app.sessions.routes import sessions_bp
    from app.chat.routes import chat_bp
    from app.ai.routes import ai_bp
    from app.payments.routes import payments_bp
    from app.journal.routes import journal_bp
    from app.safety.routes import safety_bp
    from app.resources.routes import resources_bp
    from app.notifications.routes import notifications_bp
    from app.wellness.routes import wellness_bp
    from app.admin.routes import admin_bp
    from app.sessions import realtime  # noqa: F401  (registers Socket.IO handlers)

    for bp, prefix in [
        (auth_bp, "/api/auth"), (users_bp, "/api/users"), (therapists_bp, "/api/therapists"),
        (matching_bp, "/api/matching"), (portal_bp, "/api/therapist"), (appointments_bp, "/api/appointments"),
        (sessions_bp, "/api/sessions"), (chat_bp, "/api/messages"), (ai_bp, "/api"),
        (payments_bp, "/api/payments"), (journal_bp, "/api/journal"), (safety_bp, "/api"),
        (resources_bp, "/api/resources"), (notifications_bp, "/api/notifications"),
        (wellness_bp, "/api"), (admin_bp, "/api/admin"),
    ]:
        app.register_blueprint(bp, url_prefix=prefix)

    @app.before_request
    def block_suspended_accounts():
        """A suspended account's existing login cookie stops working immediately."""
        token = request.cookies.get("access_token_cookie")
        if not token or not request.path.startswith("/api/"):
            return None
        try:
            uid = decode_token(token)["sub"]
        except Exception:
            return None
        from app.models.user import User
        u = db.session.get(User, uid)
        if u is not None and not u.is_active:
            resp = jsonify({"error": "forbidden", "message": "This account has been suspended."})
            resp.status_code = 401
            unset_jwt_cookies(resp)
            return resp

    @app.after_request
    def secure_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # ---- consistent JSON errors, never a stack trace ----
    messages = {
        400: "The request could not be understood.", 401: "Please log in to continue.",
        403: "You don't have access to this resource.", 404: "We couldn't find what you were looking for.",
        405: "That action isn't supported here.", 409: "This conflicts with existing data.",
        422: "Some of the information you entered isn't valid.", 429: "Too many requests. Please slow down and try again shortly.",
    }

    @app.errorhandler(HTTPException)
    def http_error(e):
        return jsonify({"error": e.name.lower().replace(" ", "_"), "message": messages.get(e.code, e.description)}), e.code

    @app.errorhandler(Exception)
    def unexpected(e):
        db.session.rollback()
        app.logger.exception("Unhandled error on %s", request.path)  # traceback goes to server logs only
        return jsonify({"error": "server_error", "message": "Something went wrong on our end. Please try again."}), 500

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "unauthorized", "message": "Please log in to continue."}), 401

    @jwt.invalid_token_loader
    def bad_token(reason):
        return jsonify({"error": "unauthorized", "message": "Your session is invalid. Please log in again."}), 401

    @jwt.expired_token_loader
    def expired(header, payload):
        return jsonify({"error": "session_expired", "message": "Your session expired. Please log in again."}), 401

    # ---- CLI ----
    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_admin(email, password):
        """flask --app run.py create-admin"""
        from app.models.user import User, UserProfile
        if User.query.filter_by(email=email.lower()).first():
            raise click.ClickException("A user with that email already exists. Use reset-password instead.")
        u = User(email=email.lower(), role="admin", is_email_verified=True)
        u.set_password(password)
        db.session.add(u)
        db.session.flush()
        db.session.add(UserProfile(user_id=u.id, display_name="SafeVoice Admin"))
        db.session.commit()
        click.echo("Admin created.")

    @app.cli.command("reset-password")
    @click.option("--email", prompt=True)
    @click.password_option()
    def reset_password_cli(email, password):
        """Sets a known password for any existing account — the fix when you've
        lost/mistyped a seeded or generated password.
        Usage: flask --app run.py reset-password --email admin@safevoice.app
        """
        from app.models.user import User
        u = User.query.filter_by(email=email.lower()).first()
        if not u:
            raise click.ClickException(f"No account found for {email}.")
        u.set_password(password)
        u.is_active = True
        db.session.commit()
        click.echo(f"Password updated for {email} (role: {u.role}).")

    return app
