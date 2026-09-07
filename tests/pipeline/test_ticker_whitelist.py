from app.pipeline.ticker_whitelist import VALID_TICKERS, validate_ticker


def test_known_ticker_validates() -> None:
    assert validate_ticker("AAPL") == "AAPL"


def test_lowercase_normalizes() -> None:
    assert validate_ticker("msft") == "MSFT"


def test_whitespace_stripped() -> None:
    assert validate_ticker("  NVDA  ") == "NVDA"


def test_unknown_ticker_returns_none() -> None:
    assert validate_ticker("XYZABC") is None


def test_berkshire_b_validates() -> None:
    assert validate_ticker("BRK.B") == "BRK.B"


def test_whitelist_is_nonempty() -> None:
    assert len(VALID_TICKERS) > 400


def test_whitelist_contains_major_tickers() -> None:
    for ticker in ("AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "JPM", "JNJ"):
        assert ticker in VALID_TICKERS, f"{ticker} missing from whitelist"


def test_empty_string_returns_none() -> None:
    assert validate_ticker("") is None
