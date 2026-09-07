from datetime import UTC, datetime, timedelta

from app.ingestion.dedup import compute_url_hash, is_stale, normalize_url


def test_normalize_url_strips_query_string() -> None:
    assert normalize_url("https://example.com/article?ref=twitter") == "https://example.com/article"


def test_normalize_url_strips_trailing_slash() -> None:
    assert normalize_url("https://example.com/article/") == "https://example.com/article"


def test_normalize_url_lowercases() -> None:
    assert normalize_url("https://Example.COM/Article") == "https://example.com/article"


def test_normalize_url_strips_query_before_slash() -> None:
    url = "https://finance.yahoo.com/news/item?utm_source=rss/"
    assert normalize_url(url) == "https://finance.yahoo.com/news/item"


def test_compute_url_hash_is_deterministic() -> None:
    url = "https://example.com/article"
    assert compute_url_hash(url) == compute_url_hash(url)


def test_compute_url_hash_normalizes_before_hashing() -> None:
    assert compute_url_hash("https://Example.com/article?ref=rss") == compute_url_hash(
        "https://example.com/article"
    )


def test_compute_url_hash_length() -> None:
    assert len(compute_url_hash("https://example.com/a")) == 64


def test_is_stale_old_article() -> None:
    old = datetime.now(UTC) - timedelta(days=8)
    assert is_stale(old, max_age_days=7) is True


def test_is_stale_recent_article() -> None:
    recent = datetime.now(UTC) - timedelta(days=3)
    assert is_stale(recent, max_age_days=7) is False


def test_is_stale_none_published_at() -> None:
    assert is_stale(None, max_age_days=7) is False


def test_is_stale_naive_datetime_treated_as_utc() -> None:
    naive_old = datetime.now() - timedelta(days=10)
    assert is_stale(naive_old, max_age_days=7) is True
