from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Direction, EventType, Signal
from app.db.session import get_session
from app.pipeline.runner import run_pipeline

router = APIRouter(prefix="/signals", tags=["signals"])


class SignalOut(BaseModel):
    id: int
    event_id: int
    ticker: str
    direction: Direction
    confidence: float
    event_type: EventType
    reasoning: str
    cost_usd: Decimal
    langfuse_trace_id: str | None
    created_at: datetime
    # eval fields — None until T+5 elapsed
    return_pct: float | None = None
    correct: bool | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_eval(cls, signal: Signal) -> "SignalOut":
        obj = cls.model_validate(signal)
        if signal.eval_result:
            obj.return_pct = signal.eval_result.return_pct
            obj.correct = signal.eval_result.correct
        return obj


class TriggerResponse(BaseModel):
    queued: bool


@router.post("/trigger", response_model=TriggerResponse, status_code=202)
async def trigger_pipeline(background_tasks: BackgroundTasks) -> TriggerResponse:
    background_tasks.add_task(run_pipeline)
    return TriggerResponse(queued=True)


@router.get("", response_model=list[SignalOut])
async def list_signals(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    ticker: str | None = Query(default=None),
    direction: Direction | None = Query(default=None),
    min_confidence: float | None = Query(default=None, ge=0.0, le=1.0),
    session: AsyncSession = Depends(get_session),
) -> list[SignalOut]:
    stmt = (
        select(Signal)
        .options(selectinload(Signal.eval_result))
        .order_by(Signal.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if ticker:
        stmt = stmt.where(Signal.ticker == ticker.upper())
    if direction:
        stmt = stmt.where(Signal.direction == direction)
    if min_confidence is not None:
        stmt = stmt.where(Signal.confidence >= min_confidence)

    result = await session.execute(stmt)
    return [SignalOut.from_orm_with_eval(s) for s in result.scalars().all()]


@router.get("/{signal_id}", response_model=SignalOut)
async def get_signal(
    signal_id: int,
    session: AsyncSession = Depends(get_session),
) -> SignalOut:
    result = await session.execute(
        select(Signal).where(Signal.id == signal_id).options(selectinload(Signal.eval_result))
    )
    signal = result.scalar_one_or_none()
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return SignalOut.from_orm_with_eval(signal)
