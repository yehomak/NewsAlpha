import structlog

from app.pipeline.state import SignalState

log = structlog.get_logger()


async def handle_error(state: SignalState) -> dict:  # type: ignore[type-arg]
    log.warning(
        "pipeline.handle_error",
        event_id=state["event_id"],
        error=state.get("error"),
        ticker=state.get("ticker"),
    )
    return {}
