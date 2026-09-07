from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.signals import router as signals_router
from app.ingestion.scheduler import configure_scheduler, scheduler
from app.logging_setup import configure_logging
from app.pipeline.langfuse_client import flush as flush_langfuse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    log = structlog.get_logger()
    log.info("startup", service="butterfly-effect")
    configure_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
    flush_langfuse()
    log.info("shutdown", service="butterfly-effect")


app = FastAPI(title="butterfly-effect", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(ingestion_router)
app.include_router(signals_router)
