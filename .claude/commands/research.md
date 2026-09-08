---
allowed-tools: Bash(curl *), Bash(grep *), Read
description: Investigate a question against primary sources and save findings as a Markdown file
argument-hint: <question to research>
---

Spin up a background agent to research the question while you keep working.

The background agent must:
1. Investigate against **primary sources only** — official docs, source code, specs, first-party changelogs. Not blog posts or secondary write-ups. Relevant primary sources for this project:
   - Anthropic docs + SDK changelog (API changes, model names, pricing)
   - LangGraph source + changelog (node patterns, StateGraph API)
   - Langfuse docs (trace/generation API, SDK version compat)
   - SQLAlchemy 2.0 async docs (session patterns, mapped_column)
   - yfinance source (price fetch behavior, market hours handling)
   - pandas_market_calendars docs (trading day calculation)

2. Follow every claim back to the source that owns it. Cite each claim with a URL or file+line.

3. Save findings to `docs/research/<slug>.md` (create `docs/research/` if it doesn't exist).

4. Include at the top: question asked, date, sources consulted, answer summary (3–5 sentences), then full findings.

Keep working on the current task while the background agent reads. Do not wait for it to finish.
