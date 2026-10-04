from datetime import timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from app.extensions import db
from app.constants import CONCERNS
from app.models.therapist import Therapist, TherapistSpecialization, TherapistLanguage
from app.models.review import Review
from app.appointments.service import slots_for_day
from app.therapists.matching import score_therapist
from app.utils.timeutils import utc_to_local, utcnow, IST
from datetime import datetime

therapists_bp = Blueprint("therapists", __name__)
matching_bp = Blueprint("matching", __name__)

DISCLAIMER = "This is a recommendation based on your preferences, not a clinical recommendation."


def _public_query():
    return Therapist.query.filter_by(is_verified=True, is_accepting_clients=True)


def next_available(therapist, horizon_days=14):
    today = utc_to_local(utcnow()).date()
    for i in range(horizon_days):
        slots = slots_for_day(therapist, today + timedelta(days=i))
        if slots:
            return slots[0]
    return None


def _card(t):
    card = t.to_card_dict()
    nxt = next_available(t)
    card["next_available"] = nxt.isoformat() + "Z" if nxt else None
    return card


@therapists_bp.route("", methods=["GET"])
def list_therapists():
    q = _public_query()
    a = request.args
    if a.get("specialization") in CONCERNS:
        q = q.filter(Therapist.specializations.any(TherapistSpecialization.name == a["specialization"]))
    if a.get("language"):
        q = q.filter(Therapist.languages.any(TherapistLanguage.language == a["language"]))
    if a.get("max_price", type=int) is not None:
        q = q.filter(Therapist.session_price <= a.get("max_price", type=int))
    if a.get("gender") in ("female", "male", "non_binary"):
        q = q.filter(Therapist.gender == a["gender"])
    if a.get("min_experience", type=int):
        q = q.filter(Therapist.years_experience >= a.get("min_experience", type=int))

    search = (a.get("q") or "").strip().lower()
    therapists = q.all()
    if a.get("mode") in ("video", "audio", "text"):
        therapists = [t for t in therapists if a["mode"] in t.session_modes()]

    if search:
        tokens = [w for w in search.replace("_", " ").split() if len(w) > 2 and w not in ("for", "the", "find", "therapist", "with", "and")]
        def relevance(t):
            hay = " ".join([t.display_name, t.bio or "", t.qualification] +
                           [CONCERNS.get(s.name, s.name) + " " + s.name.replace("_", " ") for s in t.specializations]).lower()
            return sum(1 for w in tokens if w in hay)
        scored = [(relevance(t), t) for t in therapists]
        therapists = [t for r, t in sorted(scored, key=lambda x: -x[0]) if r > 0] if tokens else therapists

    cards = [_card(t) for t in therapists]
    if a.get("available_within_days", type=int):
        limit = utcnow() + timedelta(days=a.get("available_within_days", type=int))
        cards = [c for c in cards if c["next_available"] and c["next_available"] <= limit.isoformat() + "Z"]

    if not cards:
        return jsonify({"therapists": [], "empty_message": "No therapists found. Try changing your language, availability or specialization filters."})
    return jsonify({"therapists": cards})


@therapists_bp.route("/<therapist_id>", methods=["GET"])
def get_therapist(therapist_id):
    t = db.session.get(Therapist, therapist_id)
    if not t or not t.is_verified:
        return jsonify({"error": "not_found", "message": "Therapist not found."}), 404
    detail = _card(t)
    detail.update(bio=t.bio, approach=t.approach, gender=t.gender)
    reviews = Review.query.filter_by(therapist_id=t.id, is_flagged=False).order_by(Review.created_at.desc()).limit(10).all()
    detail["reviews"] = [{"rating": r.rating, "comment": r.comment, "created_at": r.created_at.isoformat() + "Z"} for r in reviews]
    return jsonify({"therapist": detail})


@therapists_bp.route("/<therapist_id>/slots", methods=["GET"])
def get_slots(therapist_id):
    t = db.session.get(Therapist, therapist_id)
    if not t or not t.is_verified:
        return jsonify({"error": "not_found", "message": "Therapist not found."}), 404
    days = min(max(request.args.get("days", 7, type=int), 1), 21)
    today = utc_to_local(utcnow()).date()
    out = []
    for i in range(days):
        d = today + timedelta(days=i)
        out.append({"date": d.isoformat(), "slots": [s.isoformat() + "Z" for s in slots_for_day(t, d)]})
    return jsonify({"days": out, "timezone": "Asia/Kolkata"})


@matching_bp.route("", methods=["POST"])
def match():
    prefs = request.get_json(silent=True) or {}
    prefs["budget"] = prefs.get("budget") if isinstance(prefs.get("budget"), int) else None
    results = []
    for t in _public_query().all():
        nxt = next_available(t)
        points, reasons = score_therapist(t, prefs, nxt)
        card = t.to_card_dict()
        card["next_available"] = nxt.isoformat() + "Z" if nxt else None
        results.append({"therapist": card, "score": points, "reasons": reasons})
    results.sort(key=lambda r: (-r["score"], r["therapist"]["session_price"]))
    return jsonify({"matches": results[:5], "disclaimer": DISCLAIMER})
