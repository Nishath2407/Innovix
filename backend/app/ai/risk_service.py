"""
Risk scoring service.

Produces an internal 0-100 score for record-keeping, but the score itself
must NEVER be shown to the user directly — only the translated tier +
supportive next step (see RiskAssessment.to_user_facing_dict()).

This is an automated, heuristic support indicator only. It is explicitly
not a diagnostic or predictive clinical tool.
"""

HIGH_RISK_TERMS = ["kill myself", "end my life", "suicide", "hurt myself", "want to die", "no reason to live"]
MODERATE_RISK_TERMS = ["hopeless", "can't cope", "cant cope", "worthless", "give up", "no one cares"]


def assess_risk(text: str, emotion_scores: dict) -> dict:
    text_lower = text.lower()
    signals = []
    score = 0

    for term in HIGH_RISK_TERMS:
        if term in text_lower:
            signals.append("severe_emotional_distress")
            score = max(score, 90)
            break

    for term in MODERATE_RISK_TERMS:
        if term in text_lower:
            signals.append("repeated_distress")
            score = max(score, 55)

    if emotion_scores.get("fear", 0) > 0.5:
        signals.append("fear")
        score = max(score, 60)
    if emotion_scores.get("sadness", 0) > 0.6:
        signals.append("sadness")
        score = max(score, 40)

    if score >= 80:
        tier = "high"
    elif score >= 40:
        tier = "moderate"
    else:
        tier = "low"

    return {"score": score, "tier": tier, "signals": list(set(signals))}
