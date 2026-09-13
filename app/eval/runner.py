import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Direction, EvalResult, PriceSnapshot, Signal
from app.db.session import async_session_factory
from app.eval.pricer import fetch_price, offset_date, t5_elapsed
from app.pipeline.market_hours import t0_anchor

log = structlog.get_logger()

# Full price curve: T-2, T-1, T0, T+1, T+2, T+3, T+4, T+5
_OFFSETS = [-2, -1, 0, 1, 2, 3, 4, 5]

# Neutral signal correct when |return| within this band
_NEUTRAL_BAND_PCT = 1.0


def _is_correct(direction: Direction, return_pct: float) -> bool:
    if direction == Direction.BULLISH:
        return return_pct > 0
    if direction == Direction.BEARISH:
        return return_pct < 0
    return abs(return_pct) <= _NEUTRAL_BAND_PCT


def _t5_cutoff() -> datetime:
    """SQL-side cutoff: signals whose T+5+17h has elapsed."""
    return datetime.now(UTC) - timedelta(days=5, hours=17)


async def _fetch_uneval(session: Any) -> list[Signal]:
    # Push eligibility filter to SQL — only load signals where published_at is old enough.
    # Falls back to created_at when published_at is null (conservative: uses the later time).
    cutoff = _t5_cutoff()
    result = await session.execute(
        select(Signal)
        .outerjoin(EvalResult, EvalResult.signal_id == Signal.id)
        .where(EvalResult.id.is_(None))
        .where(Signal.created_at <= cutoff)
        .options(selectinload(Signal.event))
        .limit(500)
    )
    return result.scalars().all()  # type: ignore[no-any-return]


async def _existing_offsets(session: Any, signal_id: int) -> set[int]:
    """Return the set of offset_days already stored for this signal."""
    rows = await session.execute(
        select(PriceSnapshot.offset_days).where(PriceSnapshot.signal_id == signal_id)
    )
    return {row[0] for row in rows.all()}


async def _fetch_all_prices(ticker: str, t0: datetime) -> dict[int, Decimal | None]:
    """Fetch all 8 offsets concurrently."""
    tasks = {
        offset: fetch_price(
            ticker,
            offset_date(t0, offset),
            backward=(offset < 0),
        )
        for offset in _OFFSETS
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    return {
        offset: (None if isinstance(price, BaseException) else price)
        for offset, price in zip(tasks.keys(), results, strict=True)
    }


async def _eval_signal(signal: Signal) -> bool:
    """Evaluate one signal. Returns True if an EvalResult was stored."""
    t0 = t0_anchor(
        signal.event.published_at if signal.event else None,
        signal.created_at,
    )
    if not t5_elapsed(t0):
        return False

    prices = await _fetch_all_prices(signal.ticker, t0)

    price_t0 = prices.get(0)
    price_t5 = prices.get(5)

    if price_t0 is None or price_t5 is None:
        log.warning(
            "eval.price_missing",
            signal_id=signal.id,
            ticker=signal.ticker,
            price_t0=str(price_t0),
            price_t5=str(price_t5),
        )
        return False

    return_pct = float((price_t5 - price_t0) / price_t0 * Decimal("100"))

    # Abnormal return: T0→T5 minus the T-2→T0 pre-event drift (None if baseline missing)
    price_tm2 = prices.get(-2)
    abnormal_return_pct: float | None = None
    if price_tm2 is not None and price_tm2 != 0:
        pre_drift = float((price_t0 - price_tm2) / price_tm2 * Decimal("100"))
        abnormal_return_pct = return_pct - pre_drift

    correct = _is_correct(signal.direction, return_pct)

    async with async_session_factory() as session:
        async with session.begin():
            # Guard: skip if already evaluated (race condition on restart)
            existing = await session.scalar(
                select(EvalResult.id).where(EvalResult.signal_id == signal.id)
            )
            if existing is not None:
                return False

            existing_offsets = await _existing_offsets(session, signal.id)

            for offset, price in prices.items():
                if price is not None and offset not in existing_offsets:
                    session.add(
                        PriceSnapshot(
                            signal_id=signal.id,
                            ticker=signal.ticker,
                            price=price,
                            fetched_at=datetime.now(UTC),
                            offset_days=offset,
                        )
                    )

            session.add(
                EvalResult(
                    signal_id=signal.id,
                    price_t0=price_t0,
                    price_t5=price_t5,
                    return_pct=return_pct,
                    abnormal_return_pct=abnormal_return_pct,
                    correct=correct,
                )
            )

    log.info(
        "eval.result",
        signal_id=signal.id,
        ticker=signal.ticker,
        direction=signal.direction,
        return_pct=round(return_pct, 2),
        abnormal_return_pct=(
            round(abnormal_return_pct, 2) if abnormal_return_pct is not None else None
        ),
        correct=correct,
    )
    return True


async def run_eval() -> int:
    """Evaluate all eligible signals. Returns count of new eval_results."""
    async with async_session_factory() as session:
        signals = await _fetch_uneval(session)

    log.info("eval.candidates", count=len(signals))
    stored = 0
    for signal in signals:
        try:
            if await _eval_signal(signal):
                stored += 1
        except Exception:
            log.exception("eval.signal_error", signal_id=signal.id)

    log.info("eval.done", stored=stored)
    return stored
