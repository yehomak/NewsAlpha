import asyncio

import trafilatura
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=False,
)
def _fetch_body_sync(url: str) -> str | None:
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return None
    return trafilatura.extract(downloaded)


async def fetch_body(url: str) -> str | None:
    """Fetch full article body from URL. Returns None on failure — callers fall back to summary."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _fetch_body_sync, url)
    except Exception:
        return None
