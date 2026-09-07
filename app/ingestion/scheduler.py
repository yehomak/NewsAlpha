import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.ingestion.pipeline import run_ingestion
from app.pipeline.runner import run_pipeline

log = structlog.get_logger()

scheduler = AsyncIOScheduler()


def configure_scheduler() -> None:
    scheduler.add_job(
        run_ingestion,
        trigger="interval",
        hours=settings.ingest_interval_hours,
        id="ingest",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=settings.pipeline_interval_minutes,
        id="pipeline",
        replace_existing=True,
        max_instances=1,
    )
    log.info(
        "scheduler.configured",
        ingest_hours=settings.ingest_interval_hours,
        pipeline_minutes=settings.pipeline_interval_minutes,
    )
