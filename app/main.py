from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.logging_setup import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    log = structlog.get_logger()
    log.info("startup", service="butterfly-effect")
    yield
    log.info("shutdown", service="butterfly-effect")


app = FastAPI(title="butterfly-effect", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
