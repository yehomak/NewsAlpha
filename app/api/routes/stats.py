from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

import app.ingestion.pipeline as ingestion_pipeline
from app.db.models import EvalResult, Event, ExtractionAttempt, Signal
from app.db.session import get_session

# LLM spend from rejected/truncated calls before extraction_attempts existed (Sep 7-11).
# Derived from Anthropic API export ($3.57 total) minus tracked signals.cost_usd ($1.794).
_UNTRACKED_HISTORICAL_USD = 1.776

router = APIRouter(prefix="/stats", tags=["stats"])


class TickerStats(BaseModel):
    ticker: str
    signal_count: int
    avg_confidence: float
    last_signal_at: datetime
    last_direction: str
    evaluated_count: int
    correct_count: int
    accuracy_pct: float | None


class SourceBreakdown(BaseModel):
    source: str
    count: int


class EventStats(BaseModel):
    total: int
    processed: int
    unprocessed: int
    dedup_skipped: int
    by_source: list[SourceBreakdown]


class CostDay(BaseModel):
    date: date
    cost_usd: float
    signal_count: int


class CostStats(BaseModel):
    total_cost_usd: float
    avg_cost_per_signal: float | None
    signal_count: int
    by_day: list[CostDay]


class PipelineStats(BaseModel):
    last_ingest_run_at: datetime | None  # job execution time (in-memory, resets on restart)
    last_ingest_at: datetime | None  # when the last unique event was stored
    last_pipeline_at: datetime | None
    last_eval_at: datetime | None
    signals_today: int
    events_today: int
    events_without_signal: int


@router.get("/tickers", response_model=list[TickerStats])
async def ticker_stats(session: AsyncSession = Depends(get_session)) -> list[TickerStats]:
    agg_rows = (
        await session.execute(
            select(
                Signal.ticker,
                func.count(Signal.id).label("signal_count"),
                func.avg(Signal.confidence).label("avg_confidence"),
                func.max(Signal.created_at).label("last_signal_at"),
                func.count(EvalResult.id).label("evaluated_count"),
                func.coalesce(func.sum(case((EvalResult.correct.is_(True), 1), else_=0)), 0).label(
                    "correct_count"
                ),
            )
            .outerjoin(EvalResult, EvalResult.signal_id == Signal.id)
            .group_by(Signal.ticker)
            .order_by(func.count(Signal.id).desc())
        )
    ).all()

    # Last direction per ticker via window function — avoids N+1 queries
    inner = select(
        Signal.ticker,
        Signal.direction,
        func.row_number()
        .over(partition_by=Signal.ticker, order_by=Signal.created_at.desc())
        .label("rn"),
    ).subquery()

    last_dir_map: dict[str, str] = {
        row.ticker: str(row.direction)
        for row in (
            await session.execute(select(inner.c.ticker, inner.c.direction).where(inner.c.rn == 1))
        ).all()
    }

    result: list[TickerStats] = []
    for row in agg_rows:
        evaluated = int(row.evaluated_count or 0)
        correct = int(row.correct_count or 0)
        result.append(
            TickerStats(
                ticker=row.ticker,
                signal_count=int(row.signal_count),
                avg_confidence=round(float(row.avg_confidence or 0), 3),
                last_signal_at=row.last_signal_at,
                last_direction=last_dir_map.get(row.ticker, "unknown"),
                evaluated_count=evaluated,
                correct_count=correct,
                accuracy_pct=round(correct / evaluated * 100, 1) if evaluated > 0 else None,
            )
        )
    return result


@router.get("/events", response_model=EventStats)
async def event_stats(session: AsyncSession = Depends(get_session)) -> EventStats:
    total = int(await session.scalar(select(func.count()).select_from(Event)) or 0)
    processed = int(
        await session.scalar(
            select(func.count()).select_from(Event).where(Event.processed.is_(True))
        )
        or 0
    )
    dedup_skipped = int(
        await session.scalar(
            select(func.count()).select_from(Event).where(Event.dedup_skipped.is_(True))
        )
        or 0
    )

    source_rows = (
        await session.execute(
            select(Event.source, func.count(Event.id).label("cnt"))
            .group_by(Event.source)
            .order_by(func.count(Event.id).desc())
        )
    ).all()

    return EventStats(
        total=total,
        processed=processed,
        unprocessed=total - processed,
        dedup_skipped=dedup_skipped,
        by_source=[
            SourceBreakdown(source=str(row.source), count=int(row.cnt)) for row in source_rows
        ],
    )


