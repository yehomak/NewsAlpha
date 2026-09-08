import asyncio
from datetime import UTC, datetime, timedelta

import structlog
from alpaca.data.historical import NewsClient
from alpaca.data.models import NewsSet
from alpaca.data.requests import NewsRequest

from app.ingestion.base import RawArticle
from app.pipeline.universe import SIGNAL_UNIVERSE

log = structlog.get_logger()


class AlpacaSource:
    name = "alpaca"

    def __init__(self, api_key: str, secret_key: str) -> None:
        self._client = NewsClient(api_key=api_key, secret_key=secret_key)

    async def fetch(self, limit: int = 200) -> list[RawArticle]:
        start = datetime.now(UTC) - timedelta(days=7)
        symbols_filter = ",".join(SIGNAL_UNIVERSE)
        request = NewsRequest(symbols=symbols_filter, start=start, limit=limit, sort="desc")
        loop = asyncio.get_event_loop()
        try:
            news_set = await loop.run_in_executor(None, lambda: self._client.get_news(request))
        except Exception:
            log.exception("alpaca.fetch_failed")
            return []

        if not isinstance(news_set, NewsSet):
            log.warning("alpaca.unexpected_response_type", type=type(news_set).__name__)
            return []

        articles: list[RawArticle] = []
        for item in news_set.data.get("news", []):
            if not item.url:
                continue
            body: str | None = item.content or item.summary or None
            articles.append(
                RawArticle(
                    url=item.url,
                    title=item.headline,
                    body=body,
                    source=f"alpaca/{item.source}",
                    published_at=item.created_at,
                    ticker_hints=list(item.symbols),
                )
            )

        log.info("alpaca.fetched", count=len(articles))
        return articles
