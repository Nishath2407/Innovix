"""Admin oversight. Admins see accounts, bookings, payments and aggregate
platform health — never therapy messages, journals, safety plans or check-in text."""
from datetime import timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func, or_
from app.extensions import db
from app.constants import CONCERNS
from app.models.user import User
from app.models.therapist import Therapist
from app.models.appointment import Appointment
from app.models.therapy_session import TherapySession
from app.models.payment import Payment
from app.models.audit_log import AuditLog
from app.models.resource import Resource
from app.models.review import Review
from app.models.risk_assessment import RiskAssessment
from app.utils.decorators import role_required
from app.utils.audit import log_action
from app.utils.notify import notify
from app.utils.timeutils import utcnow

admin_bp = Blueprint("admin", __name__)


def _page():
    page = max(request.args.get("page", 1, type=int), 1)
    per = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    return page, per


def _paginate(query, page, per, serializer):
    total = query.count()
    rows = query.offset((page - 1) * per).limit(per).all()
    return jsonify({"items": [serializer(r) for r in rows], "total": total, "page": page, "per_page": per})


@admin_bp.route("/analytics", methods=["GET"])
@role_required("admin")
def analytics():
    now = utcnow()
    days = [(now - timedelta(days=i)).date() for i in range(13, -1, -1)]
    since = now - timedelta(days=14)

    def series(rows, value=lambda r: 1):
        bucket = {d: 0 for d in days}
        for r in rows:
            d = r.created_at.date()
            if d in bucket:
                bucket[d] += value(r)
        return [{"date": d.isoformat(), "value": v} for d, v in bucket.items()]

    signups = User.query.filter(User.role != "admin", User.created_at >= since).all()
    booked = Appointment.query.filter(Appointment.created_at >= since).all()
    paid = Payment.query.filter(Payment.status.in_(("paid", "refund_pending", "refunded")), Payment.created_at >= since).all()

    modes = dict(db.session.query(Appointment.session_mode, func.count()).filter(
        Appointment.status.in_(("confirmed", "completed", "requested"))).group_by(Appointment.session_mode).all())
    top = db.session.query(Therapist.display_name, func.count(Appointment.id)).join(
        Appointment, Appointment.therapist_id == Therapist.id).filter(Appointment.status == "completed").group_by(
        Therapist.id).order_by(func.count(Appointment.id).desc()).limit(5).all()

    week = now - timedelta(days=7)
    return jsonify({
        "totals": {
            "users": User.query.filter_by(role="user").count(),
            "active_users": User.query.filter(User.role == "user", User.last_login_at >= week).count(),
            "therapists": Therapist.query.count(),
            "verified_therapists": Therapist.query.filter_by(is_verified=True).count(),
            "pending_verification": Therapist.query.filter_by(verification_status="pending").count(),
            "appointments": Appointment.query.count(),
            "completed_sessions": Appointment.query.filter_by(status="completed").count(),
            "live_sessions": TherapySession.query.filter_by(status="live").count(),
            "revenue": (db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "paid").scalar() or 0) // 100,
            "refunds_pending": Payment.query.filter_by(status="refund_pending").count(),
            "high_concern_checkins_7d": RiskAssessment.query.filter(RiskAssessment.tier == "high", RiskAssessment.created_at >= week).count(),
            "flagged_reviews": Review.query.filter_by(is_flagged=True).count(),
        },
        "series": {
            "signups": series(signups), "appointments": series(booked),
            "revenue": series(paid, lambda p: p.amount // 100),
        },
        "session_types": [{"mode": m, "count": c} for m, c in modes.items()],
        "top_therapists": [{"name": n, "sessions": c} for n, c in top],
    })


@admin_bp.route("/system", methods=["GET"])
@role_required("admin")
def system():
    cfg = current_app.config
    try:
        db.session.execute(db.text("SELECT 1")); db_ok = True
    except Exception:
        db_ok = False
    pay = "razorpay" if cfg["RAZORPAY_KEY_ID"] and cfg["RAZORPAY_KEY_SECRET"] else ("test" if cfg["PAYMENTS_TEST_MODE"] else "not configured")
    return jsonify({
        "api": "ok", "database": "ok" if db_ok else "down",
        "email": "smtp" if cfg["MAIL_SERVER"] else "console (dev)",
        "payments": pay, "environment": "production" if not cfg["DEBUG"] and not cfg["TESTING"] else "development",
        "time_utc": utcnow().isoformat() + "Z",
    })


def _user_row(u):
    return {"id": u.id, "role": u.role, "email": u.email, "display_name": u.profile.display_name if u.profile else None,
            "is_active": u.is_active, "is_email_verified": u.is_email_verified,
            "created_at": u.created_at.isoformat() + "Z", "last_login_at": u.last_login_at.isoformat() + "Z" if u.last_login_at else None}


