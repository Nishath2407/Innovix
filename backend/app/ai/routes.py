from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.emotion_result import EmotionResult
from app.models.risk_assessment import RiskAssessment
from app.ai.emotion_service import classify_emotion
from app.ai.risk_service import assess_risk

ai_bp = Blueprint("ai", __name__)

SUPPORTIVE_COPY = {
    "anxiety": "Your message shows signs of anxiety.",
    "fear": "Your message shows signs of fear.",
    "sadness": "Your message shows signs of sadness.",
    "anger": "Your message shows signs of frustration or anger.",
    "stress": "Your message shows signs of stress.",
    "neutral": "Your message doesn't show strong signs of distress right now.",
}


@ai_bp.route("/check-in", methods=["POST"])
@jwt_required()
def check_in():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "validation_error", "fields": {"text": "Please share what's on your mind."}}), 422
    if len(text) > 4000:
        return jsonify({"error": "validation_error", "fields": {"text": "Please keep this under 4000 characters."}}), 422

    emotion = classify_emotion(text)
    risk = assess_risk(text, emotion["scores"])

    emotion_result = EmotionResult(
        user_id=user_id,
        input_text=text,
        primary_emotion=emotion["primary_emotion"],
        emotion_scores=emotion["scores"],
    )
    db.session.add(emotion_result)
    db.session.flush()  # get emotion_result.id before commit

    risk_assessment = RiskAssessment(
        user_id=user_id,
        check_in_text_ref=emotion_result.id,
        score=risk["score"],
        tier=risk["tier"],
        signals=risk["signals"],
    )
    db.session.add(risk_assessment)
    db.session.commit()

    message = SUPPORTIVE_COPY.get(emotion["primary_emotion"], "Thanks for sharing how you're feeling.")

    return jsonify({
        "primary_emotion": emotion["primary_emotion"],
        "message": message,
        "risk": risk_assessment.to_user_facing_dict(),
        "show_safety_resources": risk["tier"] in ("moderate", "high"),
        "emergency_note": "If you might be in immediate danger, contact your local emergency services now." if risk["tier"] == "high" else None,
        "disclaimer": "This is a supportive check-in, not a diagnosis. Consider speaking with a licensed therapist.",
    })


@ai_bp.route("/check-in/history", methods=["GET"])
@jwt_required()
def check_in_history():
    user_id = get_jwt_identity()
    results = (EmotionResult.query.filter_by(user_id=user_id)
               .order_by(EmotionResult.created_at.desc()).limit(30).all())
    return jsonify({
        "history": [
            {"id": r.id, "primary_emotion": r.primary_emotion, "created_at": r.created_at.isoformat()}
            for r in results
        ]
    })


@ai_bp.route("/check-in/summary", methods=["POST"])
@jwt_required()
def pre_session_summary():
    """Builds a PRIVATE pre-session summary from recent check-ins plus what the
    user typed. Nothing is shared with a therapist unless the user opts in on
    the appointment itself."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    recent = (EmotionResult.query.filter_by(user_id=user_id)
              .order_by(EmotionResult.created_at.desc()).limit(5).all())
    counts = {}
    for r in recent:
        counts[r.primary_emotion] = counts.get(r.primary_emotion, 0) + 1
    topics = [str(t)[:80] for t in (data.get("topics") or [])][:8]
    questions = (data.get("questions") or "").strip()[:1000]
    return jsonify({"summary": {
        "emotions_noticed": [{"emotion": k, "times": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])],
        "topics": topics, "questions": questions, "based_on_checkins": len(recent),
        "note": "Private to you. Automated observations, not a diagnosis.",
    }})
