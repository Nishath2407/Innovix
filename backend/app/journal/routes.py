from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.journal_entry import JournalEntry

MOODS = {"great", "good", "okay", "low", "struggling"}

journal_bp = Blueprint("journal", __name__)


@journal_bp.route("", methods=["GET"])
@jwt_required()
def list_entries():
    user_id = get_jwt_identity()
    q = request.args.get("q", "").strip()
    query = JournalEntry.query.filter_by(user_id=user_id)
    if q:
        query = query.filter(JournalEntry.body.ilike(f"%{q}%"))
    entries = query.order_by(JournalEntry.created_at.desc()).all()
    return jsonify({"entries": [e.to_dict() for e in entries]})


@journal_bp.route("", methods=["POST"])
@jwt_required()
def create_entry():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "validation_error", "fields": {"body": "Entry cannot be empty."}}), 422

    entry = JournalEntry(
        user_id=user_id,
        title=(data.get("title") or "").strip()[:200],
        body=body,
        mood_tag=data.get("mood_tag") if data.get("mood_tag") in MOODS else None,
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"entry": entry.to_dict()}), 201


def _get_owned_entry(entry_id, user_id):
    entry = db.session.get(JournalEntry, entry_id)
    if not entry or entry.user_id != user_id:
        return None
    return entry


@journal_bp.route("/<entry_id>", methods=["PUT"])
@jwt_required()
def update_entry(entry_id):
    entry = _get_owned_entry(entry_id, get_jwt_identity())
    if not entry:
        return jsonify({"error": "not_found"}), 404

    data = request.get_json(silent=True) or {}
    if "title" in data:
        entry.title = (data["title"] or "").strip()[:200]
    if "body" in data and (data["body"] or "").strip():
        entry.body = data["body"].strip()
    if "mood_tag" in data:
        entry.mood_tag = data["mood_tag"] if data["mood_tag"] in MOODS else None

    db.session.commit()
    return jsonify({"entry": entry.to_dict()})


@journal_bp.route("/<entry_id>", methods=["DELETE"])
@jwt_required()
def delete_entry(entry_id):
    entry = _get_owned_entry(entry_id, get_jwt_identity())
    if not entry:
        return jsonify({"error": "not_found"}), 404
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Entry deleted."})
