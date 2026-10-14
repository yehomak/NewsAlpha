# NewsAlpha

Every day, thousands of financial news articles move stock prices. Most investors read the same headlines and form gut feelings. NewsAlpha asks a different question: **can an LLM reliably predict which direction a stock will move after a news event — and can we actually measure whether it's right?**

This is a full end-to-end answer to that question, built and measured in production.

---

## 🎯 The Problem

Financial news creates noisy, high-volume signal. The conventional wisdom is split: either "the market is efficient and you can't extract alpha from public news," or "sentiment analysis works" — but almost nobody builds a system that rigorously measures both the prediction *and* the outcome at scale.

The two failure modes:
1. **Vibes-based evaluation** — "the model said bullish and the stock went up, seems right!" No baseline, no sample size, no segmentation.
2. **Look-ahead bias** — accidentally using post-reaction prices as the input, making the signal look much better than it is.

---

## 📊 Results

First full eval wave: **Sep 8–17, 2026** · **656 signals evaluated** at T+5 market close.

```mermaid
xychart-beta
    title "Directional accuracy by segment (%)"
    x-axis ["Product launch", "Bearish", "Macro", "Bullish", "General", "Earnings"]
    y-axis "Accuracy %" 0 --> 100
    bar [61.0, 54.2, 45.3, 48.7, 36.2, 33.3]
```

| Segment | n | Accuracy | Read |
|---------|---|----------|------|
| Product launch | 118 | **61.0%** | Discrete, unambiguous — market hadn't priced it |
| Bearish | 120 | **54.2%** | Model reads downside catalysts better than upside |
| Macro | 106 | 45.3% | Noise zone — market-wide events too diffuse |
| Bullish | 312 | 48.7% | Near coin-flip — positive sentiment already priced in |
| General | 348 | 36.2% | Anti-signal territory |
| Earnings | 84 | **33.3%** | Strong anti-signal — flip it for ~67% ("sell the news") |
| Neutral | 224 | 25.4% | Expected — LLM struggles to call flat correctly |

Overall accuracy is **41.8%** — below random. But segmented, the picture is more useful: product launches have a real edge, earnings signals should be inverted, and bearish calls outperform bullish by 5.5 percentage points.

Information coefficient (IC): **0.035** — weak positive directional correlation (n=432 directional signals). Profit factor: **1.06** — dragged down by the general/earnings buckets; product_launch + bearish alone would show a much stronger ratio.

Avg abnormal return: **+0.97%** (T0→T5 return minus T-2→T0 pre-event drift).

Cost: **$0.0062 per signal** using Claude Haiku 4.5 with prompt caching.

---

## ⚙️ What We Built

**Signals are locked at T0 before the T+5 price is ever fetched.** The pipeline is forward-only by construction — look-ahead bias is architecturally impossible, not just avoided by convention.

The pipeline ingests financial news from 4 sources, deduplicates at three layers (URL hash, time-domain wire-service suppression, pgvector semantic similarity), then runs each story through a LangGraph chain: pre-filter → ticker resolution against a curated 100-stock universe → Claude Haiku reasoning → structured output. Five calendar days later, the eval job fetches the full price curve and scores the prediction.

### 🔄 Pipeline

