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

## Claude Code tooling

All tooling is set up and merged to `main`:

**Agents** (`.claude/agents/`)
- `signal-dev` — LangGraph chain, Langfuse tracing, ticker resolver, eval rules
- `code-reviewer` — async SQLAlchemy, Pydantic v2, LangGraph, Langfuse checklist
- `db-migration-agent` — Alembic patterns, pgvector, safety guardrails
- `eval-analyst` — T+5 design, segmentation, accuracy SQL queries

**Commands** (`.claude/commands/`)
- `/commit` — conventional commits with ruff pre-flight
- `/pr` — lint + mypy + test + structured PR description
- `/migrate` — Alembic migration generation and apply
- `/trace` — Langfuse trace lookup by signal_id or trace_id
- `/langgraph-patterns` — state schema, node structure, graph assembly
- `/eval-design` — T+5 rules, look-ahead bias prevention, accuracy targets

**Hooks** (`.claude/hooks/`)
- `pre-commit.sh` — blocks commit if ruff/mypy fail
- `commit-msg-check.sh` — validates conventional commit format
- `secret-scan.sh` — scans written files for hardcoded secrets
- `prompt-guard.sh` — blocks destructive DB operations without confirmation

## Current stage

Stages 1–3 complete: skeleton, ingestion pipeline, LangGraph signal chain all merged to main.
Next: Stage 4 — T+5 ground-truth eval with yfinance.
