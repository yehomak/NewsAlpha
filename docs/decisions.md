# Decision Log

Key architectural decisions with rationale. Reference this when you forget why something was chosen.

---

## PostgreSQL over MongoDB

**Decision:** PostgreSQL + pgvector, not MongoDB.

**Why:** The eval harness — directional accuracy breakdowns by ticker, sector, confidence band, and source — is inherently relational. MongoDB aggregation pipelines for GROUP BY queries are more verbose and harder to maintain than SQL. pgvector also eliminates the need for a separate vector store, which MongoDB would require (Atlas Vector Search is cloud-only and paid).

**Interview answer:** "Eval queries are naturally relational. pgvector covered the vector search need without adding a second database to the stack."

---

## APScheduler over Celery

**Decision:** APScheduler running in-process with FastAPI, not Celery + Redis.

**Why:** Celery adds Redis as a dependency and significant operational overhead. For hourly ingestion and daily eval jobs at portfolio scale, APScheduler is sufficient and the tradeoff is defensible.

**Interview answer:** "APScheduler is sufficient for current volume. I'd migrate to ARQ or Celery with a Redis broker at scale when job isolation and retry semantics become critical."

---

## Langfuse over LangSmith

**Decision:** Langfuse for observability/tracing.

**Why:** Langfuse is open-source, self-hostable in Docker Compose, and not tied to LangChain. LangSmith is proprietary and requires LangChain usage. Langfuse running in Docker Compose means anyone cloning the repo gets full observability with zero extra setup.

---

## yfinance over Polygon.io / Alpha Vantage

**Decision:** yfinance for stock price ground truth.

**Why:** Free, no API key, covers all major tickers. Alpha Vantage free tier is 25 req/day — too tight for eval runs. Polygon.io is paid and only worth it for intraday data, which this project doesn't need.

**Caveat to note in README:** yfinance is an unofficial API. Production systems would use a paid provider.

---

## LangGraph over raw SDK for orchestration

**Decision:** LangGraph for the main reasoning chain.

**Why:** Stateful graph (extract→resolve→reason) shows the agentic pattern interviewers look for in 2026. Raw SDK used for simple one-shot steps where LangGraph would be overkill.

---

## Custom eval harness over RAGAS

**Decision:** Custom ground-truth eval, not RAGAS.

**Why:** RAGAS is designed for RAG faithfulness scoring (LLM-as-judge). This project has *objective* ground truth — the stock either moved in the predicted direction or it didn't. Custom eval is simpler, more credible, and more directly tied to the interview narrative.

---

## Ticker resolution approach

**Decision:** LLM proposes ticker → validate against static S&P 500 + NASDAQ whitelist → reject if no match.

**Why:** Pure LLM ticker guessing hallucinates (invents tickers). Static whitelist alone misses edge cases and synonyms ("Apple" vs "Apple Inc." vs "AAPL"). The hybrid approach catches both failure modes.

---

## FastMCP for MCP exposure

**Decision:** Add FastMCP wrapper for `/signals` in Stage 7.

**Why:** ~30 lines of code. MCP/A2A protocol awareness is a senior signal in 2026 AI engineer interviews. Shows you understand the protocol stack without over-engineering.

---

## Alpaca News API over NewsAPI.org as primary source

**Decision:** Alpaca News API (Benzinga partnership) as the primary financial news source. NewsAPI.org demoted to local dev only.

**Why:** NewsAPI.org free tier blocks non-localhost requests in production (ToS restriction), has a 1-month article age cap, and caps at 100 req/day. Alpaca News is 200 req/min, goes back to 2015, allows commercial use on the free tier, and includes pre-resolved ticker candidates per article (from Benzinga's editorial tagging). Those ticker candidates feed Stage 3's resolver as starting hints, reducing LLM hallucination surface before whitelist validation.

Reuters RSS was killed in 2020; Bloomberg has no public RSS — both removed from the original spec.

**Interview answer:** "I switched from NewsAPI to Alpaca when I discovered NewsAPI's production ToS restriction. Alpaca also gives me pre-resolved ticker candidates from Benzinga, which reduces the LLM's hallucination surface in the resolver step."

---

## SHA-256 over MD5 for URL hashing

**Decision:** SHA-256 for the `url_hash` dedup field, not MD5.

**Why:** MD5 is deprecated for integrity use cases. SHA-256 is collision-resistant and the right default for a DB unique constraint. The hashed input is the normalized URL (query string stripped, lowercased, trailing slash removed) — not the raw URL, because the same story gets tracking params appended across outlets.

---

## Three-layer dedup: hash → time-domain → semantic

**Decision:** Add a time-domain middle layer between hash dedup (Stage 2) and semantic dedup (Stage 6).

**Why:** URL hash catches exact duplicates. Semantic pgvector dedup (Stage 6) catches same-story-different-headline. But wire services publish the same story to 50 outlets simultaneously with 50 different URLs and slightly different titles. Running LLM extraction on all 50 is expensive and noisy. Time-domain rule: same source domain + overlapping ticker hints + ≤4hr window → suppress, increment `coverage_count`. Zero LLM cost. Estimated 30–40% reduction in duplicate LLM calls on high-news days.

`coverage_count` on the Event row is a secondary data point: high-coverage stories correlate with market impact and can be used as a signal weight in Stage 4 eval.

---

## T+1 accuracy as secondary eval metric alongside T+5

**Decision:** Track and expose T+1 directional accuracy in `eval_results` alongside T+5.

**Why:** T+5 is the primary metric (captures residual drift). T+1 will be measurably higher — the signal is stronger closer to the news event and decays as the market absorbs it. The T+1 vs. T+5 decay curve is more interesting than a single number: it shows you understand the mechanism, not just the metric. Required for Stage 4 eval schema — add `price_t1` and `correct_t1` to `eval_results`.

---

## Forward-only pipeline (no backtesting)

**Decision:** Run signals in real-time only, no historical backtesting.

**Why:** LLM backtests are contaminated by look-ahead bias — the model was trained on data that includes the outcomes (arxiv 2309.17322). Forward-only avoids this entirely. Also makes the accuracy claims honest and defensible.
