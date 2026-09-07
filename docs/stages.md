# Build Stages

The eval harness (Stage 4) is the narrative anchor — everything else supports it.

## Stage 1 — Foundation (Week 1)
**Goal: skeleton that actually runs**

- Docker Compose: FastAPI + PostgreSQL (pgvector) + Langfuse
- SQLAlchemy models: `events`, `signals`, `eval_results`, `price_snapshots`
- Alembic migration setup (indexes on `ticker/created_at`, `event_type`, `published_at`)
- GitHub repo + GitHub Actions CI (ruff, mypy, pytest, Docker build — from day one)
- `.env` config, structured logging setup
- FastAPI with `/health` endpoint
- Claude Code tooling: agents, skills, commands, hooks — see `CLAUDE.md`

**Status: complete.**

**Why first:** everything else plugs into this. Don't start with LLM code.

---

## Stage 2 — Ingestion Pipeline (Week 1–2)
**Goal: raw news flowing into the DB**

Sources (Reuters RSS dead since 2020; Bloomberg paywalled — both removed from original spec):
- **Alpaca News API** (primary) — 200 req/min free, Benzinga-curated, pre-resolved ticker candidates, back to 2015. Best free financial news API.
- **RSS via feedparser** — Yahoo Finance, CNBC, PR Newswire / GlobeNewswire sector feeds
- **NewsData.io** (fallback) — 200 req/day free, commercial use OK in deployed env
- **NewsAPI.org** — local dev only; production ToS blocks non-localhost, 1-month article age cap

Body text note: RSS/feedparser returns 150–300 char truncated summaries, not full article body. Add **Trafilatura** fetch per event for full text. Also: design Stage 3 prompts to work on headline + 1-sentence summary as a fallback (some outlets block scrapers).

Dedup — three layers:
1. **URL hash**: SHA-256 of normalized URL (strip `?query`, lowercase, strip trailing `/`)
2. **Time-domain**: same source domain + overlapping `ticker_hints` + ≤4hr window → suppress, increment `coverage_count`. Cheap wire-service duplicate filter before LLM calls.
3. **Semantic**: pgvector cosine similarity on headline embeddings (Stage 6)

Schema additions vs. original spec:
- `ticker_hints` JSONB on Event — Alpaca pre-resolved candidates, fed to Stage 3 resolver as starting point
- `coverage_count` int on Event — incremented on time-domain suppression; high count = market-moving story
- Composite index `(processed, fetched_at)` — required for Stage 3 batch query performance

Reliability:
- tenacity retry: 3×, exponential backoff (1s→2s→4s), on HTTP 429/5xx; no retry on 404/401
- Conditional GET: ETag + `If-Modified-Since` per feed (feedparser handles natively via `feed.etag` / `feed.modified`)
- Article age filter: skip `published_at > now - 7 days` at ingest (stale news = noise for T+5 eval)

APScheduler `AsyncIOScheduler` wired into FastAPI lifespan — single-worker only. Multi-worker deployment needs scheduler in a separate process or APScheduler 4.x (asyncio-native, beta).

**Milestone:** DB fills with deduplicated news automatically; `coverage_count > 1` visible on wire-service duplicates; ticker_hints populated from Alpaca.

---

## Stage 3 — LLM Signal Extraction (Week 2–3)
**Goal: structured signals from news**

- LangGraph reasoning chain: extract companies → resolve tickers → produce signal
- Pydantic output model: `Signal(ticker, direction, confidence, reasoning, cost_usd, event_type)`
- Ticker resolver: LLM proposes → validate against S&P 500 + NASDAQ whitelist → reject if no match
- Langfuse tracing wired in from the start (every LLM call traced)
- Cost tracking per signal logged to DB (input + output tokens × price)

**Milestone:** run batch of 20 stories, get structured signals with traces visible in Langfuse.

---

## Stage 4 — Ground Truth + Eval Harness (Week 4–5)
**Goal: measure if signals are actually right**

- yfinance price fetcher: closing price at T and T+5 (market-hours-aware — after-hours news uses next open)
- APScheduler daily job: evaluates signals where T+5 has passed
- Directional accuracy calc, stored in `eval_results`
- Breakdown by: ticker, sector, confidence band, news source, event_type
- `/eval/summary` endpoint: overall accuracy, sample size, full breakdown

**Milestone:** 50+ signals evaluated, accuracy number exists. This is the interview story.

**Note:** segment by `event_type` (earnings / product_launch / macro / general) — earnings signals often invert post-announcement ("buy the rumor, sell the news"), which skews overall accuracy if unsegmented.

**Add T+1 directional accuracy as a secondary metric alongside T+5.** T+1 will be measurably higher, showing the signal decay curve — the signal exists but gets absorbed as the market catches up. More interesting than a single T+5 number and shows domain understanding.

---

## Stage 5 — API Layer (Week 5–6)
**Goal: clean, queryable API**

- `GET /signals` — paginated, filterable by ticker/date/confidence
- `GET /signals/{ticker}` — signal history for a stock
- `GET /eval/summary` — accuracy stats with breakdown
- `POST /signals/run` — trigger manual signal generation
- Simple API key auth (header-based)
- OpenAPI docs auto-generated by FastAPI

---

## Stage 6 — Semantic Dedup + pgvector (Week 6)
**Goal: upgrade dedup, add vector skill signal**

- Enable pgvector extension in Postgres
- Embed headlines on ingest (Claude or lightweight model)
- Skip stories with cosine similarity > threshold vs recent embeddings
- Replaces/supplements hash dedup
- ~50 lines of code, adds RAG-adjacent skill to the project story

---

## Stage 7 — Production Polish (Week 7)
**Goal: looks like real software**

- Dockerfile optimized (multi-stage build)
- GitHub Actions green: ruff, mypy, pytest, Docker build
- Deploy to Railway — get a real URL
- FastMCP wrapper for `/signals` (~30 lines, MCP tool exposure)

---

## Stage 8 — README + Narrative (Week 8)
**Goal: the 5-minute reviewer impression**

- Architecture diagram (Mermaid)
- Langfuse trace screenshot
- Eval results table with real numbers: "X% directional accuracy over N signals"
- Cost stats: "$X per 1000 signals"
- Note on look-ahead bias immunity (forward-only pipeline, cite arxiv 2309.17322)
- Local setup in 3 commands (`git clone`, `cp .env.example .env`, `docker compose up`)
- Short Loom demo video (3 min max)

---

## Timeline summary

| Stage | Focus | Key output |
|---|---|---|
| 1 | Foundation | Runnable skeleton |
| 2 | Ingestion | News flowing into DB |
| 3 | LLM pipeline | Traced, structured signals |
| 4 | Eval harness | Accuracy number exists |
| 5 | API | Queryable endpoints |
| 6 | pgvector | Semantic dedup |
| 7 | Polish | Live URL, CI green |
| 8 | README | Reviewer-ready in 5 min |
