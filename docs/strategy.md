# Strategy

## Concept

> Small news events cause large stock movements. This system finds the signal before the market does.

A pipeline that ingests financial/tech news, extracts company signals using LLM reasoning chains, and measures whether those signals predict actual stock price movement — ground truth, not vibes.

## Why this project wins interviews

The eval harness is the killer differentiator. Ground-truth directional accuracy (did the stock move the right direction at T+5 days?) is objective and measurable. Almost no portfolio project in this space has this — every comparable open-source project (FinGPT, Tickermind, llm-financial-sentiment-analysis) is Jupyter-only with no eval, no dedup, no structured output, no API.

Secondary differentiators:
- Ticker resolution with hallucination guardrail (LLM proposes → whitelist validates)
- Every LLM call traced in Langfuse (observability green flag)
- Semantic dedup via pgvector (RAG-adjacent skill, no separate RAG app needed)
- Cost tracked per signal ($X per 1000 signals — shows production maturity)
- MCP tool exposure (FastMCP, ~30 lines — senior signal)
- Forward-only real-time pipeline (immune to look-ahead bias — arxiv 2309.17322)

## What the 2026 hiring bar looks like

Top take-home assignment types (from 100+ real GitHub repos, Q4 2025–Q1 2026):
- RAG systems — 40%+ of assignments
- Agentic systems — 30%+
- LLM-as-judge evaluation — 10%+

Green flags reviewers scan for:
- Production deployment with monitoring stack
- Evaluation results with specific metrics (faithfulness, accuracy, latency SLOs)
- Cost optimization work (quantified)
- Graceful LLM failure handling
- Langfuse/LangSmith trace screenshot in README

Red flags: Jupyter-only, no eval framework, just an API wrapper with no architecture.

The biggest gap: 89% of prod teams have observability, only 52% have evals. This project has both.

Senior-specific signals: LangGraph agentic orchestration, prompt caching awareness, MCP protocol, LLM-as-judge or ground-truth eval harness.

## Commercial landscape

Commercial alternatives cost $24k–$50k+/year (RavenPack, Bloomberg, LSEG MarketPsych) and don't publish live accuracy stats. A portfolio project with real measured numbers is credible by comparison.

## Interview narrative

> "I built a signal pipeline that ingests financial news, extracts company signals via LLM reasoning, and measures whether those signals predict actual stock movement. The hard parts were ticker resolution (hallucination guardrail against an S&P 500/NASDAQ whitelist), semantic deduplication (same story from 5 outlets = 1 event via pgvector), and the eval design (T+5 directional accuracy with breakdown by sector, confidence, and event type). I currently run at X% directional accuracy over N signals. Every LLM call is traced in Langfuse — here's a trace screenshot."

## Accuracy targets

- Random baseline: 50%
- Realistic target: 55–65% out-of-sample
- Academic studies: 63–72% in controlled settings (in-sample, higher)
- Claim 58–62% with real data — credible and honest. Don't chase 70%+ (signals overfitting).
- News predicts *volatility* more reliably than *direction* — state this in README (shows domain awareness)
