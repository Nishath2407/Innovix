from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.notification import Notification

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    user_id = get_jwt_identity()
    notes = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify({"notifications": [n.to_dict() for n in notes]})


@notifications_bp.route("/<notification_id>/read", methods=["POST"])
@jwt_required()
def mark_read(notification_id):
    user_id = get_jwt_identity()
    note = db.session.get(Notification, notification_id)
    if not note or note.user_id != user_id:
        return jsonify({"error": "not_found"}), 404
    note.is_read = True
    db.session.commit()
    return jsonify({"message": "Marked as read."})


@notifications_bp.route("/read-all", methods=["POST"])
@jwt_required()
def read_all():
    Notification.query.filter_by(user_id=get_jwt_identity(), is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All caught up."})
