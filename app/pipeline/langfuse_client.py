from typing import Any

from langfuse import Langfuse

from app.config import settings

_client: Langfuse | None = None


def get_langfuse() -> Any:
    """Returns a Langfuse client if credentials are configured, else None.

    Typed as Any so callers can use the full SDK API (trace, generation, etc.)
    without fighting incomplete stubs.
    """
    global _client
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    if _client is None:
        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    return _client


def flush() -> None:
    if _client is not None:
        _client.flush()
