"""Socket.IO signalling for WebRTC audio/video. The server only relays
connection-setup messages between the two verified participants of a session;
media flows peer-to-peer and never touches this server."""
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token
from app.extensions import socketio, db
from app.models.therapy_session import TherapySession
from app.sessions.service import participant_role

_sid_user = {}      # socket id -> user id
_sid_rooms = {}     # socket id -> set(session ids)


def _user_from_cookie():
    token = request.cookies.get("access_token_cookie")
    if not token:
        return None
    try:
        return decode_token(token)["sub"]
    except Exception:
        return None


@socketio.on("connect")
def on_connect():
    uid = _user_from_cookie()
    if not uid:
        return False  # reject unauthenticated sockets
    _sid_user[request.sid] = uid


@socketio.on("disconnect")
def on_disconnect():
    for sid_room in list(_sid_rooms.pop(request.sid, [])):
        emit("peer_left", {}, room=sid_room, include_self=False)
    _sid_user.pop(request.sid, None)


def _authorized(session_id):
    uid = _sid_user.get(request.sid)
    s = db.session.get(TherapySession, session_id or "")
    if not uid or not s or not participant_role(s, uid) or s.status != "live":
        return None
    return s


@socketio.on("join_session")
def on_join(data):
    s = _authorized((data or {}).get("session_id"))
    if not s:
        emit("error_message", {"message": "You can't join this session."})
        return

    # who is already in this room (before I join)?
    others = [
        sid for sid, rooms in _sid_rooms.items()
        if s.id in rooms and sid != request.sid
    ]

    join_room(s.id)
    _sid_rooms.setdefault(request.sid, set()).add(s.id)

    # tell the people already here that I arrived
    emit("peer_joined", {}, room=s.id, include_self=False)
    # tell ME that someone was already here (otherwise a late-joining caller never sends an offer)
    if others:
        emit("peer_present", {})


@socketio.on("signal")
def on_signal(data):
    s = _authorized((data or {}).get("session_id"))
    if s:
        emit("signal", {"data": data.get("data")}, room=s.id, include_self=False)


@socketio.on("leave_session")
def on_leave(data):
    sid_room = (data or {}).get("session_id")
    if sid_room:
        leave_room(sid_room)
        _sid_rooms.get(request.sid, set()).discard(sid_room)
        emit("peer_left", {}, room=sid_room, include_self=False)