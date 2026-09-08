from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvalResult, Signal
from app.db.session import get_session
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
    by_direction: list[DirectionBreakdown]
    by_event_type: list[EventTypeBreakdown]
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
        by_direction=by_direction,
        by_event_type=by_event_type,
        as_of=datetime.utcnow(),
    )
