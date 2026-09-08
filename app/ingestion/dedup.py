import hashlib
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event

_SEMANTIC_DEDUP_THRESHOLD = 0.95  # cosine similarity; <=> distance < 0.05
_SEMANTIC_WINDOW_HOURS = 24


def normalize_url(url: str) -> str:
    url = re.sub(r"\?.*$", "", url)
    return url.rstrip("/").lower()


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()


def is_stale(published_at: datetime | None, max_age_days: int = 7) -> bool:
    if published_at is None:
        return False
    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    # ensure comparison is tz-aware
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    return published_at < cutoff


async def find_by_hash(session: AsyncSession, url_hash: str) -> Event | None:
    result = await session.execute(select(Event).where(Event.url_hash == url_hash))
    return result.scalar_one_or_none()


async def find_semantic_duplicate(
    session: AsyncSession,
    embedding: list[float],
) -> tuple[Event, float] | None:
    """Return (event, similarity_score) if a near-identical event exists in the last 24h."""
    cutoff = datetime.now(UTC) - timedelta(hours=_SEMANTIC_WINDOW_HOURS)
    # pgvector <=> is cosine distance (0=identical); similarity = 1 - distance
    distance_threshold = 1.0 - _SEMANTIC_DEDUP_THRESHOLD
    result = await session.execute(
        select(Event, (1.0 - Event.embedding.cosine_distance(embedding)).label("similarity"))
        .where(
            Event.embedding.is_not(None),
            Event.dedup_skipped.is_(False),
            Event.published_at >= cutoff,
            Event.embedding.cosine_distance(embedding) < distance_threshold,
        )
        .order_by(Event.embedding.cosine_distance(embedding))
        .limit(1)
    )
    row = result.first()
    if row is None:
        return None
    event, similarity = row
    return event, float(similarity)


async def find_time_domain_duplicate(
    session: AsyncSession,
    source: str,
    ticker_hints: list[str],
    window_hours: int = 4,
) -> Event | None:
    """Return an existing Event from the same source with overlapping tickers within the window."""
    if not ticker_hints:
        return None
    cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
    result = await session.execute(
        select(Event)
        .where(
            Event.source == source,
            Event.fetched_at >= cutoff,
            Event.ticker_hints.is_not(None),
        )
        .limit(20)
    )
    recent = result.scalars().all()
    hint_set = set(ticker_hints)
    for event in recent:
        if event.ticker_hints and hint_set & set(event.ticker_hints):
            return event
    return None