@admin_bp.route("/users", methods=["GET"])
@role_required("admin")
def users():
    page, per = _page()
    q = User.query
    role = request.args.get("role")
    if role in ("user", "therapist", "admin"):
        q = q.filter(User.role == role)
    term = (request.args.get("q") or "").strip()
    if term:
        q = q.filter(or_(User.email.ilike(f"%{term}%"), User.id == term))
    return _paginate(q.order_by(User.created_at.desc()), page, per, _user_row)


def _set_active(user_id, active):
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({"error": "not_found", "message": "User not found."}), 404
    if u.role == "admin":
        return jsonify({"error": "forbidden", "message": "Admin accounts can't be suspended here."}), 403
    u.is_active = active
    if u.therapist and not active:
        u.therapist.is_accepting_clients = False
    log_action(get_jwt_identity(), "user_reactivated" if active else "user_suspended", "user", u.id)
    db.session.commit()
    return jsonify({"message": "Account reactivated." if active else "Account suspended.", "user": _user_row(u)})


@admin_bp.route("/users/<user_id>/suspend", methods=["POST"])
@role_required("admin")
def suspend(user_id):
    return _set_active(user_id, False)


@admin_bp.route("/users/<user_id>/activate", methods=["POST"])
@role_required("admin")
def activate(user_id):
    return _set_active(user_id, True)


def _therapist_row(t):
    return {"id": t.id, "user_id": t.user_id, "display_name": t.display_name, "qualification": t.qualification,
            "years_experience": t.years_experience, "session_price": t.session_price, "is_verified": t.is_verified,
            "verification_status": t.verification_status, "email": t.user.email, "is_active": t.user.is_active,
            "specializations": [CONCERNS.get(s.name, s.name) for s in t.specializations],
            "languages": [l.language for l in t.languages],
            "credentials": [{"type": c.credential_type, "details": c.details, "status": c.verification_status} for c in t.credentials],
            "rating_avg": t.rating_avg, "rating_count": t.rating_count, "created_at": t.created_at.isoformat() + "Z"}


@admin_bp.route("/therapists", methods=["GET"])
@role_required("admin")
def therapists():
    page, per = _page()
    q = Therapist.query
    status = request.args.get("status")
    if status in ("pending", "approved", "rejected"):
        q = q.filter_by(verification_status=status)
    return _paginate(q.order_by(Therapist.created_at.desc()), page, per, _therapist_row)


@admin_bp.route("/therapists/<therapist_id>/verify", methods=["POST"])
@role_required("admin")
def verify_therapist(therapist_id):
    t = db.session.get(Therapist, therapist_id)
    if not t:
        return jsonify({"error": "not_found", "message": "Therapist not found."}), 404
    data = request.get_json(silent=True) or {}
    approve = bool(data.get("approve", True))
    t.is_verified = approve
    t.verification_status = "approved" if approve else "rejected"
    for c in t.credentials:
        c.verification_status = t.verification_status
        c.reviewed_by_admin_id = get_jwt_identity()
    log_action(get_jwt_identity(), "therapist_approved" if approve else "therapist_rejected", "therapist", t.id,
               note=(data.get("note") or "")[:200])
    notify(t.user_id, "verification", "Profile review complete",
           "Your profile is now live." if approve else "Your application needs attention. Please contact support.")
    db.session.commit()
    return jsonify({"message": "Therapist approved." if approve else "Therapist rejected.", "therapist": _therapist_row(t)})


@admin_bp.route("/appointments", methods=["GET"])
@role_required("admin")
def appointments():
    page, per = _page()
    q = Appointment.query
    if request.args.get("status"):
        q = q.filter_by(status=request.args["status"])

    def row(a):
        t = db.session.get(Therapist, a.therapist_id)
        client = db.session.get(User, a.user_id)
        return {"id": a.id, "client": client.profile.display_name, "therapist": t.display_name, "mode": a.session_mode,
                "status": a.status, "price": a.price, "scheduled_start": a.scheduled_start.isoformat() + "Z"}
    return _paginate(q.order_by(Appointment.scheduled_start.desc()), page, per, row)


