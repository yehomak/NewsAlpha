import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.ingestion.pipeline import run_ingestion

log = structlog.get_logger()

scheduler = AsyncIOScheduler()


def configure_scheduler() -> None:
    scheduler.add_job(
        run_ingestion,
        trigger="interval",
        hours=settings.ingest_interval_hours,
        id="ingest",
        replace_existing=True,
        max_instances=1,  # prevent overlap if a run takes longer than the interval
    )
    log.info("scheduler.configured", interval_hours=settings.ingest_interval_hours)
