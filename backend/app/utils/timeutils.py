from datetime import datetime, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def utcnow():
    """Naive UTC 'now' — the app stores all datetimes as naive UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_naive(dt):
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def parse_iso_utc(value):
    """Parses '2026-10-01T10:30:00Z' / offsets / naive strings into naive UTC."""
    if not isinstance(value, str):
        raise ValueError("not a string")
    return to_utc_naive(datetime.fromisoformat(value.replace("Z", "+00:00")))


def local_to_utc(local_naive, tz=IST):
    return local_naive.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)


def utc_to_local(utc_naive, tz=IST):
    return utc_naive.replace(tzinfo=timezone.utc).astimezone(tz)
