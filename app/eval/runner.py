from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Direction, EvalResult, PriceSnapshot, Signal
from app.db.session import async_session_factory
from app.eval.pricer import fetch_price, t5_date, t5_elapsed
from app.pipeline.market_hours import t0_anchor

log = structlog.get_logger()


def _is_correct(direction: Direction, return_pct: float) -> bool:
    """Signal is correct when the directional call matches the T+5 return sign."""
    if direction == Direction.BULLISH:
        return return_pct > 0
    if direction == Direction.BEARISH:
        return return_pct < 0
    # Neutral: correct when move is small (within ±1%)
    return abs(return_pct) <= 1.0


async def _fetch_uneval(session: Any) -> list[Signal]:
    result = await session.execute(
        select(Signal)
        .outerjoin(EvalResult, EvalResult.signal_id == Signal.id)
        .where(EvalResult.id.is_(None))
        .options(selectinload(Signal.event))
    )
    return result.scalars().all()  # type: ignore[no-any-return]


async def run_eval() -> int:
    """Evaluate all signals whose T+5 window has elapsed. Returns count of new eval_results."""
    stored = 0
    async with async_session_factory() as session:
        signals = await _fetch_uneval(session)
        log.info("eval.candidates", count=len(signals))

        for signal in signals:
            t0 = t0_anchor(
                signal.event.published_at if signal.event else None,
                signal.created_at,
            )
            if not t5_elapsed(t0):
                continue

            t0_d = t0.date()
            t5_d = t5_date(t0)

            price_t0 = await fetch_price(signal.ticker, t0_d)
            price_t5 = await fetch_price(signal.ticker, t5_d)

            if price_t0 is None or price_t5 is None:
                log.warning(
                    "eval.price_missing",
                    signal_id=signal.id,
                    ticker=signal.ticker,
                    price_t0=str(price_t0),
                    price_t5=str(price_t5),
                )
                continue

            session.add(
                PriceSnapshot(
                    signal_id=signal.id,
                    ticker=signal.ticker,
                    price=price_t0,
                    fetched_at=datetime.now(UTC),
                    offset_days=0,
                )
            )
            session.add(
                PriceSnapshot(
                    signal_id=signal.id,
                    ticker=signal.ticker,
                    price=price_t5,
                    fetched_at=datetime.now(UTC),
                    offset_days=5,
                )
            )

            return_pct = float((price_t5 - price_t0) / price_t0 * Decimal("100"))
            correct = _is_correct(signal.direction, return_pct)

            session.add(
                EvalResult(
                    signal_id=signal.id,
                    price_t0=price_t0,
                    price_t5=price_t5,
                    return_pct=return_pct,
                    correct=correct,
                )
            )
            stored += 1
            log.info(
                "eval.result",
                signal_id=signal.id,
                ticker=signal.ticker,
                direction=signal.direction,
                return_pct=round(return_pct, 2),
                correct=correct,
            )

        await session.commit()

    log.info("eval.done", stored=stored)
    return stored