```mermaid
flowchart TD
    classDef ingest fill:#0D47A1,color:#fff,stroke:#0D47A1
    classDef dedup fill:#4527A0,color:#fff,stroke:#4527A0
    classDef skip fill:#37474F,color:#bbb,stroke:#37474F
    classDef llm fill:#BF360C,color:#fff,stroke:#BF360C
    classDef store fill:#004D40,color:#fff,stroke:#004D40
    classDef eval fill:#1B5E20,color:#fff,stroke:#1B5E20
    classDef out fill:#01579B,color:#fff,stroke:#01579B

    A[News Sources\nAlpaca · Yahoo RSS · CNBC · NewsData]:::ingest --> B[Ingest\nevery 30 min]:::ingest

    B --> C{URL hash\ndedup}:::dedup
    C -->|seen| Z1[skip]:::skip
    C -->|new| D{Time-domain\ndedup\nsame source + ticker\n≤4h window}:::dedup
    D -->|duplicate| Z2[increment coverage_count]:::skip
    D -->|unique| E{pgvector\nsemantic dedup\ncosine > 0.95}:::dedup
    E -->|similar| Z3[dedup_skipped=true]:::skip
    E -->|distinct| F[(events table)]:::store

    F --> G[Pipeline\nevery 30 min]:::ingest
    G --> H{Pre-LLM filter\nuniverse keyword match}:::dedup
    H -->|no match| Z4[skip — free]:::skip
    H -->|match| I[Ticker resolver\nAlpaca hint OR Haiku → universe gate]:::llm
    I -->|rejected| Z5[extraction_attempt\noutcome=rejected]:::skip
    I -->|accepted| J[Haiku reasoning\ncache_control ephemeral]:::llm
    J -->|truncated| Z6[extraction_attempt\noutcome=truncated]:::skip
    J -->|signal| K[(signals table\nticker · direction · confidence\nevent_type · cost_usd)]:::store
    K --> L[extraction_attempt\noutcome=stored]:::store

    K --> M[Eval job\nevery 6h]:::eval
    M -->|T+5 not elapsed| Z7[skip until ready]:::skip
    M -->|T+5 elapsed| N[yfinance fetch\nT-2 · T-1 · T0 · T+1–T+5]:::eval
    N --> O[(eval_results\nreturn_pct · abnormal_return · correct)]:::eval

    K --> P[FastAPI]:::out
    O --> P
    P --> Q[React Dashboard]:::out
    P --> R[FastMCP\nClaude Desktop]:::out
```

### ⏱️ Eval Design

The signal (direction, confidence) is written at T0 and never modified. Prices are fetched days later — the two never touch until evaluation:

```mermaid
timeline
    title Signal lifecycle — no look-ahead bias
    T-2 : Pre-event baseline price fetched
        : (retroactively, at eval time)
    T-1 : Pre-event price fetched
        : (retroactively, at eval time)
    T0  : News published
        : Signal LOCKED in DB
        : direction · confidence · event_type
        : T0 price fetched at eval time
    T+1 : Price snapshot
    T+2 : Price snapshot
    T+3 : Price snapshot
    T+4 : Price snapshot
    T+5 : Final price fetched
        : return_pct computed
        : correct flag set
        : abnormal_return = return − pre-drift
```

---

## 🧠 Architecture

**LangGraph chain** — two nodes: ticker resolver (Alpaca hint fast-path, or LLM → validate against universe) and reasoning node (structured output via tool call). Every call traced in Langfuse.

**Universe gate** — 100 curated tickers (S&P 500 megacaps, no utilities/REITs/commodity E&P). Signals outside the universe are rejected — no hallucinated tickers reach the DB.

**Cost tracking** — every LLM call writes to `extraction_attempts`, including rejections. Nothing is invisible in the spend report.

**Abnormal return** — T0→T5 raw return minus the T-2→T0 pre-event drift. Isolates the news effect from pre-existing momentum.

**Stack:** FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16 + pgvector · LangGraph + Claude Haiku 4.5 · Langfuse (self-hosted) · APScheduler · yfinance · React + TypeScript + Vite · FastMCP

---

## 🚀 Run It

```bash
git clone https://github.com/yehomak/NewsAlpha
cp .env.example .env        # ANTHROPIC_API_KEY + ALPACA_API_KEY
docker compose up
```

App → `localhost:8000` · Dashboard → `localhost:5173` · Langfuse → `localhost:3000`

```bash
# Trigger manually
curl -X POST localhost:8000/ingestion/trigger
curl -X POST localhost:8000/signals/trigger
curl -X POST localhost:8000/eval/trigger

# Check results
curl localhost:8000/eval/summary
```

---

## 📁 Dive Deeper

- **[`app/pipeline/`](app/pipeline/)** — LangGraph chain: nodes, state, runner, universe
- **[`app/eval/`](app/eval/)** — pricer, T0 anchor, 8-point curve, abnormal return
- **[`app/api/routes/`](app/api/routes/)** — FastAPI endpoints
- **[`dashboard/src/`](dashboard/src/)** — React sections mapped to pipeline stages
- **[`CLAUDE.md`](CLAUDE.md)** — full architecture reference
