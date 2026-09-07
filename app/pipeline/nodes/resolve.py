import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from app.config import settings
from app.pipeline.costs import compute_cost
from app.pipeline.langfuse_client import get_langfuse
from app.pipeline.state import SignalState
from app.pipeline.ticker_whitelist import validate_ticker
from app.pipeline.universe import SIGNAL_UNIVERSE_SET

log = structlog.get_logger()

_HAIKU = "claude-haiku-4-5-20251001"


class TickerProposal(BaseModel):
    ticker: str
    reasoning: str


async def resolve_tickers(state: SignalState) -> dict:  # type: ignore[type-arg]
    # Fast path: if ingestion already gave us a validated universe hint, use it
    for hint in state.get("ticker_hints", []):
        normalized = hint.strip().upper()
        if normalized in SIGNAL_UNIVERSE_SET:
            log.info("resolve_tickers.hint_hit", ticker=normalized, event_id=state["event_id"])
            return {"ticker": normalized}

    companies = state.get("companies", [])
    if not companies:
        return {"ticker": None, "error": "no companies extracted"}

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    lf = get_langfuse()

    company_list = ", ".join(companies[:5])
    gen = None
    if lf:
        gen = lf.generation(
            name="resolve_tickers",
            model=_HAIKU,
            trace_id=state.get("langfuse_trace_id"),
            input={"companies": company_list},
        )

    try:
        response = await client.messages.create(
            model=_HAIKU,
            max_tokens=128,
            tools=[
                {
                    "name": "output",
                    "description": "The single most relevant stock ticker for the primary company.",
                    "input_schema": TickerProposal.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": "output"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Given these companies mentioned in a financial news headline: "
                        f"{company_list}\n\n"
                        "Return the US stock ticker symbol for the PRIMARY company "
                        "this news is about. "
                        "Use standard NYSE/NASDAQ format (e.g. AAPL, MSFT). "
                        f"Headline: {state['headline']}"
                    ),
                }
            ],
        )
    except Exception as exc:
        log.exception("resolve_tickers.api_error", event_id=state["event_id"])
        if gen:
            gen.end(level="ERROR", status_message=str(exc))
        return {"ticker": None, "error": f"resolve_tickers failed: {exc}"}

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    cost = compute_cost(response.usage, _HAIKU)

    if not tool_block:
        if gen:
            gen.end(level="WARNING", status_message="no tool_use block")
        return {"ticker": None, "total_cost_usd": float(state["total_cost_usd"] + float(cost))}

    proposal = TickerProposal.model_validate(tool_block.input)
    in_whitelist = validate_ticker(proposal.ticker)
    validated = in_whitelist if (in_whitelist and in_whitelist in SIGNAL_UNIVERSE_SET) else None

    if gen:
        gen.end(
            output={"proposed": proposal.ticker, "validated": validated},
            usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
        )

    if validated is None:
        log.warning(
            "resolve_tickers.out_of_universe",
            proposed=proposal.ticker,
            event_id=state["event_id"],
        )
        return {
            "ticker": None,
            "total_cost_usd": float(state["total_cost_usd"] + float(cost)),
            "error": f"ticker '{proposal.ticker}' not in signal universe",
        }

    log.info("resolve_tickers.done", ticker=validated, event_id=state["event_id"])
    return {
        "ticker": validated,
        "total_cost_usd": float(state["total_cost_usd"] + float(cost)),
    }
