import math
from dataclasses import dataclass, field

from app.db.models import Direction

_NEUTRAL_BAND_PCT = 1.0


@dataclass
class SignalRow:
    direction: Direction
    return_pct: float
    correct: bool
    price_t0: float
    snapshots: dict[int, float] = field(default_factory=dict)  # offset_days -> price


def _encode(direction: Direction) -> float:
    if direction == Direction.BULLISH:
        return 1.0
    if direction == Direction.BEARISH:
        return -1.0
    return 0.0


def pearson_ic(rows: list[SignalRow]) -> tuple[float | None, int]:
    """Pearson correlation between encoded direction and return_pct.

    Neutral signals excluded — they carry no directional conviction.
    Returns (ic, n) where n is the sample size used.
    """
    pairs = [(_encode(r.direction), r.return_pct) for r in rows if r.direction != Direction.NEUTRAL]
    n = len(pairs)
    if n < 5:
        return None, n

    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    cov = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    std_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    std_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))

    if std_x == 0 or std_y == 0:
        return None, n

    return round(cov / (std_x * std_y), 4), n


def profit_factor(rows: list[SignalRow]) -> float | None:
    """avg_return_when_correct / |avg_return_when_incorrect|, directional signals only.

    > 1.0 means wins are larger than losses on average.
    """
    directional = [r for r in rows if r.direction != Direction.NEUTRAL]
    wins = [r.return_pct for r in directional if r.correct]
    losses = [r.return_pct for r in directional if not r.correct]

    if not wins or not losses:
        return None

    avg_win = sum(wins) / len(wins)
    avg_loss = abs(sum(losses) / len(losses))

    if avg_loss == 0:
        return None

    return round(avg_win / avg_loss, 3)


@dataclass
class HorizonPoint:
    offset: int
    accuracy_pct: float | None
    n: int


def _correct_at(direction: Direction, price_t0: float, price_at: float) -> bool:
    ret = (price_at - price_t0) / price_t0 * 100
    if direction == Direction.BULLISH:
        return ret > 0
    if direction == Direction.BEARISH:
        return ret < 0
    return abs(ret) <= _NEUTRAL_BAND_PCT


def multi_horizon_accuracy(rows: list[SignalRow]) -> list[HorizonPoint]:
    """Directional accuracy at each offset T+1 through T+5.

    Signals missing a snapshot at a given offset are excluded from that offset's n.
    """
    result: list[HorizonPoint] = []
    for offset in range(1, 6):
        eligible = [r for r in rows if offset in r.snapshots and r.price_t0 > 0]
        n = len(eligible)
        if n == 0:
            result.append(HorizonPoint(offset=offset, accuracy_pct=None, n=0))
            continue
        correct = sum(
            1 for r in eligible if _correct_at(r.direction, r.price_t0, r.snapshots[offset])
        )
        result.append(HorizonPoint(offset=offset, accuracy_pct=round(correct / n * 100, 1), n=n))
    return result
