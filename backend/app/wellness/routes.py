from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.emotion_result import EmotionResult
from app.models.journal_entry import JournalEntry
from app.models.appointment import Appointment
from app.models.recovery import RecoveryProgress
from app.utils.timeutils import utcnow, utc_to_local

wellness_bp = Blueprint("wellness", __name__)

MOOD_SCORES = {"struggling": 1, "low": 2, "okay": 3, "good": 4, "great": 5}
TOTAL_DAYS = 7


def _streak(days_done):
    n = 0
    while (n + 1) in days_done:
        n += 1
    return n


@wellness_bp.route("/progress", methods=["GET"])
@jwt_required()
def progress():
    uid = get_jwt_identity()
    since = utcnow() - timedelta(days=60)
    emotions = EmotionResult.query.filter(EmotionResult.user_id == uid, EmotionResult.created_at >= since).order_by(EmotionResult.created_at).all()
    journals = JournalEntry.query.filter(JournalEntry.user_id == uid, JournalEntry.created_at >= since).order_by(JournalEntry.created_at).all()

    mood_points = [{"date": utc_to_local(j.created_at).date().isoformat(), "score": MOOD_SCORES[j.mood_tag], "mood": j.mood_tag}
                   for j in journals if j.mood_tag in MOOD_SCORES]
    emotion_counts = {}
    for e in emotions:
        emotion_counts[e.primary_emotion] = emotion_counts.get(e.primary_emotion, 0) + 1
    done = {r.day for r in RecoveryProgress.query.filter_by(user_id=uid)}
    sessions = Appointment.query.filter_by(user_id=uid, status="completed").count()
    return jsonify({
        "mood_trend": mood_points,
        "emotion_counts": [{"emotion": k, "count": v} for k, v in sorted(emotion_counts.items(), key=lambda x: -x[1])],
        "checkins": [{"date": utc_to_local(e.created_at).date().isoformat(), "emotion": e.primary_emotion} for e in emotions],
        "totals": {"checkins": len(emotions), "journal_entries": len(journals), "sessions_completed": sessions,
                   "recovery_days": len(done), "recovery_streak": _streak(done)},
        "note": "These charts reflect what you've logged. They are not a medical assessment.",
    })


@wellness_bp.route("/recovery", methods=["GET"])
@jwt_required()
def recovery():
    rows = RecoveryProgress.query.filter_by(user_id=get_jwt_identity()).all()
    done = {r.day for r in rows}
    return jsonify({"completed_days": sorted(done), "streak": _streak(done), "total_days": TOTAL_DAYS,
                    "notes": {r.day: r.note for r in rows}})


@wellness_bp.route("/recovery/complete", methods=["POST"])
@jwt_required()
def complete_day():
    uid = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    try:
        day = int(data.get("day")); assert 1 <= day <= TOTAL_DAYS
    except (TypeError, ValueError, AssertionError):
        return jsonify({"error": "validation_error", "message": "Choose a day from 1 to 7."}), 422
    done = {r.day for r in RecoveryProgress.query.filter_by(user_id=uid)}
    if day in done:
        return jsonify({"message": "Already completed.", "completed_days": sorted(done)})
    if day > len(done) + 1:
        return jsonify({"error": "conflict", "message": "Take it one day at a time — finish the earlier days first."}), 409
    db.session.add(RecoveryProgress(user_id=uid, day=day, note=(data.get("note") or "")[:500]))
    db.session.commit()
    done.add(day)
    return jsonify({"message": "Nicely done.", "completed_days": sorted(done), "streak": _streak(done)})


@wellness_bp.route("/recovery/reset", methods=["POST"])
@jwt_required()
def reset_recovery():
    RecoveryProgress.query.filter_by(user_id=get_jwt_identity()).delete()
    db.session.commit()
    return jsonify({"message": "Journey restarted."})
