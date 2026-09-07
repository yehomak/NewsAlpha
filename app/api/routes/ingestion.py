from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event
from app.db.session import get_session

log = structlog.get_logger()
router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestionStatus(BaseModel):
    event_count: int
    last_fetched_at: datetime | None
    checked_at: datetime


@router.get("/status", response_model=IngestionStatus)
async def ingestion_status(session: AsyncSession = Depends(get_session)) -> IngestionStatus:
    count_result = await session.execute(select(func.count()).select_from(Event))
    event_count: int = count_result.scalar_one()

    last_result = await session.execute(select(func.max(Event.fetched_at)))
    last_fetched_at: datetime | None = last_result.scalar_one()

    return IngestionStatus(
        event_count=event_count,
        last_fetched_at=last_fetched_at,
        checked_at=datetime.now(UTC),
    )
