from typing import Any

from langgraph.graph import END, StateGraph

from app.pipeline.nodes.error import handle_error
from app.pipeline.nodes.extract import extract_companies
from app.pipeline.nodes.reason import generate_signal
from app.pipeline.nodes.resolve import resolve_tickers
from app.pipeline.state import SignalState


def _route_after_resolve(state: SignalState) -> str:
    if state.get("error") or not state.get("ticker"):
        return "handle_error"
    return "generate_signal"


def _route_after_generate(state: SignalState) -> str:
    if state.get("error") or state.get("signal") is None:
        return "handle_error"
    return END


def build_graph() -> Any:
    builder: Any = StateGraph(SignalState)

    builder.add_node("extract_companies", extract_companies)
    builder.add_node("resolve_tickers", resolve_tickers)
    builder.add_node("generate_signal", generate_signal)
    builder.add_node("handle_error", handle_error)

    builder.set_entry_point("extract_companies")
    builder.add_edge("extract_companies", "resolve_tickers")
    builder.add_conditional_edges("resolve_tickers", _route_after_resolve)
    builder.add_conditional_edges("generate_signal", _route_after_generate)
    builder.add_edge("handle_error", END)

    return builder


# Compiled graph — import this in runner.py
graph: Any = build_graph().compile()
