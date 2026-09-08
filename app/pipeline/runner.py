from datetime import UTC, datetime, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Direction, Event, EventType, Signal
from app.db.session import async_session_factory
from app.pipeline.graph import graph
from app.pipeline.langfuse_client import get_langfuse
from app.pipeline.state import SignalState

log = structlog.get_logger()

_TRUNCATION_MARKERS = (
    "cuts off mid-sentence",
    "article cuts off",
    "text cuts off",
    "is incomplete",
    "appears to be cut",
    "truncated",
)


def _reasoning_flags_truncation(reasoning: str) -> bool:
    lower = reasoning.lower()
    return any(marker in lower for marker in _TRUNCATION_MARKERS)


async def _fetch_unprocessed(session: AsyncSession, limit: int) -> list[Event]:
    cutoff = datetime.now(UTC) - timedelta(days=settings.ingest_max_age_days)
    result = await session.execute(
        select(Event)
        .where(Event.processed.is_(False))
        .where(Event.fetched_at >= cutoff)
        .order_by(Event.fetched_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def _run_event(event: Event) -> tuple[Signal | None, float]:
    lf = get_langfuse()
    trace_id: str | None = None

    if lf:
        trace = lf.trace(
            name="signal-generation",
            input={"event_id": event.id, "headline": event.title},
        )
        trace_id = trace.id

    initial: SignalState = {
        "event_id": event.id,
        "headline": event.title,
        "body": event.body,
        "ticker_hints": list(event.ticker_hints or []),
        "companies": [],
        "ticker": None,
        "signal": None,
        "error": None,
        "total_cost_usd": 0.0,
        "langfuse_trace_id": trace_id,
    }

    result: SignalState = await graph.ainvoke(initial)

    if lf and trace_id:
        lf.trace(
            id=trace_id,
            output={"signal": result.get("signal"), "error": result.get("error")},
        )

    signal_data = result.get("signal")
    total_cost = result.get("total_cost_usd", 0.0)

    if signal_data is None:
        return None, total_cost

    if _reasoning_flags_truncation(signal_data["reasoning"]):
        log.warning(
            "pipeline.truncated_article",
            event_id=event.id,
            ticker=signal_data.get("ticker"),
        )
        return None, total_cost

    orm_signal = Signal(
        event_id=event.id,
        ticker=signal_data["ticker"],
        direction=Direction(signal_data["direction"].lower()),
        confidence=signal_data["confidence"],
        reasoning=signal_data["reasoning"],
        event_type=EventType(signal_data["event_type"].lower()),
        cost_usd=Decimal(str(round(total_cost, 6))),
        langfuse_trace_id=trace_id,
    )
    return orm_signal, total_cost


async def run_pipeline() -> int:
    """Process a batch of unprocessed events. Returns count of signals stored."""
    stored = 0
    async with async_session_factory() as session:
        events = await _fetch_unprocessed(session, settings.pipeline_batch_size)
        if not events:
            log.info("pipeline.no_events")
            return 0

        for event in events:
            event.processed = True  # mark first — committed even if signal insert fails
            try:
                signal, cost = await _run_event(event)
                if signal:
                    async with session.begin_nested():  # savepoint per signal insert
                        session.add(signal)
                    stored += 1
                    log.info(
                        "pipeline.signal_stored",
                        event_id=event.id,
                        ticker=signal.ticker,
                        direction=signal.direction,
                        cost_usd=float(signal.cost_usd),
                    )
                else:
                    log.info("pipeline.no_signal", event_id=event.id, cost_usd=round(cost, 6))
            except Exception:
                log.exception("pipeline.event_failed", event_id=event.id)

        await session.commit()  # commits processed=True for all events

    log.info("pipeline.run_complete", stored=stored, processed=len(events))
    return stored
