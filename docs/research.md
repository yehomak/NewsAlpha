# Niche Research

## Does news actually predict stock movement?

**Yes — weakly, for a narrow window, with documented failure modes to segment around.**

Realistic accuracy targets (LLM-era, 2024–2026 research):
- **53–60% T+5 directional accuracy** is honest and defensible out-of-sample
- **55–65% T+1–T+3** is achievable; signal decays as market absorbs it
- Anything above 60% at meaningful sample size (200+ signals) should trigger a look-ahead bias audit before claiming it
- Combined models (sentiment + price features): up to 86–89% in academic papers — almost always in-sample and inflated; do not cite these numbers

Academic sources: arXiv 2412.19245 (LLM sentiment trading, 965k articles 2010–2023), arXiv 2412.10823 (FinGPT benchmark, 55%→63% with news clustering)

News predicts *volatility* more reliably than *direction* — worth a sentence in the README. Shows domain awareness.

**Speed window by market cap** (this defines where the project has realistic edge):
- Large-cap (S&P 500): priced in within 15 min – 2 hr by algorithmic traders
- Mid-cap: 2 – 12 hr absorption window
- Small-cap: hours to 2 days — the realistic target for this pipeline

The pipeline polls hourly. It competes against retail readers (hours to days), not HFTs (milliseconds). The edge is in extracting structured company+direction from narratives that don't fire a Bloomberg terminal alert automatically — supply chain disruption, exec departure, product recall.

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

**Look-ahead bias — top risk for LLM-based pipelines (critical)**
LLM backtests are contaminated in two ways: (1) the model was trained on data including outcomes; (2) Claude trained past 2021 may *recall* a 2022 earnings headline's stock reaction rather than reasoning from the text. Papers: arXiv 2601.13770, arXiv 2512.23847. This project is immune because signals are extracted at ingest time — before T+5 is known — and the eval job only reads price data after the window closes. Cite arXiv 2309.17322 if asked about methodology.

**Earnings announcement inversion ("buy the rumor, sell the news")**
Pre-announcement informed trading front-runs the actual announcement, so the stock often moves *opposite* to the news sentiment on and just after the earnings date. The `event_type = earnings` segment will likely underperform or invert in the eval. Segment separately and do not average with analyst upgrades or product launches. Documented empirically in arXiv 2608.14014.

**Market hours**
After-hours news affects the *next* open, not the same-day close. T+5 price fetch must use next trading day's open as the reference point, or ground truth is wrong.

**Macro events — not worth extracting**
Fed decisions, CPI prints, jobs reports: priced in by algorithmic traders within seconds. These swamp company-specific signals. Either filter macro `event_type` out of the LLM pipeline entirely, or report it separately and note the near-random accuracy.

**Sector sensitivity**
Sentiment predicts tech and biotech better than utilities or consumer staples. Track accuracy by sector — makes results richer and more defensible.

**Stale news**
Skip stories older than 7 days at ingest — they have no T+5 signal value for a live pipeline.

**RSS body text**
feedparser body is truncated (150–300 chars). Stage 3 LLM prompts must be designed to work on headline + 1-sentence summary. Trafilatura can fetch full body but adds latency and blocking risk. This is a real constraint, not an edge case.

## Eval schema additions

`event_type` on Signal: `earnings | product_launch | macro | general` — already in schema.

`price_t1` + `correct_t1` on EvalResult (add in Stage 4): T+1 accuracy as a secondary metric alongside T+5. Shows the signal decay curve — T+1 will be higher, which confirms the signal exists and decays, rather than being random noise. More interesting interview story than a single number.

`coverage_count` on Event (add in Stage 2): how many outlets published equivalent stories. High count = market-moving story. Use as a signal weight multiplier in Stage 4 eval.

## Open-source landscape (updated)

| Project | Approach | Eval harness | Ticker validation |
|---|---|---|---|
| FinGPT (AI4Finance, ~14k ⭐) | Fine-tuned FinBERT batch sentiment | None | None |
| FinRobot | LLM agents for finance tasks | None | None |
| butterfly-effect | LangGraph + Claude + Pydantic validation | Ground-truth T+5 | Whitelist guardrail |

No open-source project combines reasoning LLMs (not classifiers), structured Pydantic output, ticker whitelist validation, Langfuse tracing, and a ground-truth eval harness. All of them are missing at least one of these.

The FinGPT DataSource layer pattern is worth borrowing: they normalize heterogeneous sources into one event schema before any LLM processing — which is exactly the Stage 2 → Stage 3 separation already planned.
