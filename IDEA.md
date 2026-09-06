# butterfly-effect

> Small news events cause large stock movements. This system finds the signal before the market does.

## Concept

A pipeline that ingests financial/tech news, extracts company signals using LLM reasoning chains, and correlates them with actual stock price movements — measured and evaluated, not just vibes.

## What it does

1. **Ingest** — pull news from multiple sources (RSS, NewsAPI, etc.), deduplicate cross-source stories
2. **Extract** — identify companies/tickers mentioned, filter noise
3. **Reason** — LLM reasoning chain produces a structured signal: bullish/bearish, confidence, why
4. **Store** — signals + metadata in PostgreSQL; actual price data fetched N days later
5. **Eval** — measure directional accuracy of signals vs real price movement (ground truth)
6. **API** — FastAPI endpoints to query signals, accuracy stats, signal history

## What makes it real engineering (not a tutorial)

- Multi-source deduplication — same story from 5 outlets = 1 event
- Ticker resolution — "Apple" → AAPL, handles ambiguity and hallucination
- Structured LLM output — Pydantic models, not raw text
- Eval harness — automated weekly accuracy measurement vs actual stock moves
- Cost tracking — $ per signal generated
- Failure handling — LLM hallucination guardrails, API downtime fallbacks

## Stack

- **FastAPI** — API layer
- **PostgreSQL + SQLAlchemy** — signals, events, eval results
- **Celery or APScheduler** — scheduled ingestion and eval jobs
- **LangGraph** — reasoning chain orchestration
- **Claude API** — LLM backbone
- **Pydantic** — structured outputs and validation
- **pytest** — unit tests + eval harness
- **Docker + GitHub Actions** — containerized, CI passing

## Eval design

- Signal generated at T
- Price fetched at T+5 days
- Directional accuracy: did the stock move in the predicted direction?
- Track by: source, sector, confidence level, model version
- Goal: beat 50% baseline consistently across 200+ signals

## Narrative for interviews

"I built a signal pipeline that ingests financial news, extracts company signals via LLM reasoning, and measures whether those signals predict actual stock movement. The hard part was [dedup / ticker resolution / eval design]. I currently run at X% directional accuracy over N signals."

## Scope (6-8 weeks, ~5h/week)

- Wk 1-2: ingestion pipeline + PostgreSQL schema
- Wk 3-4: LLM entity extraction + signal reasoning chain
- Wk 5-6: eval harness + price data integration
- Wk 7-8: FastAPI endpoints + README + Docker + deploy
