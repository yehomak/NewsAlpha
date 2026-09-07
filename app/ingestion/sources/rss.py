import asyncio
from datetime import UTC, datetime

import feedparser
import structlog

from app.ingestion.base import RawArticle

log = structlog.get_logger()

FEEDS: dict[str, str] = {
    "yahoo_finance": "https://finance.yahoo.com/news/rss",
    "cnbc_markets": (
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"
    ),
    "pr_newswire": "https://www.prnewswire.com/rss/news-releases-list.rss",
    "globenewswire": "https://www.globenewswire.com/RssFeed/subjectcode/17-Mergers%20%26%20Acquisitions",
}

# Per-feed ETag/Modified state for conditional GET (in-memory; resets on restart)
_feed_state: dict[str, dict[str, str]] = {}


def _parse_feed(name: str, url: str) -> list[RawArticle]:
    state = _feed_state.get(name, {})
    parsed = feedparser.parse(
        url,
        etag=state.get("etag"),
        modified=state.get("modified"),
    )

    # persist conditional GET tokens for next poll
    new_state: dict[str, str] = {}
    if hasattr(parsed, "etag"):
        new_state["etag"] = parsed.etag
    if hasattr(parsed, "modified"):
        new_state["modified"] = parsed.modified
    if new_state:
        _feed_state[name] = new_state

    # 304 Not Modified — nothing new
    if getattr(parsed, "status", 200) == 304:
        return []

    articles: list[RawArticle] = []
    for entry in parsed.entries:
        url_str: str = entry.get("link", "")
        if not url_str:
            continue

        title: str = entry.get("title", "")
        body: str | None = entry.get("summary") or None

        published_at: datetime | None = None
        if entry.get("published_parsed"):
            pt = entry.published_parsed
            published_at = datetime(pt[0], pt[1], pt[2], pt[3], pt[4], pt[5], tzinfo=UTC)

        articles.append(
            RawArticle(
                url=url_str,
                title=title,
                body=body,
                source=f"rss/{name}",
                published_at=published_at,
                ticker_hints=[],  # RSS feeds don't pre-resolve tickers
            )
        )

    return articles


class RssSource:
    name = "rss"

    def __init__(self, feeds: dict[str, str] | None = None) -> None:
        self._feeds = feeds or FEEDS

    async def fetch(self) -> list[RawArticle]:
        loop = asyncio.get_event_loop()
        all_articles: list[RawArticle] = []
        for feed_name, feed_url in self._feeds.items():
            try:
                articles = await loop.run_in_executor(None, _parse_feed, feed_name, feed_url)
                all_articles.extend(articles)
                log.info("rss.fetched", feed=feed_name, count=len(articles))
            except Exception:
                log.exception("rss.fetch_failed", feed=feed_name)
        return all_articles
