from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

_MARKET_OPEN = time(9, 30)
_MARKET_CLOSE = time(16, 0)


def _to_et(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ET)


def is_market_hours(dt: datetime) -> bool:
    """True if dt falls within a regular NYSE session (Mon–Fri 9:30–16:00 ET).
    Does not account for market holidays — close enough for T+0 anchoring.
    """
    et = _to_et(dt)
    return et.weekday() < 5 and _MARKET_OPEN <= et.time() < _MARKET_CLOSE


def next_market_open(dt: datetime) -> datetime:
    """Return the next NYSE open at or after dt (9:30 ET, Mon–Fri)."""
    et = _to_et(dt)
    # same day before open → today's open
    if et.weekday() < 5 and et.time() < _MARKET_OPEN:
        candidate = et.replace(hour=9, minute=30, second=0, microsecond=0)
        return candidate.astimezone(UTC)
    # advance one calendar day, then skip weekends
    et = et.replace(hour=9, minute=30, second=0, microsecond=0) + timedelta(days=1)
    while et.weekday() >= 5:
        et += timedelta(days=1)
    return et.astimezone(UTC)


def t0_anchor(published_at: datetime | None, signal_created_at: datetime) -> datetime:
    """The correct T+0 price timestamp for a signal.

    If the news hit during market hours, use published_at (price already moving).
    Otherwise the price reaction happens at the next open.
    """
    dt = published_at if published_at is not None else signal_created_at
    if is_market_hours(dt):
        return dt
    return next_market_open(dt)
