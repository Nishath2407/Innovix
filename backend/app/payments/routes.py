import hmac
import hashlib
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.payment import Payment
from app.models.appointment import Appointment
from app.models.therapist import Therapist
from app.utils.notify import notify
from app.utils.timeutils import utcnow

payments_bp = Blueprint("payments", __name__)


def _mode():
    cfg = current_app.config
    if cfg["RAZORPAY_KEY_ID"] and cfg["RAZORPAY_KEY_SECRET"] and not cfg["TESTING"]:
        return "razorpay"
    return "test" if cfg["PAYMENTS_TEST_MODE"] else None


def _mark_paid(payment, appt):
    payment.status = "paid"
    appt.status = "requested"          # paid; waiting for the therapist to accept
    appt.payment_id = payment.id
    t = db.session.get(Therapist, appt.therapist_id)
    notify(appt.user_id, "payment_confirmed", "Payment received", "Your SafeVoice payment was received. Your request has been sent.")
    notify(t.user_id, "appointment_requested", "New appointment request", "You have a new SafeVoice appointment request.")


def _pending_appt(appt_id, uid):
    appt = db.session.get(Appointment, appt_id or "")
    if not appt or appt.user_id != uid:
        return None, (jsonify({"error": "not_found", "message": "Appointment not found."}), 404)
    if appt.status != "pending":
        return None, (jsonify({"error": "conflict", "message": "This appointment isn't awaiting payment. Its hold may have expired."}), 409)
    return appt, None


@payments_bp.route("/config", methods=["GET"])
def config():
    return jsonify({"mode": _mode(), "key_id": current_app.config["RAZORPAY_KEY_ID"] or None})


@payments_bp.route("/create-order", methods=["POST"])
@jwt_required()
def create_order():
    uid = get_jwt_identity()
    appt, err = _pending_appt((request.get_json(silent=True) or {}).get("appointment_id"), uid)
    if err:
        return err
    mode = _mode()
    if mode is None:
        return jsonify({"error": "not_configured", "message": "Payments aren't configured on this server yet."}), 503

    amount = appt.price * 100  # paise
    payment = Payment.query.filter_by(appointment_id=appt.id, status="created").first() or \
        Payment(user_id=uid, appointment_id=appt.id, amount=amount, mode=mode, status="created")

    if mode == "razorpay":
        import razorpay
        client = razorpay.Client(auth=(current_app.config["RAZORPAY_KEY_ID"], current_app.config["RAZORPAY_KEY_SECRET"]))
        try:
            order = client.order.create({"amount": amount, "currency": "INR", "receipt": f"appt_{appt.id[:30]}", "payment_capture": 1})
        except Exception:
            return jsonify({"error": "gateway_error", "message": "Couldn't reach the payment gateway. Please try again."}), 502
        payment.razorpay_order_id = order["id"]
    else:
        payment.razorpay_order_id = f"test_order_{payment.id[:12] if payment.id else appt.id[:12]}"
    db.session.add(payment)
    db.session.commit()
    return jsonify({
        "mode": mode, "payment_id": payment.id, "order_id": payment.razorpay_order_id,
        "amount": amount, "currency": "INR", "key_id": current_app.config["RAZORPAY_KEY_ID"] or None,
    }), 201


@payments_bp.route("/verify", methods=["POST"])
@jwt_required()
def verify_payment():
    """Razorpay: recompute HMAC-SHA256(order_id|payment_id) with the server-only
    secret and compare in constant time. The client's word alone is never trusted."""
    uid = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    order_id, gw_payment_id, signature = (data.get("razorpay_order_id"), data.get("razorpay_payment_id"), data.get("razorpay_signature"))
    if not all([order_id, gw_payment_id, signature]):
        return jsonify({"error": "validation_error", "message": "Missing payment verification details."}), 422
    payment = Payment.query.filter_by(razorpay_order_id=order_id, user_id=uid).first()
    if not payment:
        return jsonify({"error": "not_found", "message": "Payment not found."}), 404
    if payment.status == "paid":
        return jsonify({"message": "Payment already verified.", "payment": payment.to_dict()})

    secret = current_app.config["RAZORPAY_KEY_SECRET"]
    expected = hmac.new(secret.encode(), f"{order_id}|{gw_payment_id}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, str(signature)):
        payment.status = "failed"
        db.session.commit()
        return jsonify({"error": "invalid_signature", "message": "We couldn't verify this payment. If you were charged, contact support."}), 400

    appt = db.session.get(Appointment, payment.appointment_id)
    payment.razorpay_payment_id, payment.razorpay_signature = gw_payment_id, signature
    if appt and appt.status == "pending":
        _mark_paid(payment, appt)
    db.session.commit()
    return jsonify({"message": "Payment verified.", "payment": payment.to_dict()})


@payments_bp.route("/test-confirm", methods=["POST"])
@jwt_required()
def test_confirm():
    """Sandbox-only confirmation for local development. Rejected whenever real
    payments are configured or the app runs in production."""
    if _mode() != "test":
        return jsonify({"error": "forbidden", "message": "Test payments are disabled."}), 403
    uid = get_jwt_identity()
    payment = Payment.query.filter_by(id=(request.get_json(silent=True) or {}).get("payment_id"), user_id=uid, mode="test").first()
    if not payment:
        return jsonify({"error": "not_found", "message": "Payment not found."}), 404
    appt = db.session.get(Appointment, payment.appointment_id)
    if not appt or appt.status != "pending":
        return jsonify({"error": "conflict", "message": "This appointment isn't awaiting payment. Its hold may have expired."}), 409
    _mark_paid(payment, appt)
    db.session.commit()
    return jsonify({"message": "Test payment confirmed.", "payment": payment.to_dict()})


@payments_bp.route("/mine", methods=["GET"])
@jwt_required()
def my_payments():
    rows = Payment.query.filter_by(user_id=get_jwt_identity()).order_by(Payment.created_at.desc()).all()
    return jsonify({"payments": [p.to_dict() for p in rows]})
