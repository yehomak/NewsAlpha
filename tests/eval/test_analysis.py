from app.db.models import Direction
from app.eval.analysis import SignalRow, multi_horizon_accuracy, pearson_ic, profit_factor


def _row(
    direction: Direction,
    return_pct: float,
    correct: bool,
    snapshots: dict | None = None,
) -> SignalRow:
    return SignalRow(
        direction=direction,
        return_pct=return_pct,
        correct=correct,
        price_t0=100.0,
        snapshots=snapshots or {},
    )


class TestPearsonIC:
    def test_positive_ic_bullish_up(self) -> None:
        rows = [_row(Direction.BULLISH, 2.0, True)] * 10
        rows += [_row(Direction.BEARISH, -2.0, True)] * 10
        ic, n = pearson_ic(rows)
        assert ic is not None and ic > 0
        assert n == 20

    def test_negative_ic_bullish_down(self) -> None:
        rows = [_row(Direction.BULLISH, -2.0, False)] * 10
        rows += [_row(Direction.BEARISH, 2.0, False)] * 10
        ic, n = pearson_ic(rows)
        assert ic is not None and ic < 0
        assert n == 20

    def test_neutrals_excluded(self) -> None:
        rows = [_row(Direction.NEUTRAL, 5.0, False)] * 20
        ic, n = pearson_ic(rows)
        assert ic is None
        assert n == 0

    def test_below_min_sample_returns_none(self) -> None:
        rows = [_row(Direction.BULLISH, 1.0, True)] * 4
        ic, n = pearson_ic(rows)
        assert ic is None
        assert n == 4

    def test_all_same_direction_returns_none(self) -> None:
        # std_x == 0 when all signals are the same direction
        rows = [_row(Direction.BULLISH, float(i), True) for i in range(10)]
        ic, n = pearson_ic(rows)
        assert ic is None
        assert n == 10


class TestProfitFactor:
    def test_wins_larger_than_losses(self) -> None:
        rows = [_row(Direction.BULLISH, 3.0, True)] * 5 + [_row(Direction.BULLISH, -1.0, False)] * 5
        pf = profit_factor(rows)
        assert pf is not None and pf == 3.0

    def test_neutrals_excluded(self) -> None:
        rows = [_row(Direction.NEUTRAL, 5.0, True)] * 10
        assert profit_factor(rows) is None

    def test_all_wins_returns_none(self) -> None:
        rows = [_row(Direction.BULLISH, 2.0, True)] * 5
        assert profit_factor(rows) is None

    def test_all_losses_returns_none(self) -> None:
        rows = [_row(Direction.BEARISH, 2.0, False)] * 5
        assert profit_factor(rows) is None


class TestMultiHorizon:
    def test_correct_at_each_offset(self) -> None:
        snaps = {1: 102.0, 2: 103.0, 3: 104.0, 4: 105.0, 5: 106.0}
        rows = [_row(Direction.BULLISH, 6.0, True, snaps)] * 10
        pts = multi_horizon_accuracy(rows)
        assert len(pts) == 5
        for pt in pts:
            assert pt.accuracy_pct == 100.0
            assert pt.n == 10

    def test_missing_offset_excluded(self) -> None:
        # Only has snapshot at offset 1, not 2–5
        rows = [_row(Direction.BULLISH, 2.0, True, {1: 102.0})] * 5
        pts = multi_horizon_accuracy(rows)
        assert pts[0].n == 5  # T+1
        for pt in pts[1:]:
            assert pt.n == 0  # T+2 through T+5 missing
            assert pt.accuracy_pct is None

    def test_correct_direction_bearish(self) -> None:
        snaps = {1: 98.0}  # price dropped → bearish correct
        rows = [_row(Direction.BEARISH, -2.0, True, snaps)] * 8
        pts = multi_horizon_accuracy(rows)
        assert pts[0].accuracy_pct == 100.0
        assert pts[0].n == 8
