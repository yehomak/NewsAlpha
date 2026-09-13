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

## ⚙️ What We Built

An automated pipeline that:

1. **Ingests** financial news continuously from 4 sources (Alpaca, Yahoo Finance RSS, CNBC RSS, NewsData.io)
2. **Deduplicates** at three layers — URL hash, time-domain wire-service suppression, and pgvector semantic similarity (so the same story from 5 outlets counts once)
3. **Extracts signals** via a LangGraph reasoning chain: pre-filter (no LLM cost if the article doesn't mention a tracked company) → ticker resolution against a curated 100-stock universe → Claude Haiku reasoning → structured output (direction, confidence, event type)
4. **Measures ground truth** — 5 calendar days later, fetches closing prices from yfinance and asks: was the directional call correct?
5. **Tracks everything** — every LLM call (including rejections), every dollar spent, every price point from T-2 to T+5 per signal

The key design choice: **signals are locked before the T+5 price is ever fetched**. The pipeline is forward-only by construction — no look-ahead bias possible.

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

### ⏱️ Eval Timeline

The core anti-bias guarantee, visualised:

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

The signal (direction, confidence) is written at T0 and never modified. The price is fetched days later. The two never touch until evaluation — that's the guarantee.

---

## 📊 Results

First eval wave landed Sep 13, 2026 — 5 days after pipeline went live.

**760 signals extracted · 104 evaluated · 45.2% overall accuracy**

```mermaid
xychart-beta
    title "Directional accuracy by segment (%)"
    x-axis ["Bearish", "Macro", "General", "Neutral", "Bullish", "Earnings"]
    y-axis "Accuracy %" 0 --> 100
    bar [72.2, 60.0, 49.1, 46.3, 33.3, 15.8]
```

| Segment | n | Accuracy | Signal |
|---------|---|----------|--------|
| Bearish calls | 18 | **72.2%** | Real — model catches downside catalysts |
| Macro events | 20 | **60.0%** | Market-wide news reads well |
| General news | 57 | 49.1% | Near coin-flip |
| Bullish calls | 45 | 33.3% | Below random — positive news already priced in |
| Earnings | 19 | **15.8%** | Classic "buy the rumor, sell the news" inversion |

The bearish accuracy at 72% with n=18 is the most interesting early result — the model is meaningfully better at identifying downside risk than upside. The earnings inversion (15.8%) is a textbook "sell the news" effect — worth inverting as a strategy signal rather than discarding.

Avg abnormal return (signal return minus pre-event T-2→T0 drift): **+0.13%** — the signal adds marginal positive value above trend.

Cost: **$4.71 total · $0.0062 per signal** using Claude Haiku 4.5 with prompt caching.

Full eval wave completes Sep 18 (637 signals still in the T+5 window).

---

## 🧠 How It Works

**LangGraph chain** — two nodes: ticker resolver (Alpaca hint fast-path, or LLM → validate against universe) and reasoning node (structured output via tool call). Every call traced in Langfuse.

**Universe gate** — 100 curated tickers (S&P 500 megacaps, no utilities/REITs/commodity E&P). Signals outside the universe are rejected — no hallucinated tickers reach the DB.

**Cost tracking** — every LLM call writes to `extraction_attempts`, including rejections. Nothing is invisible in the spend report.

**Abnormal return** — T0→T5 raw return minus the T-2→T0 pre-event drift. Isolates the news effect from pre-existing momentum.

---

## 🛠️ Stack

FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16 + pgvector · LangGraph + Claude Haiku 4.5 · Langfuse (self-hosted) · APScheduler · yfinance · React + TypeScript + Vite · FastMCP

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

- **[`docs/stages.md`](docs/stages.md)** — how the project was built stage by stage
- **[`app/pipeline/`](app/pipeline/)** — LangGraph chain: nodes, state, runner, universe
- **[`app/eval/`](app/eval/)** — pricer, T0 anchor, 8-point curve, abnormal return
- **[`app/api/routes/`](app/api/routes/)** — FastAPI endpoints
- **[`dashboard/src/`](dashboard/src/)** — React sections mapped to pipeline stages
- **[`CLAUDE.md`](CLAUDE.md)** — full architecture reference
