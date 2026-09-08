# butterfly-effect

Financial news → LLM signal extraction → ground-truth eval harness.

## What this is

A pipeline that ingests financial/tech news, extracts company signals via LangGraph reasoning chains (all Claude Haiku for cost control), and measures directional accuracy against actual T+5 stock price movement. The eval harness is the differentiator — signals are measured, not vibed.

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
- LangGraph — extract → resolve → reason chain (all Haiku, ~$0.001/article)
- Claude Haiku (`claude-haiku-4-5-20251001`) for all LLM nodes
- Langfuse (self-hosted on port 3000) — every LLM call traced, `langfuse_trace_id` stored on Signal; SDK pinned to `<3.0.0`
- APScheduler — hourly ingestion, 30-min pipeline, 6h eval job
- yfinance — T+5 price fetches for eval
- pydantic-settings for config (`app/config.py`, reads `.env`)
- structlog — structured JSON logging throughout

## Conventions

**Async everywhere** — all DB operations use `async with session` from `app/db/session.py`. Never use sync SQLAlchemy.

**Pydantic for LLM output** — all Claude responses validated through Pydantic models before touching the DB.

**Ticker resolver pattern** — Alpaca hint fast-path (if ticker already in `SIGNAL_UNIVERSE_SET`, skip LLM). Otherwise: LLM proposes ticker → validate against `SIGNAL_UNIVERSE_SET` (100 curated tickers) → reject if not in universe. Never trust raw LLM ticker output.

**Signal universe** — 100 tickers (`app/pipeline/universe.py`), curated by sector. Excludes utilities, REITs, gold miners, commodity E&P. Alpaca news API pre-filtered via `symbols=` param. Both resolver paths gate on `SIGNAL_UNIVERSE_SET`.

**Enum serialization** — `Mapped[Direction]` and `Mapped[EventType]` use `values_callable=lambda obj: [e.value for e in obj]` to make SQLAlchemy send lowercase values matching PostgreSQL enum labels. Always include this on any new enum-typed column.

**Truncation filter** — after `signal_data` is returned from the LangGraph chain, `_reasoning_flags_truncation()` in `runner.py` checks the reasoning for phrases like "cuts off mid-sentence", "truncated", etc. If flagged, returns `(None, cost)` — no signal inserted, event still marked `processed=True`.

**Semantic dedup** — on every ingest, `embed_text(title)` produces a 384-dim vector via `all-MiniLM-L6-v2` (local, free, lazy-loaded). `find_semantic_duplicate()` queries events from the last 24h with cosine distance < 0.05 (similarity > 0.95). Dupes are inserted with `processed=True` + `dedup_skipped=True` + `similar_to_id` + `similarity_score` — audit trail in DB, invisible to the pipeline. Never use a separate filter on `dedup_skipped` in pipeline queries; `processed=True` already excludes them.

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

## API endpoints

- `GET /health` — liveness check
- `POST /ingestion/trigger` — manual ingest run (202)
- `GET /ingestion/status` — event count + last fetch time
- `POST /signals/trigger` — manual pipeline run (202)
- `GET /signals` — list signals; filters: `ticker`, `direction`, `min_confidence`; pagination: `limit`, `offset`; inlines `return_pct` + `correct` when eval exists
- `GET /signals/{id}` — single signal with eval result
- `POST /eval/trigger` — manual eval run (202)
- `GET /eval/summary` — overall accuracy %, avg return, pending count, breakdown by direction and event_type

## Current stage

Stages 1–6 complete: skeleton, ingestion, LangGraph signal chain, T+5 eval harness, query API, pgvector semantic dedup — all merged to main.
Pipeline live: collecting signals, Langfuse tracing active (self-hosted). First T+5 eval results expected ~2026-09-13.

**Known gaps (not yet built):**
- API key auth on /signals and /eval endpoints (deferred, low priority — not internet-exposed)
- FastMCP wrapper (Stage 7)
- Railway deploy + README with real accuracy numbers (Stage 7/8)

Next: Stage 7 — FastMCP wrapper + Railway deploy.
