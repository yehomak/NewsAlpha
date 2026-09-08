---
allowed-tools: Bash(python *), Bash(pytest *), Bash(psql *), Bash(ruff *), Bash(docker *), Bash(grep *), Bash(git *), Read
description: Structured 6-phase debug loop for pipeline failures — no hypothesis without a red-capable loop first
argument-hint: <what is broken>
---

A discipline for hard bugs. Skip phases only when explicitly justified.

Read `CLAUDE.md` to orient: pipeline is news → ingest → events → LangGraph chain → signals → eval_results.

**Redact every secret before showing output.** Write `<REDACTED>` in place of API keys, DB passwords, tokens.

## Phase 1: Build a feedback loop

This is the skill. No hypothesis until you have a tight, red-capable, deterministic, agent-runnable loop.

Ways to construct one for this project (in order):
1. **Failing pytest test** — `pytest tests/path_to_test.py -x`
2. **Direct async function call** — minimal Python script invoking the broken function with a fixture
3. **DB query** — `psql $DATABASE_URL -c "..."` to verify state before/after
4. **Docker log grep** — `docker compose logs app 2>&1 | grep ERROR`
5. **Single pipeline step replay** — run just the failing LangGraph node in isolation

The loop is done when you can name one command that has already been run, goes red on this bug, and is deterministic.

## Phase 2: Reproduce + minimise

Run the loop. Confirm it reproduces the user's exact symptom. Shrink the repro to the smallest scenario that still goes red — cut data, callers, pipeline steps one at a time.

## Phase 3: Hypothesise

Generate 3–5 ranked falsifiable hypotheses before testing any. Show the list to the user. Each must state: "If X is the cause, then changing Y will make the bug disappear."

Common sources in this codebase:
- Async session lifecycle (missing `await`, session closed early)
- Pydantic v2 validation failure on LLM output
- Ticker resolver rejecting valid tickers (whitelist miss)
- LangGraph state mutation (node returning full state instead of dict slice)
- Langfuse trace not started before LLM call
- DB enum mismatch between SQLAlchemy model and migration

## Phase 4: Instrument

One variable at a time. Tag every debug log with `[DEBUG-<4-char-id>]` for easy cleanup. For async bugs, add `structlog` calls at await boundaries.

## Phase 5: Fix + regression test

Write the regression test before the fix if a correct seam exists. Turn the minimised repro into a failing pytest. Watch it fail. Apply fix. Watch it pass. Re-run Phase 1 loop.

## Phase 6: Cleanup

- [ ] Original repro no longer reproduces
- [ ] `grep DEBUG-` returns nothing
- [ ] Throwaway scripts deleted
- [ ] Root cause stated in commit message
