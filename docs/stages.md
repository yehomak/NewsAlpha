# Project Stages

butterfly-effect decomposed foundation-up: infrastructure first, then data ingestion, then LLM extraction, then measurement. Each stage has one job and builds on the last. Stages 1–6 build the pipeline; 7–8 make it visible; 9–10 make it provable.

## Stage 1 — Foundation

- Docker Compose: FastAPI + PostgreSQL (pgvector) + Langfuse
- SQLAlchemy models: `events`, `signals`, `eval_results`, `price_snapshots`
- Alembic migration setup (indexes on `ticker/created_at`, `event_type`, `published_at`)
- GitHub repo + GitHub Actions CI (ruff, mypy, pytest, Docker build — from day one)
- `.env` config, structured logging setup
- FastAPI with `/health` endpoint
- Claude Code tooling: agents, skills, commands, hooks — see `CLAUDE.md`

---

## Stage 2 — Ingestion Pipeline

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

## Stage 3 — LLM Signal Extraction

- LangGraph reasoning chain: extract companies → resolve tickers → produce signal
- Pydantic output model: `Signal(ticker, direction, confidence, reasoning, cost_usd, event_type)`
- Ticker resolver: LLM proposes → validate against curated 100-ticker universe → reject if no match
- Pre-LLM relevance filter: `_has_universe_mention()` scans title + body for ticker symbols and company keywords before spending tokens
- Langfuse tracing wired in from the start (every LLM call traced, `langfuse_trace_id` stored on Signal)
- Cost tracking per signal logged to DB (input + output tokens × price)

**Milestone:** batch of news stories produces structured signals with traces visible in Langfuse.

---

## Stage 4 — Ground Truth + Eval Harness

- yfinance price fetcher: closing price at T and T+5 (market-hours-aware — after-hours news uses next open)
- APScheduler daily job: evaluates signals where T+5 has passed
- Directional accuracy calc, stored in `eval_results`
- Breakdown by: ticker, sector, confidence band, news source, event_type
- `/eval/summary` endpoint: overall accuracy, sample size, full breakdown

**Milestone:** 50+ signals evaluated, accuracy number exists. This is the interview story.

**Note:** segment by `event_type` (earnings / product_launch / macro / general) — earnings signals often invert post-announcement ("buy the rumor, sell the news"), which skews overall accuracy if unsegmented.

**T+1 directional accuracy** as secondary metric alongside T+5 — shows the signal decay curve (signal exists but gets absorbed as the market catches up).

---

## Stage 5 — API Layer

- `GET /signals` — paginated, filterable by ticker/direction/confidence; inlines `return_pct` + `correct` when eval exists
- `GET /signals/{id}` — single signal with eval result
- `GET /eval/summary` — accuracy stats with full breakdown
- `POST /signals/trigger` / `POST /ingestion/trigger` — manual run triggers (202)
- `GET /stats/tickers` / `/stats/events` / `/stats/costs` / `/stats/pipeline` — dashboard data endpoints
- OpenAPI docs auto-generated by FastAPI

---

## Stage 6 — Semantic Dedup + pgvector

- pgvector extension enabled in Postgres
- `all-MiniLM-L6-v2` (384-dim, local, free) embeds headlines on ingest
- Cosine similarity threshold 0.05 (>0.95 similarity) over 24h window → duplicate suppressed
- Dupes inserted with `processed=True` + `dedup_skipped=True` + `similar_to_id` + `similarity_score` — audit trail in DB, invisible to pipeline
- `processed=True` already excludes dupes from pipeline queries — no extra filter needed

---

## Stage 7 — Dashboard Base

React + TypeScript + Vite SPA in `dashboard/`. Dark terminal aesthetic: monospace for tickers/numbers, green/red for direction, amber accent.

**Sections:**
1. Header bar — status pill, last ingest/pipeline time, theme toggle
2. Hero metrics — directional accuracy %, total signals, total cost, events ingested
3. Tickers grid — per-ticker card: accuracy rate, signal count, last direction; click → modal with full signal history
4. Signal feed — latest signals: ticker, direction chip, confidence bar, event type, correct/wrong badge
5. Eval & accuracy breakdown — by direction, by event type, pending count
6. Event intelligence — processed / unprocessed / dedup-skipped, by source
7. Cost & spend — total spend, avg cost per signal, daily spend sparkline
8. Process timeline — last run times, signals/events today

---

## Stage 8 — Dashboard Rework

Complete dashboard redesign — single page structured by pipeline stage, each section answering real questions about that stage with ratios, groups, and outliers.

**Five pipeline-stage sections:**

