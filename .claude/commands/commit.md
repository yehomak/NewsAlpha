---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git diff:*), Bash(ruff check:*), Bash(ruff format:*)
argument-hint: [optional message]
description: Lint, then create a conventional commit
---

## Pre-flight

Run linting first and surface any issues:

```
!`ruff check . 2>&1 | head -20`
```

If ruff reports errors, fix them before committing. Format issues are auto-fixable with `ruff format .`.

## Context

- Status: !`git status`
- Staged diff: !`git diff --cached`
- Unstaged diff: !`git diff`
- Branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -5`

## Task

If $ARGUMENTS is provided, use it as the commit message. Otherwise analyze the diff and write one.

Conventional commit format — pick the right type:
- `feat:` new capability added
- `fix:` bug corrected
- `refactor:` restructured without behavior change
- `test:` tests added or updated
- `docs:` documentation only
- `chore:` tooling, deps, config
- `db:` schema migration or model change

Include a short body (1-2 lines) explaining **why** when the reason isn't obvious from the diff.

Branch naming reminder: if working on a new topic, branch should be `agent/<topic>-<desc>` before committing.
