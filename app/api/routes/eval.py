from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvalResult, PriceSnapshot, Signal
from app.db.session import get_session
from app.eval.analysis import (
    SignalRow,
    multi_horizon_accuracy,
    pearson_ic,
    profit_factor,
)
from app.eval.runner import run_eval

router = APIRouter(prefix="/eval", tags=["eval"])


class DirectionBreakdown(BaseModel):
    direction: str
    total: int
    correct: int
    accuracy_pct: float


class EventTypeBreakdown(BaseModel):
    event_type: str
    total: int
    correct: int
    accuracy_pct: float


class EvalSummary(BaseModel):
    evaluated: int
    pending: int
    accuracy_pct: float | None
    avg_return_pct: float | None
    avg_abnormal_return_pct: float | None
    by_direction: list[DirectionBreakdown]
    by_event_type: list[EventTypeBreakdown]
    as_of: datetime


class HorizonPointOut(BaseModel):
    offset: int
    accuracy_pct: float | None
    n: int


class AnalysisResponse(BaseModel):
    ic: float | None
    ic_n: int
    profit_factor: float | None
    horizon: list[HorizonPointOut]
    evaluated: int
    as_of: datetime


class TriggerResponse(BaseModel):
    queued: bool


@router.post("/trigger", response_model=TriggerResponse, status_code=202)
async def trigger_eval(background_tasks: BackgroundTasks) -> TriggerResponse:
    background_tasks.add_task(run_eval)
    return TriggerResponse(queued=True)


@router.get("/summary", response_model=EvalSummary)
async def eval_summary(session: AsyncSession = Depends(get_session)) -> EvalSummary:
    # Overall counts
    evaluated = await session.scalar(select(func.count()).select_from(EvalResult)) or 0
    total_signals = await session.scalar(select(func.count()).select_from(Signal)) or 0
    pending = total_signals - evaluated

    accuracy_pct: float | None = None
    avg_return_pct: float | None = None
    avg_abnormal_return_pct: float | None = None

    if evaluated > 0:
        correct_count = (
            await session.scalar(
                select(func.count()).select_from(EvalResult).where(EvalResult.correct.is_(True))
            )
            or 0
        )
        accuracy_pct = round(correct_count / evaluated * 100, 1)

        avg_return = await session.scalar(select(func.avg(EvalResult.return_pct)))
        avg_return_pct = round(float(avg_return), 2) if avg_return is not None else None

        avg_abnormal = await session.scalar(
            select(func.avg(EvalResult.abnormal_return_pct)).where(
                EvalResult.abnormal_return_pct.is_not(None)
            )
        )
        avg_abnormal_return_pct = (
            round(float(avg_abnormal), 2) if avg_abnormal is not None else None
        )

    # Breakdown by direction
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

    by_direction = [
        DirectionBreakdown(
            direction=d,
            total=v["total"],
            correct=v["correct"],
            accuracy_pct=round(v["correct"] / v["total"] * 100, 1),
        )
        for d, v in dir_map.items()
    ]

    # Breakdown by event_type
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

    by_event_type = [
        EventTypeBreakdown(
            event_type=et,
            total=v["total"],
            correct=v["correct"],
            accuracy_pct=round(v["correct"] / v["total"] * 100, 1),
        )
        for et, v in et_map.items()
    ]

    return EvalSummary(
        evaluated=evaluated,
        pending=pending,
        accuracy_pct=accuracy_pct,
        avg_return_pct=avg_return_pct,
        avg_abnormal_return_pct=avg_abnormal_return_pct,
        by_direction=by_direction,
        by_event_type=by_event_type,
        as_of=datetime.now(UTC),
    )


@router.get("/analysis", response_model=AnalysisResponse)
async def eval_analysis(session: AsyncSession = Depends(get_session)) -> AnalysisResponse:
    eval_rows = (
        await session.execute(
            select(
                Signal.id,
                Signal.direction,
                EvalResult.return_pct,
                EvalResult.correct,
                EvalResult.price_t0,
            ).join(EvalResult, EvalResult.signal_id == Signal.id)
        )
    ).all()

    if not eval_rows:
        return AnalysisResponse(
            ic=None,
            ic_n=0,
            profit_factor=None,
            horizon=[HorizonPointOut(offset=o, accuracy_pct=None, n=0) for o in range(1, 6)],
            evaluated=0,
            as_of=datetime.now(UTC),
        )

    signal_ids = [r.id for r in eval_rows]
    snap_rows = (
        await session.execute(
            select(PriceSnapshot.signal_id, PriceSnapshot.offset_days, PriceSnapshot.price)
            .where(PriceSnapshot.signal_id.in_(signal_ids))
            .where(PriceSnapshot.offset_days.in_([1, 2, 3, 4, 5]))
        )
    ).all()

    snaps: dict[int, dict[int, float]] = {}
    for snap in snap_rows:
        snaps.setdefault(snap.signal_id, {})[snap.offset_days] = float(snap.price)

    rows = [
        SignalRow(
            direction=r.direction,
            return_pct=r.return_pct,
            correct=r.correct,
            price_t0=float(r.price_t0),
            snapshots=snaps.get(r.id, {}),
        )
        for r in eval_rows
    ]

    ic, ic_n = pearson_ic(rows)
    pf = profit_factor(rows)
    horizon_pts = multi_horizon_accuracy(rows)

    return AnalysisResponse(
        ic=ic,
        ic_n=ic_n,
        profit_factor=pf,
        horizon=[
            HorizonPointOut(offset=h.offset, accuracy_pct=h.accuracy_pct, n=h.n)
            for h in horizon_pts
        ],
        evaluated=len(eval_rows),
        as_of=datetime.now(UTC),
    )