@admin_bp.route("/payments", methods=["GET"])
@role_required("admin")
def payments():
    page, per = _page()
    q = Payment.query
    if request.args.get("status"):
        q = q.filter_by(status=request.args["status"])
    return _paginate(q.order_by(Payment.created_at.desc()), page, per,
                     lambda p: {**p.to_dict(), "amount_rupees": p.amount // 100, "appointment_id": p.appointment_id})


@admin_bp.route("/payments/<payment_id>/mark-refunded", methods=["POST"])
@role_required("admin")
def mark_refunded(payment_id):
    p = db.session.get(Payment, payment_id)
    if not p or p.status != "refund_pending":
        return jsonify({"error": "conflict", "message": "Only refunds marked as pending can be closed."}), 409
    p.status = "refunded"
    log_action(get_jwt_identity(), "refund_marked_done", "payment", p.id)
    db.session.commit()
    return jsonify({"message": "Refund marked as processed.", "payment": p.to_dict()})


@admin_bp.route("/audit-logs", methods=["GET"])
@role_required("admin")
def audit_logs():
    page, per = _page()
    def row(l):
        actor = db.session.get(User, l.actor_user_id) if l.actor_user_id else None
        return {"id": l.id, "action": l.action, "target_type": l.target_type, "target_id": l.target_id,
                "actor": actor.profile.display_name if actor and actor.profile else "system",
                "created_at": l.created_at.isoformat() + "Z", "ip": l.ip_address}
    return _paginate(AuditLog.query.order_by(AuditLog.created_at.desc()), page, per, row)


# ---- resources management ----
def _resource_row(r):
    return {**r.to_dict(), "is_published": r.is_published}


def _resource_fields(data):
    title, body = (data.get("title") or "").strip(), (data.get("body") or "").strip()
    category = data.get("category")
    valid = set(CONCERNS) | {"mental_health", "digital_safety", "domestic_violence", "emergency"}
    if not title or not body or category not in valid:
        return None
    return dict(title=title[:200], body=body, category=category, source_url=(data.get("source_url") or "").strip()[:500] or None,
                is_published=bool(data.get("is_published", True)))


@admin_bp.route("/resources", methods=["GET"])
@role_required("admin")
def list_resources():
    return jsonify({"items": [_resource_row(r) for r in Resource.query.order_by(Resource.created_at.desc()).all()]})


@admin_bp.route("/resources", methods=["POST"])
@role_required("admin")
def create_resource():
    fields = _resource_fields(request.get_json(silent=True) or {})
    if not fields:
        return jsonify({"error": "validation_error", "message": "Title, body and a valid category are required."}), 422
    r = Resource(**fields)
    db.session.add(r)
    db.session.flush()
    log_action(get_jwt_identity(), "resource_created", "resource", r.id)
    db.session.commit()
    return jsonify({"resource": _resource_row(r)}), 201


@admin_bp.route("/resources/<rid>", methods=["PUT"])
@role_required("admin")
def update_resource(rid):
    r = db.session.get(Resource, rid)
    fields = _resource_fields(request.get_json(silent=True) or {})
    if not r:
        return jsonify({"error": "not_found", "message": "Resource not found."}), 404
    if not fields:
        return jsonify({"error": "validation_error", "message": "Title, body and a valid category are required."}), 422
    for k, v in fields.items():
        setattr(r, k, v)
    log_action(get_jwt_identity(), "resource_updated", "resource", r.id)
    db.session.commit()
    return jsonify({"resource": _resource_row(r)})


@admin_bp.route("/resources/<rid>", methods=["DELETE"])
@role_required("admin")
def delete_resource(rid):
    r = db.session.get(Resource, rid)
    if not r:
        return jsonify({"error": "not_found", "message": "Resource not found."}), 404
    log_action(get_jwt_identity(), "resource_deleted", "resource", r.id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "Resource deleted."})


# ---- reviews / reports ----
@admin_bp.route("/reviews", methods=["GET"])
@role_required("admin")
def reviews():
    page, per = _page()
    q = Review.query
    if request.args.get("flagged") == "1":
        q = q.filter_by(is_flagged=True)
    def row(r):
        t = db.session.get(Therapist, r.therapist_id)
        return {"id": r.id, "therapist": t.display_name, "rating": r.rating, "comment": r.comment,
                "is_flagged": r.is_flagged, "created_at": r.created_at.isoformat() + "Z"}
    return _paginate(q.order_by(Review.created_at.desc()), page, per, row)


@admin_bp.route("/reviews/<rid>/flag", methods=["POST"])
@role_required("admin")
def flag_review(rid):
    r = db.session.get(Review, rid)
    if not r:
        return jsonify({"error": "not_found", "message": "Review not found."}), 404
    r.is_flagged = bool((request.get_json(silent=True) or {}).get("flag", True))
    log_action(get_jwt_identity(), "review_flagged" if r.is_flagged else "review_restored", "review", r.id)
    db.session.commit()
    return jsonify({"message": "Review hidden from public profile." if r.is_flagged else "Review restored.", "is_flagged": r.is_flagged})
