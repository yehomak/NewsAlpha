from datetime import UTC, datetime, timedelta

from app.eval.pricer import t5_date, t5_elapsed


def test_t5_date_adds_5_days() -> None:
    t0 = datetime(2026, 9, 1, 14, 30, tzinfo=UTC)
    assert t5_date(t0) == (t0 + timedelta(days=5)).date()


def test_t5_elapsed_false_before_cutoff() -> None:
    # T+0 set far in the future — T+5 hasn't passed yet
    t0 = datetime.now(UTC) + timedelta(days=10)
    assert t5_elapsed(t0) is False


def test_t5_elapsed_true_after_cutoff() -> None:
    # T+0 well in the past — T+5 + buffer has passed
    t0 = datetime.now(UTC) - timedelta(days=10)
    assert t5_elapsed(t0) is True


def test_t5_elapsed_boundary_before() -> None:
    # Just inside the window (T+5 + 16h = not yet elapsed)
    t0 = datetime.now(UTC) - timedelta(days=5, hours=16)
    assert t5_elapsed(t0) is False


def test_t5_elapsed_boundary_after() -> None:
    # Just past the window (T+5 + 18h = elapsed)
    t0 = datetime.now(UTC) - timedelta(days=5, hours=18)
    assert t5_elapsed(t0) is True
