import pytest

from app.db.models import Direction
from app.eval.runner import _is_correct


@pytest.mark.parametrize(
    ("direction", "return_pct", "expected"),
    [
        (Direction.BULLISH, 2.5, True),
        (Direction.BULLISH, 0.0, False),
        (Direction.BULLISH, -1.0, False),
        (Direction.BEARISH, -2.5, True),
        (Direction.BEARISH, 0.0, False),
        (Direction.BEARISH, 1.0, False),
        (Direction.NEUTRAL, 0.5, True),  # within ±1%
        (Direction.NEUTRAL, -0.9, True),  # within ±1%
        (Direction.NEUTRAL, 1.1, False),  # outside ±1%
        (Direction.NEUTRAL, -1.1, False),  # outside ±1%
    ],
)
def test_is_correct(direction: Direction, return_pct: float, expected: bool) -> None:
    assert _is_correct(direction, return_pct) == expected