1. **Ingestion** — total events, events today, active sources, dedup rate; source breakdown bars; processed rate callout
2. **Extraction Funnel** — 4-step funnel (ingested → dedup removed → sent to LLM → signals stored) with absolute counts and retention % at every drop; acceptance rate + cost-per-attempt callouts
3. **Signal Portfolio** — direction split, confidence buckets (`<0.5` noise / `0.5–0.7` low / `0.7–0.85` mid / `≥0.85` high), event type mix, top-8 tickers by coverage, last-10 signal feed
4. **Ground Truth** — pending state until T+5 evals land; flips to accuracy breakdown by direction + event_type with color-coded accuracy rates
5. **Cost & Efficiency** — total spend (real vs tracked), avg cost per signal, daily bar chart, efficiency callouts

Earlier dashboard cards (PipelineIntel, SignalProfile, SignalLedger) replaced by this structure. Signal Ledger removed.

---

## Stage 9 — FastMCP + Pipeline Improvements

### 9A — FastMCP
~30 lines wrapping `/signals` and `/eval/summary` as MCP tools. Makes the pipeline callable from Claude Desktop and any MCP client.

### 9B — Pipeline cost tracking fix
Currently ~48% of real API spend is untracked — tokens burned on ticker resolver rejections and truncation rejections are only structlog-logged, never written to DB. Fix: add `extraction_attempts` table.

Schema:
```
event_id | ticker_proposed | outcome | rejection_reason | cost_usd | created_at
```

Outcomes: `stored` / `rejected_universe` / `truncated` / `no_signal` / `error`

Benefits: accurate total cost accounting, universe gap detection (which companies are frequently proposed but rejected), truncation rate by source, real pipeline efficiency ratio.

### 9C — Prompt caching
Zero cache reads/writes currently — system prompt (~800 tokens) re-sent on every Haiku call. Add `cache_control: {type: "ephemeral"}` to system prompt. ~10–20% total bill reduction; ~90% reduction on system prompt input tokens specifically.

### 9D — README
- Mermaid pipeline diagram (news → ingest → dedup → LangGraph → eval → dashboard)
- Langfuse trace screenshot
- Real accuracy table: "X% directional accuracy over N signals, T+5"
- Cost stats: "$X avg per signal, $Y total tracked"
- Note on look-ahead bias immunity (forward-only pipeline)
- Local setup in 3 commands (`git clone`, `cp .env.example .env`, `docker compose up`)

*README blocked on real accuracy numbers — build after Stage 10 results land.*

---

## Stage 9E — Visualization Tab

Second dashboard tab: 2D/3D visualizations of signal data. Builds the portfolio story visually pre-eval; becomes dramatically more interesting after T+5 results land.

**Visualizations (ranked by interview demo value):**

### Pre-eval (available now)

**Ticker × Confidence Scatter** — X: avg confidence, Y: signal count, color: last direction. Answers "where do we have high-conviction portfolio positions?" Post-eval: size encodes accuracy_pct. Canvas or D3.

**Signal Timeline Heatmap** — rows = tickers (sorted by signal count), columns = days, cell color = direction, opacity = confidence. Shows the pipeline is alive with consistent directional views. Post-eval: ✓/✗ badge overlay per cell. Canvas (one rect per cell).

**Extraction Funnel Sankey** — ingested → LLM → [stored | rejected_universe | no_signal | truncated] as a flow diagram. Tells the yield/cost story visually. D3 sankey or Canvas paths.

### Post-eval (Sep 13+)

**3D Accuracy Landscape** — X: confidence bucket, Z: event_type, Y: accuracy % as 3D bars or mesh surface. Rotation via OrbitControls. Answers "where does the model actually know what it's doing?" — the interview showstopper. Three.js.

**Confidence Calibration Curve** — stated confidence (bucketed) vs actual accuracy % overlaid on the "perfectly calibrated" diagonal. Classic ML eval visualization. Proves whether the confidence score is meaningful ("overconfident in the 0.7–0.85 band"). Canvas or SVG. Low complexity, very high credibility.

**Build plan:** ship Scatter + Heatmap now. Add placeholder panels for Accuracy Landscape + Calibration showing "waiting for T+5 data" — they light up automatically after Sep 13.

---

## Stage 10 — Eval Grid

New dashboard section: per-signal eval table once T+5 results land.

Columns: ticker · direction · confidence · T0 price · T5 price · return% · correct/wrong badge

This is the visual centerpiece — proof the numbers are real. The interview claim ("X% directional accuracy over N signals") only becomes concrete here.

---

## Stage 11 — Deploy

Railway is no longer free. Options if a public URL is needed: Fly.io (hobby tier free), Render (free tier). Docker Compose local setup is sufficient for a technical review. Defer until clear whether a live URL is required for target interviews.

---

## Timeline summary

| Stage | Focus |
|---|---|
| 1 | Foundation |
| 2 | Ingestion |
| 3 | LLM pipeline |
| 4 | Eval harness |
| 5 | API |
| 6 | pgvector semantic dedup |
| 7 | Dashboard base |
| 8 | Dashboard enhancements |
| 9A | FastMCP |
| 9B | Pipeline cost tracking |
| 9C | Prompt caching |
| 9D | README |
| 9E | Visualization tab |
| 10 | Eval grid |
| 11 | Deploy |
