---
allowed-tools: Bash(git *), Bash(ruff *), Bash(mypy *), Read
description: Two-axis code review — Standards vs Spec — via parallel sub-agents
argument-hint: <fixed point: branch name, commit SHA, or HEAD~N>
---

Two-axis review of the diff between HEAD and the fixed point the user supplied.

## Step 1: Pin the fixed point

Run `git diff <fixed-point>...HEAD` and `git log <fixed-point>..HEAD --oneline`. Confirm the diff is non-empty.

## Step 2: Spawn both sub-agents in parallel

**Standards sub-agent** — reviews against:
- Conventions in CLAUDE.md: async everywhere, Pydantic for LLM output, ticker resolver pattern, cost tracking on every LLM call, Langfuse tracing on every LLM call
- Ruff rules (E, F, I, UP, B) and mypy strict
- Fowler smell baseline: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Speculative Generality, Shotgun Surgery, Divergent Change
- Output: **Blocking** (CLAUDE.md violation or mypy error) / **Important** (smell) / **Minor** (style) with file+line+fix

**Spec sub-agent** — reviews against:
- The originating issue or stage spec in docs/stages.md
- Check: missing requirements, behavior not asked for (scope creep), requirements that look implemented but are wrong
- Output: each finding cites the spec line it maps to

## Step 3: Aggregate

Present findings under `## Standards` and `## Spec` headings. Do not merge or rerank across axes. End with: total findings per axis, worst issue per axis.
