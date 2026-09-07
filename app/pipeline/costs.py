from decimal import Decimal

from anthropic.types import Usage

# Per-token prices in USD (Anthropic list pricing, 2025)
_PRICES: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 0.80 / 1_000_000, "output": 4.00 / 1_000_000},
    "claude-sonnet-5": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
}


def compute_cost(usage: Usage, model: str) -> Decimal:
    prices = _PRICES.get(model, _PRICES["claude-haiku-4-5-20251001"])
    raw = usage.input_tokens * prices["input"] + usage.output_tokens * prices["output"]
    return Decimal(str(round(raw, 6)))
