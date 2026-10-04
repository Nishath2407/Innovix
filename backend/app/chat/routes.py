"""Session text chat over plain REST. The client polls `?after=<message_id>`,
which is simple, reliable behind any proxy, and needs no sticky connection."""
from flask import Blueprint, request, jsonify
from app.extensions import limiter
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.message import Message
from app.models.therapy_session import TherapySession
from app.sessions.service import participant_role

chat_bp = Blueprint("chat", __name__)


def _session_for(session_id, uid):
    s = db.session.get(TherapySession, session_id)
    if not s:
        return None, (jsonify({"error": "not_found", "message": "Session not found."}), 404)
    if not participant_role(s, uid):
        return None, (jsonify({"error": "forbidden", "message": "You don't have access to this session."}), 403)
    return s, None


@chat_bp.route("/<session_id>", methods=["GET"])
@limiter.exempt
@jwt_required()
def get_messages(session_id):
    uid = get_jwt_identity()
    s, err = _session_for(session_id, uid)
    if err:
        return err
    q = Message.query.filter_by(session_id=s.id).order_by(Message.created_at.asc(), Message.id.asc())
    after = request.args.get("after")
    msgs = q.all()
    if after:
        ids = [m.id for m in msgs]
        msgs = msgs[ids.index(after) + 1:] if after in ids else msgs
    # mark the other person's messages as read
    changed = False
    for m in msgs:
        if m.sender_user_id != uid and not m.is_read:
            m.is_read, changed = True, True
    if changed:
        db.session.commit()
    return jsonify({"messages": [dict(m.to_dict(), mine=(m.sender_user_id == uid)) for m in msgs], "session_status": s.status})


@chat_bp.route("/<session_id>", methods=["POST"])
@limiter.exempt
@jwt_required()
def send_message(session_id):
    uid = get_jwt_identity()
    s, err = _session_for(session_id, uid)
    if err:
        return err
    if s.status != "live":
        return jsonify({"error": "conflict", "message": "This session isn't active."}), 409
    body = ((request.get_json(silent=True) or {}).get("body") or "").strip()
    if not body:
        return jsonify({"error": "validation_error", "message": "Message can't be empty."}), 422
    m = Message(session_id=s.id, sender_user_id=uid, body=body[:4000])
    db.session.add(m)
    db.session.commit()
    return jsonify({"message": dict(m.to_dict(), mine=True)}), 201
