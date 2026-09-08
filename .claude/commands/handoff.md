---
description: Compact the current conversation into a handoff document for the next session
argument-hint: <focus of the next session, e.g. "Stage 4 eval harness">
disable-model-invocation: true
---

Write a handoff document for the next session. Save to `/tmp/butterfly-effect-handoff-<YYYY-MM-DD>.md`.

Include:

## Current state
What stage are we on, what was just completed, what's in progress.

## Decisions made this session
Key choices and their reasons — things that would need re-deriving without this doc.

## Next session focus
If the user passed arguments, use them. Otherwise infer from conversation state.

## Suggested skills
Which commands/agents to invoke first in the next session (e.g. `/grilling` before starting a new stage, `signal-dev` agent for LangGraph work).

## Open questions
Anything unresolved or deferred.

## Do not duplicate
Do not restate content already in commits, CLAUDE.md, or docs/stages.md — reference them by path instead.

Redact any API keys, DB passwords, or other secrets. They must not appear in the handoff document.