@router.get("/costs", response_model=CostStats)
async def cost_stats(
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> CostStats:
    # Cost source strategy: extraction_attempts (Sep 11+) captures full spend including
    # rejections. For historical days before the table existed, fall back to signals.cost_usd.
    # Per-day: prefer attempts rows; fill missing days from signals.
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Days that have extraction_attempts data
    attempt_rows = (
        await session.execute(
            select(
                func.date_trunc(text("'day'"), ExtractionAttempt.created_at).label("day"),
                func.sum(ExtractionAttempt.cost_usd).label("cost_usd"),
            )
            .where(ExtractionAttempt.created_at >= cutoff)
            .group_by(func.date_trunc(text("'day'"), ExtractionAttempt.created_at))
        )
    ).all()
    attempt_days: set[date] = {row.day.date() for row in attempt_rows}

    # Historical days only (signals table, excluding days already covered by attempts)
    signal_rows = (
        await session.execute(
            select(
                func.date_trunc(text("'day'"), Signal.created_at).label("day"),
                func.sum(Signal.cost_usd).label("cost_usd"),
                func.count(Signal.id).label("signal_count"),
            )
            .where(Signal.created_at >= cutoff)
            .group_by(func.date_trunc(text("'day'"), Signal.created_at))
        )
    ).all()

    sig_by_day: dict[date, tuple[float, int]] = {
        row.day.date(): (float(row.cost_usd), int(row.signal_count)) for row in signal_rows
    }

    # Merge: attempts days take priority; historical days fill the gaps
    by_day_merged: dict[date, tuple[float, int]] = {}
    for row in attempt_rows:
        d = row.day.date()
        sig_count = sig_by_day.get(d, (0, 0))[1]
        by_day_merged[d] = (float(row.cost_usd), sig_count)
    for d, (cost, count) in sig_by_day.items():
        if d not in attempt_days:
            by_day_merged[d] = (cost, count)

    total_cost = sum(c for c, _ in by_day_merged.values()) + _UNTRACKED_HISTORICAL_USD
    signal_count = int(await session.scalar(select(func.count()).select_from(Signal)) or 0)
    avg_cost = round(total_cost / signal_count, 6) if signal_count > 0 else None

    return CostStats(
        total_cost_usd=round(total_cost, 6),
        avg_cost_per_signal=avg_cost,
        signal_count=signal_count,
        by_day=[
            CostDay(date=d, cost_usd=round(cost, 6), signal_count=count)
            for d, (cost, count) in sorted(by_day_merged.items())
        ],
    )


@router.get("/pipeline", response_model=PipelineStats)
async def pipeline_stats(session: AsyncSession = Depends(get_session)) -> PipelineStats:
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    last_ingest = await session.scalar(select(func.max(Event.fetched_at)))
    last_pipeline = await session.scalar(select(func.max(Signal.created_at)))
    last_eval = await session.scalar(select(func.max(EvalResult.evaluated_at)))

    signals_today = int(
        await session.scalar(
            select(func.count()).select_from(Signal).where(Signal.created_at >= today_start)
        )
        or 0
    )
    events_today = int(
        await session.scalar(
            select(func.count()).select_from(Event).where(Event.fetched_at >= today_start)
        )
        or 0
    )

    # Processed events that produced no signal (truncated, extraction failed, out-of-universe)
    events_without_signal = int(
        await session.scalar(
            select(func.count(Event.id))
            .outerjoin(Signal, Signal.event_id == Event.id)
            .where(Event.processed.is_(True))
            .where(Event.dedup_skipped.is_(False))
            .where(Signal.id.is_(None))
        )
        or 0
    )

    return PipelineStats(
        last_ingest_run_at=ingestion_pipeline.last_run_at,
        last_ingest_at=last_ingest,
        last_pipeline_at=last_pipeline,
        last_eval_at=last_eval,
        signals_today=signals_today,
        events_today=events_today,
        events_without_signal=events_without_signal,
    )
