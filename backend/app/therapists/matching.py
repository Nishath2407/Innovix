"""Transparent therapist matching. Every point of the score is explained back
to the user. This is a preference-based recommendation, not clinical advice."""
from datetime import timedelta
from app.constants import CONCERNS, LANGUAGES
from app.models.therapist import TherapistAvailability
from app.utils.timeutils import utcnow

WEIGHTS = {"concern": 40, "language": 15, "mode": 10, "time": 15, "budget": 10, "gender": 5, "urgency": 5}
TIME_BANDS = {"morning": (6, 12), "afternoon": (12, 17), "evening": (17, 22)}


def _band_overlap(rules, band):
    lo, hi = TIME_BANDS[band]
    return any(r.start_time.hour < hi and r.end_time.hour > lo for r in rules)


def score_therapist(t, prefs, next_slot=None):
    pts, reasons = 0, []
    specs = {s.name for s in t.specializations}
    langs = {l.language for l in t.languages}

    concern = prefs.get("concern")
    if concern in specs:
        pts += WEIGHTS["concern"]
        reasons.append(f"Specializes in {CONCERNS[concern].lower()}")
    elif concern and specs & {"general_wellbeing"}:
        pts += WEIGHTS["concern"] * 0.4
        reasons.append("Works with general emotional wellbeing")
    elif not concern:
        pts += WEIGHTS["concern"] * 0.5

    lang = prefs.get("language")
    if not lang or lang in langs:
        pts += WEIGHTS["language"]
        if lang:
            reasons.append(f"Speaks {LANGUAGES.get(lang, lang)}")
    
    mode = prefs.get("mode")
    if not mode or mode in t.session_modes():
        pts += WEIGHTS["mode"]
        if mode:
            reasons.append(f"Offers {mode} sessions")

    gender = prefs.get("gender")
    if not gender or gender == "any" or t.gender == gender:
        pts += WEIGHTS["gender"]
        if gender and gender != "any":
            reasons.append(f"{gender.capitalize()} therapist, as you preferred")

    band = prefs.get("time")
    if not band or band == "any":
        pts += WEIGHTS["time"]
    else:
        rules = TherapistAvailability.query.filter_by(therapist_id=t.id, is_blocked=False).all()
        if band in TIME_BANDS and _band_overlap(rules, band):
            pts += WEIGHTS["time"]
            reasons.append(f"Available in the {band}")

    budget = prefs.get("budget")
    if not budget or t.session_price <= budget:
        pts += WEIGHTS["budget"]
        if budget:
            reasons.append(f"Within your budget (₹{t.session_price})")

    if prefs.get("urgency") == "soon":
        if next_slot and next_slot <= utcnow() + timedelta(days=2):
            pts += WEIGHTS["urgency"]
            reasons.append("Has an opening within 2 days")
    else:
        pts += WEIGHTS["urgency"]

    return round(pts), reasons
