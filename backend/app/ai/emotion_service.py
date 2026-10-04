"""
Emotion classification service.

Uses the HuggingFace DistilRoBERTa emotion model
(j-hartmann/emotion-english-distilroberta-base) as specified. The model is
loaded lazily on first use so `flask run` / tests don't require downloading
weights just to boot the app, and a keyword-based fallback keeps the
endpoint usable in offline/dev environments where the model can't be
downloaded (e.g. this sandbox).

IMPORTANT: outputs are supportive, never diagnostic. Nothing here should be
phrased as "you have X" — only "your message shows signs of X".
"""

_pipeline = None
_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

_KEYWORD_FALLBACK = {
    "anxiety": ["anxious", "anxiety", "on edge", "panicking", "worried", "nervous"],
    "sadness": ["sad", "down", "hopeless", "empty", "crying", "depressed"],
    "fear": ["scared", "afraid", "terrified", "fear", "unsafe"],
    "anger": ["angry", "furious", "rage", "resentful", "irritated"],
    "stress": ["stressed", "overwhelmed", "burnt out", "burned out", "pressure"],
}


def _load_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    try:
        from transformers import pipeline
        _pipeline = pipeline(
            "text-classification",
            model=_MODEL_NAME,
            top_k=None,
        )
    except Exception:
        _pipeline = False  # sentinel: model unavailable, use fallback
    return _pipeline


def classify_emotion(text: str) -> dict:
    """Returns {"primary_emotion": str, "scores": {label: float, ...}}"""
    pipe = _load_pipeline()

    if pipe:
        try:
            results = pipe(text[:512])[0]  # list of {label, score}
            scores = {r["label"].lower(): round(float(r["score"]), 4) for r in results}
            primary = max(scores, key=scores.get)
            return {"primary_emotion": primary, "scores": scores}
        except Exception:
            pass  # fall through to keyword fallback

    # --- fallback: simple keyword matching, clearly a placeholder ---
    text_lower = text.lower()
    scores = {}
    for emotion, keywords in _KEYWORD_FALLBACK.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        scores[emotion] = round(min(hits * 0.3, 0.95), 2)

    if all(v == 0 for v in scores.values()):
        scores["neutral"] = 0.6
        primary = "neutral"
    else:
        primary = max(scores, key=scores.get)

    return {"primary_emotion": primary, "scores": scores}
