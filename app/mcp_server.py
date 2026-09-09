"""FastMCP server — exposes butterfly-effect pipeline data as MCP tools and resources.

Run standalone (stdio transport for Claude Desktop):
    python -m app.mcp_server

Or mount onto the FastAPI app for SSE transport:
    from app.mcp_server import mcp
    app.mount("/mcp", mcp.sse_app())
"""

from datetime import UTC, datetime, timedelta

from fastmcp import FastMCP
from sqlalchemy import case, func, select, text

from app.db.models import EvalResult, Event, Signal
from app.db.session import async_session_factory

mcp: FastMCP = FastMCP(
    "butterfly-effect",
    instructions=(
        "Financial news signal pipeline. Extracts LLM-generated directional signals "
        "(bullish/bearish/neutral) from news, then evaluates them against T+5 stock prices. "
        "Use get_pipeline_status() first to confirm the pipeline is live "
        "before interpreting signals."
    ),
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_signals(
    ticker: str | None = None,
    direction: str | None = None,
    min_confidence: float = 0.0,
    limit: int = 10,
) -> list[dict]:  # type: ignore[type-arg]
    """Retrieve recent signals from the pipeline.

    Args:
        ticker: Filter by stock ticker (e.g. "NVDA"). None returns all tickers.
        direction: Filter by direction — "bullish", "bearish", or "neutral". None returns all.
        min_confidence: Minimum confidence threshold (0.0–1.0).
        limit: Max signals to return (1–50).
    """
    limit = max(1, min(50, limit))
    async with async_session_factory() as session:
        stmt = (
            select(
                Signal.id,
                Signal.ticker,
                Signal.direction,
                Signal.confidence,
                Signal.event_type,
                Signal.reasoning,
                Signal.created_at,
                Signal.cost_usd,
                EvalResult.correct,
                EvalResult.return_pct,
            )
            .outerjoin(EvalResult, EvalResult.signal_id == Signal.id)
            .where(Signal.confidence >= min_confidence)
            .order_by(Signal.created_at.desc())
            .limit(limit)
        )
        if ticker:
            stmt = stmt.where(Signal.ticker == ticker.upper())
        if direction:
            stmt = stmt.where(Signal.direction == direction.lower())

        rows = (await session.execute(stmt)).all()

    return [
        {
            "id": row.id,
            "ticker": row.ticker,
            "direction": str(row.direction),
            "confidence": round(float(row.confidence), 3),
            "event_type": str(row.event_type),
            "reasoning": row.reasoning,
            "created_at": row.created_at.isoformat(),
            "cost_usd": float(row.cost_usd),
            "evaluated": row.correct is not None,
            "correct": row.correct,
            "return_pct": round(float(row.return_pct), 2) if row.return_pct is not None else None,
        }
        for row in rows
    ]


@mcp.tool()
async def get_ticker_accuracy(ticker: str) -> dict:  # type: ignore[type-arg]
    """Accuracy and signal stats for a single ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
    """
    ticker = ticker.upper()
    async with async_session_factory() as session:
        row = (
            await session.execute(
                select(
                    func.count(Signal.id).label("signal_count"),
                    func.avg(Signal.confidence).label("avg_confidence"),
                    func.max(Signal.created_at).label("last_signal_at"),
                    func.count(EvalResult.id).label("evaluated_count"),
                    func.coalesce(
                        func.sum(case((EvalResult.correct.is_(True), 1), else_=0)), 0
                    ).label("correct_count"),
                )
                .outerjoin(EvalResult, EvalResult.signal_id == Signal.id)
                .where(Signal.ticker == ticker)
            )
        ).one()

        last_dir_row = (
            await session.execute(
                select(Signal.direction)
                .where(Signal.ticker == ticker)
                .order_by(Signal.created_at.desc())
                .limit(1)
            )
        ).first()

    if row.signal_count == 0:
        return {"ticker": ticker, "error": "No signals found for this ticker"}

    accuracy_pct = None
    if row.evaluated_count and row.evaluated_count >= 3:
        accuracy_pct = round(int(row.correct_count) / int(row.evaluated_count) * 100, 1)

    return {
        "ticker": ticker,
        "signal_count": int(row.signal_count),
        "avg_confidence": round(float(row.avg_confidence), 3),
        "last_signal_at": row.last_signal_at.isoformat() if row.last_signal_at else None,
        "last_direction": str(last_dir_row[0]) if last_dir_row else None,
        "evaluated_count": int(row.evaluated_count),
        "correct_count": int(row.correct_count),
        "accuracy_pct": accuracy_pct,
        "note": "accuracy_pct only shown for tickers with ≥3 evaluated signals",
    }


@mcp.tool()
async def get_eval_summary() -> dict:  # type: ignore[type-arg]
    """Overall pipeline accuracy: hit rate, avg return, breakdown by direction and event type.

    First T+5 results expected after signals are 5 trading days old.
    """
    async with async_session_factory() as session:
        evaluated = int(await session.scalar(select(func.count()).select_from(EvalResult)) or 0)
        total_signals = int(await session.scalar(select(func.count()).select_from(Signal)) or 0)

        accuracy_pct = None
        avg_return_pct = None

        if evaluated > 0:
            correct_count = int(
                await session.scalar(
                    select(func.count()).select_from(EvalResult).where(EvalResult.correct.is_(True))
                )
                or 0
            )
            accuracy_pct = round(correct_count / evaluated * 100, 1)
            avg_return = await session.scalar(select(func.avg(EvalResult.return_pct)))
            avg_return_pct = round(float(avg_return), 2) if avg_return is not None else None

        dir_rows = (
            await session.execute(
                select(Signal.direction, EvalResult.correct, func.count().label("cnt"))
                .join(EvalResult, EvalResult.signal_id == Signal.id)
                .group_by(Signal.direction, EvalResult.correct)
            )
        ).all()

        dir_map: dict[str, dict[str, int]] = {}
        for direction, correct, cnt in dir_rows:
            key = str(direction)
            if key not in dir_map:
                dir_map[key] = {"total": 0, "correct": 0}
            dir_map[key]["total"] += cnt
            if correct:
                dir_map[key]["correct"] += cnt

        et_rows = (
            await session.execute(
                select(Signal.event_type, EvalResult.correct, func.count().label("cnt"))
                .join(EvalResult, EvalResult.signal_id == Signal.id)
                .group_by(Signal.event_type, EvalResult.correct)
            )
        ).all()

        et_map: dict[str, dict[str, int]] = {}
        for event_type, correct, cnt in et_rows:
            key = str(event_type)
            if key not in et_map:
                et_map[key] = {"total": 0, "correct": 0}
            et_map[key]["total"] += cnt
            if correct:
                et_map[key]["correct"] += cnt

    return {
        "evaluated": evaluated,
        "pending": total_signals - evaluated,
        "accuracy_pct": accuracy_pct,
        "avg_return_pct": avg_return_pct,
        "by_direction": [
            {
                "direction": d,
                "total": v["total"],
                "correct": v["correct"],
                "accuracy_pct": round(v["correct"] / v["total"] * 100, 1),
            }
            for d, v in dir_map.items()
        ],
        "by_event_type": [
            {
                "event_type": et,
                "total": v["total"],
                "correct": v["correct"],
                "accuracy_pct": round(v["correct"] / v["total"] * 100, 1),
            }
            for et, v in et_map.items()
        ],
        "as_of": datetime.now(UTC).isoformat(),
    }


@mcp.tool()
async def get_pipeline_status() -> dict:  # type: ignore[type-arg]
    """Current health of the pipeline: last run times, signals and events ingested today."""
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    async with async_session_factory() as session:
        last_ingest = await session.scalar(select(func.max(Event.fetched_at))) or None
        last_pipeline = await session.scalar(select(func.max(Signal.created_at))) or None
        last_eval = await session.scalar(select(func.max(EvalResult.evaluated_at))) or None
        signals_today = int(
            await session.scalar(select(func.count(Signal.id)).where(Signal.created_at >= today))
            or 0
        )
        events_today = int(
            await session.scalar(select(func.count(Event.id)).where(Event.fetched_at >= today)) or 0
        )
        total_signals = int(await session.scalar(select(func.count(Signal.id))) or 0)

    now = datetime.now(UTC)
    is_live = last_ingest is not None and (now - last_ingest) < timedelta(hours=2)

    return {
        "is_live": is_live,
        "last_ingest_at": last_ingest.isoformat() if last_ingest else None,
        "last_pipeline_at": last_pipeline.isoformat() if last_pipeline else None,
        "last_eval_at": last_eval.isoformat() if last_eval else None,
        "signals_today": signals_today,
        "events_today": events_today,
        "total_signals": total_signals,
    }


@mcp.tool()
async def get_cost_report(days: int = 30) -> dict:  # type: ignore[type-arg]
    """Pipeline cost breakdown: total spend, avg per signal, daily trend.

    Args:
        days: Lookback window in days (1–365). Default 30.
    """
    days = max(1, min(365, days))
    cutoff = datetime.now(UTC) - timedelta(days=days)

    async with async_session_factory() as session:
        total_row = (
            await session.execute(
                select(
                    func.sum(Signal.cost_usd).label("total"),
                    func.avg(Signal.cost_usd).label("avg"),
                    func.count(Signal.id).label("cnt"),
                ).where(Signal.created_at >= cutoff)
            )
        ).one()

        daily_rows = (
            await session.execute(
                select(
                    func.date_trunc(text("'day'"), Signal.created_at).label("day"),
                    func.sum(Signal.cost_usd).label("cost_usd"),
                    func.count(Signal.id).label("signal_count"),
                )
                .where(Signal.created_at >= cutoff)
                .group_by(func.date_trunc(text("'day'"), Signal.created_at))
                .order_by(func.date_trunc(text("'day'"), Signal.created_at).asc())
            )
        ).all()

    return {
        "period_days": days,
        "total_cost_usd": round(float(total_row.total or 0), 4),
        "avg_cost_per_signal": round(float(total_row.avg), 6) if total_row.avg else None,
        "signal_count": int(total_row.cnt),
        "daily": [
            {
                "date": row.day.date().isoformat(),
                "cost_usd": round(float(row.cost_usd), 4),
                "signal_count": int(row.signal_count),
            }
            for row in daily_rows
        ],
    }


# ---------------------------------------------------------------------------
# Resources — lightweight snapshots, no heavy computation
# ---------------------------------------------------------------------------


@mcp.resource("signal://{ticker}/latest")
async def latest_signal_resource(ticker: str) -> str:
    """Latest signal for a ticker as a formatted text summary."""
    ticker = ticker.upper()
    async with async_session_factory() as session:
        row = (
            await session.execute(
                select(Signal)
                .where(Signal.ticker == ticker)
                .order_by(Signal.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    if row is None:
        return f"No signals found for {ticker}."

    age = datetime.now(UTC) - row.created_at
    hours_ago = int(age.total_seconds() / 3600)

    return (
        f"{ticker} — {str(row.direction).upper()} "
        f"(confidence: {row.confidence:.0%}, event: {row.event_type})\n"
        f"Generated {hours_ago}h ago\n\n"
        f"Reasoning: {row.reasoning}"
    )


@mcp.resource("eval://summary")
async def eval_summary_resource() -> str:
    """Current eval accuracy snapshot as plain text."""
    async with async_session_factory() as session:
        evaluated = int(await session.scalar(select(func.count()).select_from(EvalResult)) or 0)
        total = int(await session.scalar(select(func.count()).select_from(Signal)) or 0)

        if evaluated == 0:
            return (
                f"No evaluated signals yet. {total} signals pending T+5 evaluation.\n"
                "First results expected after 5 trading days from first signal."
            )

        correct = int(
            await session.scalar(
                select(func.count()).select_from(EvalResult).where(EvalResult.correct.is_(True))
            )
            or 0
        )
        accuracy = round(correct / evaluated * 100, 1)
        avg_return = await session.scalar(select(func.avg(EvalResult.return_pct)))

    return (
        f"Directional accuracy: {accuracy}% ({correct}/{evaluated} correct)\n"
        f"Avg T+5 return on correct signals: "
        f"{round(float(avg_return), 2)}%\n"
        if avg_return
        else f"Pending evaluation: {total - evaluated} signals"
    )


@mcp.resource("pipeline://status")
async def pipeline_status_resource() -> str:
    """Pipeline health snapshot as plain text."""
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    async with async_session_factory() as session:
        last_ingest = await session.scalar(select(func.max(Event.fetched_at)))
        signals_today = int(
            await session.scalar(select(func.count(Signal.id)).where(Signal.created_at >= today))
            or 0
        )
        events_today = int(
            await session.scalar(select(func.count(Event.id)).where(Event.fetched_at >= today)) or 0
        )

    if last_ingest is None:
        return "Pipeline has not run yet."

    now = datetime.now(UTC)
    minutes_ago = int((now - last_ingest).total_seconds() / 60)
    status = "LIVE" if minutes_ago < 120 else "STALE"

    return (
        f"Status: {status}\n"
        f"Last ingest: {minutes_ago}m ago\n"
        f"Signals today: {signals_today}\n"
        f"Events today: {events_today}"
    )


if __name__ == "__main__":
    mcp.run()
