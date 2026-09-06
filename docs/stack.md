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
| News sources | feedparser (RSS) + NewsAPI free tier |
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

**feedparser + NewsAPI** — feedparser is free, no key, covers Reuters/Bloomberg RSS/Yahoo Finance. NewsAPI free tier = 100 req/day, good for volume. Polygon.io News as paid upgrade (pre-attaches ticker metadata).

**yfinance** — free, no API key, T+5 lookups trivial. Unofficial API (note this in README — shows you know the tradeoff). Alpha Vantage free tier too rate-limited (25 req/day).

**Langfuse** — open-source, self-hostable in Docker Compose. Designed for LLM tracing. Trace screenshot in README is an explicit reviewer green flag. LangSmith is proprietary and requires LangChain.

**Ticker resolution** — LLM proposes ticker, code validates against static S&P 500 + NASDAQ whitelist. Reject if no match. This is the hallucination guardrail.

**pytest + custom eval harness** — pytest for unit tests (ticker resolver, signal parser, dedup). Custom eval harness for directional accuracy — better than RAGAS here because ground truth is objective (price movement), not subjective.

**Railway** — best DX for portfolio. Push-to-deploy, managed Postgres, real URL in 20 min. Free tier sufficient.

**FastMCP** — one decorator turns FastAPI endpoints into MCP tools. ~30 lines. Shows protocol-stack awareness, a senior signal in 2026 interviews.
