import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from app.config import settings
from app.db.models import Direction, EventType
from app.pipeline.costs import compute_cost
from app.pipeline.langfuse_client import get_langfuse
from app.pipeline.state import SignalData, SignalState

log = structlog.get_logger()

_MODEL = "claude-haiku-4-5-20251001"


class SignalOutput(BaseModel):
    direction: Direction
    confidence: float = Field(ge=0.0, le=1.0)
    event_type: EventType
    reasoning: str


async def generate_signal(state: SignalState) -> dict:  # type: ignore[type-arg]
    ticker = state["ticker"]
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    lf = get_langfuse()

    body_snippet = (state["body"] or "")[:2000]
    gen = None
    if lf:
        gen = lf.generation(
            name="generate_signal",
            model=_MODEL,
            trace_id=state.get("langfuse_trace_id"),
            input={"ticker": ticker, "headline": state["headline"]},
        )

    try:
        response = await client.messages.create(
            model=_MODEL,
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": (
                        "You are a quantitative financial analyst. "
                        "Analyze news articles and determine "
                        "their likely short-term impact on the mentioned stock's price direction. "
                        "Be objective and evidence-based. "
                        "Confidence should reflect genuine uncertainty."
                    ),
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[
                {
                    "name": "output",
                    "description": (
                        "Short-term directional signal for the stock based on this news."
                    ),
                    "input_schema": SignalOutput.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": "output"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Analyze this news about {ticker} and generate a signal.\n\n"
                        f"Headline: {state['headline']}\n\n"
                        f"Article:\n{body_snippet}"
                    ),
                }
            ],
        )
    except Exception as exc:
        log.exception("generate_signal.api_error", event_id=state["event_id"])
        if gen:
            gen.end(level="ERROR", status_message=str(exc))
        return {"signal": None, "error": f"generate_signal failed: {exc}"}

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    cost = compute_cost(response.usage, _MODEL)

    if not tool_block:
        if gen:
            gen.end(level="WARNING", status_message="no tool_use block")
        return {
            "signal": None,
            "total_cost_usd": float(state["total_cost_usd"] + float(cost)),
            "error": "generate_signal returned no tool_use block",
        }

    output = SignalOutput.model_validate(tool_block.input)

    signal: SignalData = {
        "ticker": ticker,  # type: ignore[typeddict-item]
        "direction": output.direction.value,
        "confidence": output.confidence,
        "event_type": output.event_type.value,
        "reasoning": output.reasoning,
    }

    if gen:
        gen.end(
            output={"direction": output.direction, "confidence": output.confidence},
            usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
        )

    log.info(
        "generate_signal.done",
        event_id=state["event_id"],
        ticker=ticker,
        direction=output.direction,
        confidence=output.confidence,
    )
    return {
        "signal": signal,
        "total_cost_usd": float(state["total_cost_usd"] + float(cost)),
    }
