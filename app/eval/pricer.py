import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import structlog
import yfinance as yf

log = structlog.get_logger()


def _fetch_close(ticker: str, target_date: date) -> Decimal | None:
    """Return the closing price on target_date, or the next trading day if it's a holiday."""
    # Fetch a small window around the target to handle holidays/weekends
    start = target_date
    end = target_date + timedelta(days=7)
    hist = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if hist.empty:
        return None
    # Use the first row (earliest available on or after target_date)
    close = float(hist["Close"].iloc[0])
    return Decimal(str(round(close, 4)))


async def fetch_price(ticker: str, target_date: date) -> Decimal | None:
    """Async wrapper around the blocking yfinance download."""
    loop = asyncio.get_event_loop()
    try:
        price = await loop.run_in_executor(None, _fetch_close, ticker, target_date)
    except Exception:
        log.exception("pricer.fetch_failed", ticker=ticker, target_date=str(target_date))
        return None
    if price is None:
        log.warning("pricer.no_data", ticker=ticker, target_date=str(target_date))
    return price


def t5_date(t0: datetime) -> date:
    """5 calendar days after T+0 anchor — yfinance skips non-trading days automatically."""
    return (t0 + timedelta(days=5)).date()


def t5_elapsed(t0: datetime) -> bool:
    """True once T+5 has passed (with a 1-hour buffer for late market close data)."""
    cutoff = t0 + timedelta(days=5, hours=17)
    return datetime.now(UTC) >= cutoff
