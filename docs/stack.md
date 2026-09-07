# Confirmed Stack

All choices below are decided. Rationale included for interview prep.

## Summary

| Component | Choice |
|---|---|
| LLM API | Claude API (Sonnet for reasoning, Haiku for cheap extraction) |
| Orchestration | LangGraph |
| Structured output | Pydantic v2 |
| API layer | FastAPI (async) |
| Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Scheduling | APScheduler |
| News sources | Alpaca News API (primary) + feedparser/RSS + NewsData.io (fallback); NewsAPI.org local dev only |
| Stock prices | yfinance |
| Observability | Langfuse (self-hosted in Docker Compose) |
| Testing | pytest + pytest-asyncio + custom eval harness |
| CI/CD | GitHub Actions (ruff, mypy, pytest, Docker build) |
| Containerization | Docker + Docker Compose |
| Deployment | Railway (mention ECS/Hetzner for prod in README) |
| MCP | FastMCP |

## Rationale per component

**Claude API** — strongest structured output reliability, prompt caching cuts costs on repeated system prompts. Good interview story since most people default to OpenAI. Sonnet for reasoning chain, Haiku for cheap entity extraction pass.

**LangGraph** — stateful graph for extract→resolve→reason shows the agentic pattern interviewers look for. Raw Anthropic SDK as fallback for simple one-shot steps.

**Pydantic v2** — non-negotiable. Validates LLM output, free serialization, integrates with FastAPI.

**FastAPI** — async, auto OpenAPI docs, native Pydantic integration. No debate.

**PostgreSQL + pgvector** — relational for signals/evals (GROUP BY queries are natural SQL), pgvector for semantic dedup. One DB, less ops.

**Why not MongoDB** — eval queries are inherently relational (accuracy breakdowns by ticker, sector, confidence, source). MongoDB aggregation pipelines for this are more verbose and harder to maintain. pgvector also eliminates the need for a separate vector store that MongoDB would require.

**SQLAlchemy 2.0 async + Alembic** — industry standard, async support, migrations included.

**APScheduler** — runs in-process with FastAPI, zero extra infra. Sufficient for hourly ingestion + daily eval jobs. Interview answer: "I'd migrate to ARQ/Celery at scale."

**Alpaca News API + feedparser + NewsData.io** — Alpaca (Benzinga partnership) is the primary source: 200 req/min free, pre-resolved ticker candidates already on each article, historical back to 2015, commercial use OK. feedparser covers RSS (Yahoo Finance, CNBC, PR Newswire) for breadth. NewsData.io (200/day free) as deployed fallback — NewsAPI.org is localhost-only per ToS and has a 1-month age cap. Reuters RSS was killed in 2020; Bloomberg is paywalled — neither is usable.

**trafilatura** — full article body extraction from URLs. feedparser returns 150–300 char truncated summaries; trafilatura fetches the full text. Required for quality LLM input. Fallback: design Stage 3 prompts to work on headline + summary only.

**tenacity** — retry decorator for HTTP fetches. 3 attempts, exponential backoff (1s→2s→4s). Handles NewsAPI 429s and feed timeouts without crashing the scheduler job.

**Ticker whitelist** — NASDAQ screener CSV (downloadable daily from nasdaq.com/market-activity/stocks/screener). Covers NASDAQ, NYSE, AMEX with company name + symbol + sector. Refreshed as a periodic job. Alpaca's pre-resolved `ticker_hints` feed into the whitelist validation step, not past it.

**yfinance** — free, no API key, T+5 lookups trivial. Unofficial API (note this in README — shows you know the tradeoff). Alpha Vantage free tier too rate-limited (25 req/day).

**Langfuse** — open-source, self-hostable in Docker Compose. Designed for LLM tracing. Trace screenshot in README is an explicit reviewer green flag. LangSmith is proprietary and requires LangChain.

**Ticker resolution** — LLM proposes ticker, code validates against static S&P 500 + NASDAQ whitelist. Reject if no match. This is the hallucination guardrail.

**pytest + custom eval harness** — pytest for unit tests (ticker resolver, signal parser, dedup). Custom eval harness for directional accuracy — better than RAGAS here because ground truth is objective (price movement), not subjective.

**Railway** — best DX for portfolio. Push-to-deploy, managed Postgres, real URL in 20 min. Free tier sufficient.

**FastMCP** — one decorator turns FastAPI endpoints into MCP tools. ~30 lines. Shows protocol-stack awareness, a senior signal in 2026 interviews.
