from datetime import datetime
from zoneinfo import ZoneInfo

from app.pipeline.market_hours import is_market_hours, next_market_open, t0_anchor

ET = ZoneInfo("America/New_York")


def _et(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=ET)


# --- is_market_hours ---


def test_midday_weekday_is_market_hours() -> None:
    assert is_market_hours(_et(2026, 9, 14, 12)) is True  # Monday noon ET


def test_before_open_is_not_market_hours() -> None:
    assert is_market_hours(_et(2026, 9, 14, 9, 0)) is False  # 9:00 ET


def test_after_close_is_not_market_hours() -> None:
    assert is_market_hours(_et(2026, 9, 14, 16, 30)) is False


def test_exact_open_is_market_hours() -> None:
    assert is_market_hours(_et(2026, 9, 14, 9, 30)) is True


def test_exact_close_is_not_market_hours() -> None:
    assert is_market_hours(_et(2026, 9, 14, 16, 0)) is False  # close is exclusive


def test_saturday_is_not_market_hours() -> None:
    assert is_market_hours(_et(2026, 9, 12, 12)) is False


def test_sunday_is_not_market_hours() -> None:
    assert is_market_hours(_et(2026, 9, 13, 12)) is False


# --- next_market_open ---


def test_next_open_from_after_close_is_next_day() -> None:
    after_close = _et(2026, 9, 14, 17)  # Monday 5pm ET
    result = next_market_open(after_close).astimezone(ET)
    assert result.weekday() == 1  # Tuesday
    assert result.hour == 9 and result.minute == 30


def test_next_open_skips_weekend() -> None:
    friday_close = _et(2026, 9, 11, 17)  # Friday 5pm ET → Monday open
    result = next_market_open(friday_close).astimezone(ET)
    assert result.weekday() == 0  # Monday
    assert result.hour == 9 and result.minute == 30


def test_next_open_before_open_same_day() -> None:
    pre_open = _et(2026, 9, 14, 7)  # Monday 7am ET
    result = next_market_open(pre_open).astimezone(ET)
    assert result.weekday() == 0  # same Monday
    assert result.hour == 9 and result.minute == 30


# --- t0_anchor ---


def test_t0_during_market_uses_published_at() -> None:
    pub = _et(2026, 9, 14, 14)  # 2pm ET, market hours
    created = _et(2026, 9, 14, 14, 1)
    assert t0_anchor(pub, created) == pub


def test_t0_after_hours_uses_next_open() -> None:
    pub = _et(2026, 9, 14, 18)  # Monday 6pm ET, after hours
    created = _et(2026, 9, 14, 18, 1)
    result = t0_anchor(pub, created).astimezone(ET)
    assert result.weekday() == 1 and result.hour == 9 and result.minute == 30  # Tuesday


def test_t0_none_published_uses_created_at() -> None:
    created = _et(2026, 9, 14, 14)  # market hours
    result = t0_anchor(None, created)
    assert result == created
