import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from app.config import settings
from app.pipeline.costs import compute_cost
from app.pipeline.langfuse_client import get_langfuse
from app.pipeline.state import SignalState

log = structlog.get_logger()

_HAIKU = "claude-haiku-4-5-20251001"


class CompanyList(BaseModel):
    companies: list[str]


async def extract_companies(state: SignalState) -> dict:  # type: ignore[type-arg]
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    lf = get_langfuse()

    text = state["headline"]
    if state["body"]:
        text = f"{state['headline']}\n\n{state['body'][:1000]}"

    gen = None
    if lf:
        gen = lf.generation(
            name="extract_companies",
            model=_HAIKU,
            trace_id=state.get("langfuse_trace_id"),
            input={"text": text[:200]},
        )

    try:
        response = await client.messages.create(
            model=_HAIKU,
            max_tokens=256,
            tools=[
                {
                    "name": "output",
                    "description": "List of publicly traded company names mentioned in the text.",
                    "input_schema": CompanyList.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": "output"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Extract the names of publicly traded companies mentioned in this "
                        "financial news. Include only companies that could have a stock ticker."
                        f"\n\n{text}"
                    ),
                }
            ],
        )
    except Exception as exc:
        log.exception("extract_companies.api_error", event_id=state["event_id"])
        if gen:
            gen.end(level="ERROR", status_message=str(exc))
        return {"error": f"extract_companies failed: {exc}"}

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_block:
        if gen:
            gen.end(level="WARNING", status_message="no tool_use block")
        return {"companies": [], "total_cost_usd": state["total_cost_usd"]}

    result = CompanyList.model_validate(tool_block.input)
    cost = compute_cost(response.usage, _HAIKU)

    if gen:
        gen.end(
            output={"companies": result.companies},
            usage={
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
        )

    log.info("extract_companies.done", event_id=state["event_id"], count=len(result.companies))
    return {
        "companies": result.companies,
        "total_cost_usd": float(state["total_cost_usd"] + float(cost)),
    }
