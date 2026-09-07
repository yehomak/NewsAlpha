from decimal import Decimal
from unittest.mock import MagicMock

from app.pipeline.costs import compute_cost


def _usage(input_tokens: int, output_tokens: int) -> MagicMock:
    u = MagicMock()
    u.input_tokens = input_tokens
    u.output_tokens = output_tokens
    return u


def test_haiku_cost_is_small() -> None:
    cost = compute_cost(_usage(1000, 200), "claude-haiku-4-5-20251001")
    # 1000 * 0.0000008 + 200 * 0.000004 = 0.0008 + 0.0008 = 0.0016
    assert cost == Decimal("0.001600")


def test_sonnet_cost_higher_than_haiku() -> None:
    usage = _usage(1000, 200)
    haiku_cost = compute_cost(usage, "claude-haiku-4-5-20251001")
    sonnet_cost = compute_cost(usage, "claude-sonnet-5")
    assert sonnet_cost > haiku_cost


def test_zero_tokens_is_zero() -> None:
    assert compute_cost(_usage(0, 0), "claude-haiku-4-5-20251001") == Decimal("0.000000")


def test_unknown_model_falls_back_to_haiku() -> None:
    cost = compute_cost(_usage(1000, 0), "claude-unknown-model")
    haiku_cost = compute_cost(_usage(1000, 0), "claude-haiku-4-5-20251001")
    assert cost == haiku_cost
