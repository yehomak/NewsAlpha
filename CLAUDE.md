# butterfly-effect

Financial news → LLM signal extraction → ground-truth eval harness.

## What this is

A pipeline that ingests financial/tech news, extracts company signals via LangGraph reasoning chains (Claude Sonnet for reasoning, Haiku for cheap extraction), and measures directional accuracy against actual T+5 stock price movement. The eval harness is the differentiator — signals are measured, not vibed.

## Architecture

```
news sources → ingest (feedparser/NewsAPI) → dedup → events table
events → LangGraph chain → ticker resolve → signals table
signals (T+5 elapsed) → yfinance → eval_results table
FastAPI → /signals, /eval/summary endpoints
FastMCP → MCP tool exposure
```

## Key tables

- `events` — raw deduplicated news stories, `url_hash` for dedup, `processed` flag
- `signals` — LLM output: ticker, direction (bullish/bearish/neutral), confidence, reasoning, cost_usd, langfuse_trace_id
- `eval_results` — ground truth: price_t0, price_t5, return_pct, correct (bool)
- `price_snapshots` — raw price fetches at offset_days (0 and 5)

## Stack

- FastAPI (async) + SQLAlchemy 2.0 async + Alembic + asyncpg
- PostgreSQL 16 + pgvector (semantic dedup in Stage 6)
- LangGraph — extract → resolve → reason chain
- Claude API: Sonnet for reasoning chain, Haiku for entity extraction
- Langfuse (self-hosted) — every LLM call traced, `langfuse_trace_id` stored on Signal
- APScheduler — hourly ingestion, daily eval job
- pydantic-settings for config (`app/config.py`, reads `.env`)
- structlog — structured JSON logging throughout

## Conventions

**Async everywhere** — all DB operations use `async with session` from `app/db/session.py`. Never use sync SQLAlchemy.

**Pydantic for LLM output** — all Claude responses validated through Pydantic models before touching the DB.

**Ticker resolver pattern** — LLM proposes ticker → validate against S&P 500 + NASDAQ whitelist → reject if no match. Never trust raw LLM ticker output.

**Cost tracking** — every LLM call records input + output tokens × price to `signals.cost_usd`. Use `anthropic` SDK usage response for this.

**Langfuse tracing** — wrap every LLM call in a Langfuse trace. Store `trace_id` on the Signal row.

## Git workflow

**Branch naming:** `agent/<topic>-<short-desc>` for AI-assisted work (e.g. `agent/stage2-ingestion`), `feat/<desc>` for manual feature work, `fix/<desc>` for bug fixes.

**Commits:** Conventional commits — `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`. Use `/commit` command.

**PRs:** Keep diffs focused — one stage at a time. Use `/pr` command. All PRs go through the PR template.

**Never commit directly to main.** Feature branch → PR → merge.

## Running locally

```bash
cp .env.example .env   # fill in API keys
docker compose up      # starts app + postgres + langfuse
```

Tests: `pytest`
Lint: `ruff check . && ruff format --check .`
Types: `mypy app`
Migrations: `alembic upgrade head`

## Current stage

Stage 1 complete: skeleton running, schema migrated, CI green.
Next: Stage 2 — ingestion pipeline (feedparser + NewsAPI, APScheduler, dedup).
