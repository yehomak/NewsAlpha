---
name: langgraph-patterns
description: LangGraph patterns for the butterfly-effect signal pipeline. Auto-invoked when adding nodes, edges, or modifying the extract→resolve→reason chain. Teaches state schema design, node structure, error routing, and async Claude API integration.
---

# LangGraph Patterns — butterfly-effect

## Chain structure

```
extract_companies → resolve_tickers → generate_signal
                                    ↘ handle_error (on any failure)
```

All nodes are async. The chain is defined in `app/pipeline/graph.py`.

## State schema

Define state in `app/pipeline/state.py` using `TypedDict`:

```python
from typing import TypedDict

class SignalState(TypedDict):
    event_id: int
    headline: str
    body: str | None
    companies: list[str]          # from extract_companies
    tickers: list[str]            # from resolve_tickers (validated)
    signal: Signal | None         # from generate_signal
    error: str | None             # set by any node on failure
    total_cost_usd: float         # accumulated across nodes
```

## Node pattern

Each node receives full state, returns only the keys it updates:

```python
async def extract_companies(state: SignalState) -> dict:
    response = await claude_haiku(
        system="Extract company names from financial news.",
        user=state["headline"]
    )
    cost = compute_cost(response.usage, model="haiku")
    return {
        "companies": response.parsed.companies,
        "total_cost_usd": state["total_cost_usd"] + cost,
    }
```

Never return the full state dict — only the slice this node owns.

## Conditional edge for error routing

```python
def route_after_resolve(state: SignalState) -> str:
    if state.get("error") or not state["tickers"]:
        return "handle_error"
    return "generate_signal"

graph.add_conditional_edges("resolve_tickers", route_after_resolve)
```

## Error node

```python
async def handle_error(state: SignalState) -> dict:
    log.warning("pipeline_error", event_id=state["event_id"], error=state.get("error"))
    return {}  # terminal node, no further routing
```

## Graph assembly

```python
from langgraph.graph import StateGraph, END

builder = StateGraph(SignalState)
builder.add_node("extract_companies", extract_companies)
builder.add_node("resolve_tickers", resolve_tickers)
builder.add_node("generate_signal", generate_signal)
builder.add_node("handle_error", handle_error)

builder.set_entry_point("extract_companies")
builder.add_edge("extract_companies", "resolve_tickers")
builder.add_conditional_edges("resolve_tickers", route_after_resolve)
builder.add_edge("generate_signal", END)
builder.add_edge("handle_error", END)

graph = builder.compile()
```

## Invoking the graph

```python
result = await graph.ainvoke({
    "event_id": event.id,
    "headline": event.title,
    "body": event.body,
    "companies": [],
    "tickers": [],
    "signal": None,
    "error": None,
    "total_cost_usd": 0.0,
})
```

## Claude API helper pattern

Wrap calls to share Langfuse tracing:

```python
async def claude_haiku(system: str, user: str, trace=None) -> ParsedResponse:
    gen = trace.generation(name="haiku-call", model="claude-haiku-4-5-20251001") if trace else None
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if gen:
        gen.end(usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens})
    return response
```
