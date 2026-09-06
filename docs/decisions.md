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

## Forward-only pipeline (no backtesting)

**Decision:** Run signals in real-time only, no historical backtesting.

**Why:** LLM backtests are contaminated by look-ahead bias — the model was trained on data that includes the outcomes (arxiv 2309.17322). Forward-only avoids this entirely. Also makes the accuracy claims honest and defensible.
