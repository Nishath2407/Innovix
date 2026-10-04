"""Booking logic: slot generation, availability checks, stale-hold release.

All times are stored as naive UTC. Therapist availability is defined in local
(IST) wall-clock time per weekday, so slot generation converts local -> UTC.
"""
from datetime import datetime, timedelta, time
from flask import current_app
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.appointment import Appointment, ACTIVE_STATUSES
from app.models.therapist import TherapistAvailability
from app.utils.timeutils import IST, local_to_utc, utc_to_local, utcnow


def release_stale_pending(therapist_id=None):
    """Unpaid bookings only hold a slot for a short time."""
    cutoff = utcnow() - timedelta(minutes=current_app.config["PENDING_PAYMENT_HOLD_MINUTES"])
    q = Appointment.query.filter(Appointment.status == "pending", Appointment.created_at < cutoff)
    if therapist_id:
        q = q.filter(Appointment.therapist_id == therapist_id)
    stale = q.all()
    for a in stale:
        a.status = "expired"
    if stale:
        db.session.commit()


def slots_for_day(therapist, day):
    """Bookable start times (naive UTC) for `day` (a date in IST)."""
    release_stale_pending(therapist.id)
    rules = TherapistAvailability.query.filter_by(
        therapist_id=therapist.id, weekday=day.weekday(), is_blocked=False).all()
    if not rules:
        return []

    length = current_app.config["SESSION_LENGTH_MINUTES"]
    now = utcnow()
    day_start = local_to_utc(datetime.combine(day, time.min))
    day_end = day_start + timedelta(days=1)
    taken = {
        a.scheduled_start for a in Appointment.query.filter(
            Appointment.therapist_id == therapist.id,
            Appointment.status.in_(ACTIVE_STATUSES),
            Appointment.scheduled_start >= day_start,
            Appointment.scheduled_start < day_end)
    }

    slots = []
    for rule in rules:
        cursor = datetime.combine(day, rule.start_time)
        end = datetime.combine(day, rule.end_time)
        while cursor + timedelta(minutes=length) <= end:
            start_utc = local_to_utc(cursor)
            if start_utc > now + timedelta(minutes=30) and start_utc not in taken:
                slots.append(start_utc)
            cursor += timedelta(minutes=60)
    return sorted(set(slots))


def is_bookable(therapist, start_utc):
    local = utc_to_local(start_utc)
    return start_utc in slots_for_day(therapist, local.date())


def create_appointment(user_id, therapist, start_utc, mode):
    """Returns (appointment, error_code). The partial unique index is the final
    guard against two people grabbing the same slot at the same instant."""
    if mode not in therapist.session_modes():
        return None, "mode_unavailable"
    if not is_bookable(therapist, start_utc):
        return None, "slot_unavailable"
    length = current_app.config["SESSION_LENGTH_MINUTES"]
    appt = Appointment(
        user_id=user_id, therapist_id=therapist.id, scheduled_start=start_utc,
        scheduled_end=start_utc + timedelta(minutes=length), session_mode=mode,
        status="pending", price=therapist.session_price,
    )
    db.session.add(appt)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, "slot_taken"
    return appt, None
