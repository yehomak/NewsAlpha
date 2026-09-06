---
name: eval-design
description: Eval harness design rules for butterfly-effect. Auto-invoked when discussing signal accuracy, T+5 logic, eval segmentation, or changes to the evaluation pipeline. Prevents look-ahead bias and keeps eval results credible.
---

# Eval Design Rules — butterfly-effect

## Core definition

A signal is **correct** if the stock moved in the predicted direction by market close on T+5 trading days after signal creation.

```
correct = (direction == "bullish" and price_t5 > price_t0) or
          (direction == "bearish" and price_t5 < price_t0)
# neutral signals are not evaluated for directional accuracy
```

## T+5 means trading days

5 calendar days is wrong. Use market-aware date arithmetic:

```python
import pandas_market_calendars as mcal

nyse = mcal.get_calendar("NYSE")

def get_t5_date(signal_created_at: datetime) -> date:
    schedule = nyse.schedule(start_date=signal_created_at.date(), end_date=signal_created_at.date() + timedelta(days=14))
    trading_days = mcal.date_range(schedule, frequency="1D")
    return trading_days[5].date()  # 0-indexed: T+0 is same day if market open
```

## After-hours correction

If news is published outside market hours (before 9:30 AM or after 4:00 PM ET), T+0 price = **next market open**, not the current close.

```python
def get_t0_price_date(published_at: datetime) -> date:
    et = published_at.astimezone(ZoneInfo("America/New_York"))
    market_open = et.replace(hour=9, minute=30)
    market_close = et.replace(hour=16, minute=0)
    if et < market_open or et >= market_close:
        # use next trading day open
        return get_next_trading_day(et.date())
    return et.date()
```

## Required segmentation

Never report a single aggregate accuracy number. Always segment by:

| Dimension | Why |
|---|---|
| `event_type` | Earnings often invert post-announcement |
| Confidence band | Low/medium/high — validates model calibration |
| News source | Identifies low-quality signal sources |
| Sample size | Flag N < 20 as statistically unreliable |

## Accuracy targets

| Level | Accuracy | Interpretation |
|---|---|---|
| Random baseline | 50% | Coin flip |
| Weak signal | 52–54% | Marginal, needs more data |
| Credible range | 55–62% | Claim this in the README |
| Suspect | >65% | Likely in-sample overfitting |

Do not optimize to beat 65%+ — it undermines credibility.

## Look-ahead bias rules

The pipeline is forward-only: signals generated using only information available at publication time.

**Safe changes:**
- Prompt improvements to the reasoning chain
- Adding more context to entity extraction
- Filtering by confidence threshold
- Changing the evaluation window (T+3, T+10) — but document it as a design choice

**Unsafe — introduces look-ahead bias:**
- Using price data from T+1 to T+4 in the reasoning chain
- Training on historical signal/outcome pairs and using those weights in generation
- Adding technical indicators computed after publication time

## `eval_results` write pattern

```python
eval_result = EvalResult(
    signal_id=signal.id,
    price_t0=Decimal(str(price_t0)),
    price_t5=Decimal(str(price_t5)),
    return_pct=float((price_t5 - price_t0) / price_t0 * 100),
    correct=correct,
)
session.add(eval_result)
await session.commit()
```

Always use `Decimal` for prices — never `float` for money storage.
