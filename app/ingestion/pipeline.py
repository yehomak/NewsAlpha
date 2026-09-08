import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Event
from app.db.session import async_session_factory
from app.ingestion.base import NewsSource, RawArticle
from app.ingestion.dedup import (
    compute_url_hash,
    find_by_hash,
    find_semantic_duplicate,
    find_time_domain_duplicate,
    is_stale,
)
from app.ingestion.embedder import embed_text
from app.ingestion.fetcher import fetch_body
from app.ingestion.sources.alpaca import AlpacaSource
from app.ingestion.sources.rss import RssSource

_MIN_BODY_LEN = 200  # chars below which we attempt a full trafilatura fetch

log = structlog.get_logger()


def _get_sources() -> list[NewsSource]:
    sources: list[NewsSource] = [RssSource()]
    if settings.alpaca_key and settings.alpaca_secret:
        sources.insert(0, AlpacaSource(settings.alpaca_key, settings.alpaca_secret))
    else:
        log.warning("ingestion.alpaca_disabled", reason="ALPACA_KEY or ALPACA_SECRET not set")
    return sources


async def _store_article(session: AsyncSession, article: RawArticle) -> bool:
    """Attempt to store an article. Returns True if stored, False if skipped."""
    if is_stale(article.published_at, settings.ingest_max_age_days):
        return False

    url_hash = compute_url_hash(article.url)

    if await find_by_hash(session, url_hash):
        return False

    dupe = await find_time_domain_duplicate(session, article.source, article.ticker_hints)
    if dupe:
        dupe.coverage_count += 1
        return False

    body = article.body
    if not body or len(body) < _MIN_BODY_LEN:
        fetched = await fetch_body(article.url)
        if fetched:
            body = fetched

    embedding = await embed_text(article.title)
    semantic_match = await find_semantic_duplicate(session, embedding)

    if semantic_match:
        matched_event, score = semantic_match
        log.info(
            "ingestion.semantic_duplicate",
            url=article.url,
            matched_event_id=matched_event.id,
            similarity=round(score, 4),
        )
        session.add(
            Event(
                url=article.url,
                title=article.title,
                body=body,
                source=article.source,
                published_at=article.published_at,
                url_hash=url_hash,
                ticker_hints=article.ticker_hints or None,
                coverage_count=1,
                embedding=embedding,
                processed=True,  # skip LLM pipeline — dedup_skipped explains why
                dedup_skipped=True,
                similar_to_id=matched_event.id,
                similarity_score=score,
            )
        )
        return False

    event = Event(
        url=article.url,
        title=article.title,
        body=body,
        source=article.source,
        published_at=article.published_at,
        url_hash=url_hash,
        ticker_hints=article.ticker_hints or None,
        coverage_count=1,
        embedding=embedding,
    )
    session.add(event)
    return True


async def ingest_from_source(source: NewsSource, session: AsyncSession) -> int:
    articles = await source.fetch()
    stored = 0
    for article in articles:
        if await _store_article(session, article):
            stored += 1
    await session.commit()
    log.info("ingestion.complete", source=source.name, stored=stored, fetched=len(articles))
    return stored


async def run_ingestion() -> int:
    total = 0
    async with async_session_factory() as session:
        for source in _get_sources():
            try:
                total += await ingest_from_source(source, session)
            except Exception:
                log.exception("ingestion.source_failed", source=source.name)
    log.info("ingestion.run_complete", total_stored=total)
    return total
