from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    model_config = {"from_attributes": True}


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
    session: AsyncSession = Depends(get_session),
) -> list[Signal]:
    stmt = select(Signal).order_by(Signal.created_at.desc()).limit(limit).offset(offset)
    if ticker:
        stmt = stmt.where(Signal.ticker == ticker.upper())
    result = await session.execute(stmt)
    return list(result.scalars().all())
