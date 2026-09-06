# Niche Research

## Does news actually predict stock movement?

**Yes, with caveats.**

- Academic studies: 63–72% directional accuracy in controlled settings
- One study: 68.5% for tech/finance sectors at short horizons
- Combined models (sentiment + price features): up to 86–89% — but that's in-sample and inflated
- Realistic out-of-sample target: **55–65% at T+5** is credible and honest
- News predicts *volatility* more reliably than *direction* — important nuance, worth stating in README
- T+5 days is the right horizon: captures drift, not the initial spike (which is priced in within minutes)

## Commercial landscape

| Product | What they do | Price |
|---|---|---|
| LSEG MarketPsych | NLP on news + social → 10+ perceptual dimensions per asset. Bond "Fear" metric: 22–30% out-of-sample R². | Institutional |
| RavenPack | Real-time event-driven sentiment scores. Used by quant hedge funds. | $50k+/yr |
| Accern | NLP platform for trading signals from news/forums. | Institutional |
| Bloomberg BNEF Sentiment | Bundled in Bloomberg Terminal. | $24k+/yr terminal |

Key point: none of them publish live accuracy stats publicly. A portfolio project with real measured numbers is credible by comparison.

## Open-source landscape (what exists and what it misses)

| Project | What it does | What it misses |
|---|---|---|
| FinGPT (AI4Finance) | Fine-tuned LLMs on financial news/tweets for sentiment | No eval harness, no observability, raw text not structured |
| Tickermind (McMaster 2025) | Local LLM + real-time scanner | No ground-truth eval, no cost tracking, no API |
| LLM-Enhanced Trading | Sentiment extraction + signal generation | Notebooks only, no persistence |
| llm-financial-sentiment-analysis | NLP pipeline → prediction | No dedup, no ticker resolver, Jupyter-only |
| stock-analysis-with-llm | LLM reasoning + financial data | No eval against actual price movement |

**Universal gaps:** no ground-truth accuracy measurement, no observability/tracing, no structured outputs, no deduplication, no production API. This project addresses all of them.

## Known pitfalls

**Look-ahead bias (critical)**
LLM backtests are contaminated — the model was trained on data that includes the outcomes. A 2026 arxiv paper (2309.17322) specifically addresses this. This project is immune because it's a forward-only real-time pipeline. State this explicitly in the README.

**Market hours**
After-hours news affects the *next* open, not the same-day close. T+5 price fetch must use the next trading day's open as the reference point, or ground truth is wrong.

**"Buy the rumor, sell the news"**
Earnings-day signals often invert post-announcement. Segment eval by `event_type` (earnings / product_launch / macro / general) or accuracy numbers will look confusing and unreliable.

**Sector sensitivity**
Sentiment predicts tech stocks better than utilities or consumer staples. Track accuracy by sector in the eval breakdown — makes results richer and more defensible in interviews.

**Anonymization effect**
Research found anonymized headlines outperform originals in-sample, because the LLM's prior knowledge of a company biases its sentiment assessment. Worth a note in the README.

**Stale news**
Markets price in news within minutes. A story published at 9am is largely priced in by 9:05am. T+5 days captures the slower drift, which is more reliable.

## Eval schema additions (from research)

Add `event_type` field to signals: `earnings | product_launch | macro | general`
- Takes ~30 min to implement
- Makes eval story significantly stronger
- Lets you explain the earnings inversion effect in interviews
