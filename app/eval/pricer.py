import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import structlog
import yfinance as yf

log = structlog.get_logger()

# Cap concurrent yfinance threads to avoid throttling
_SEMAPHORE = asyncio.Semaphore(10)


def _fetch_close(ticker: str, target_date: date, backward: bool = False) -> Decimal | None:
    """Return the closing price on or nearest to target_date.

    forward (backward=False): target_date + 7-day window, take first row.
      Used for T0 and positive offsets — snaps to next trading day on holidays.
    backward (backward=True): target_date - 7-day window, take last row.
      Used for negative offsets (T-1, T-2) — snaps to prev trading day on weekends.
    """
    if backward:
        start = target_date - timedelta(days=7)
        end = target_date + timedelta(days=1)  # yfinance end is exclusive
        hist = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if hist.empty:
            return None
        close = float(hist["Close"].iloc[-1])
    else:
        start = target_date
        end = target_date + timedelta(days=7)
        hist = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if hist.empty:
            return None
        close = float(hist["Close"].iloc[0])
    return Decimal(str(round(close, 4)))


async def fetch_price(
    ticker: str, target_date: date, backward: bool = False
) -> Decimal | None:
    """Async wrapper around the blocking yfinance download."""
    async with _SEMAPHORE:
        loop = asyncio.get_event_loop()
        try:
            price = await loop.run_in_executor(
                None, _fetch_close, ticker, target_date, backward
            )
        except Exception:
            log.exception("pricer.fetch_failed", ticker=ticker, target_date=str(target_date))
            return None
    if price is None:
        log.warning("pricer.no_data", ticker=ticker, target_date=str(target_date))
    return price


def offset_date(t0: datetime, offset_days: int) -> date:
    """Calendar date at t0 + offset_days. Negative offsets go backward."""
    return (t0 + timedelta(days=offset_days)).date()


def t5_date(t0: datetime) -> date:
    return offset_date(t0, 5)


def t5_elapsed(t0: datetime) -> bool:
    """True once T+5 has passed (with a 1-hour buffer for late market close data)."""
    t0_utc = t0 if t0.tzinfo is not None else t0.replace(tzinfo=UTC)
    cutoff = t0_utc + timedelta(days=5, hours=17)
    return datetime.now(UTC) >= cutoff
