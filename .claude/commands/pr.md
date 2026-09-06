---
allowed-tools: Bash(git *), Bash(ruff *), Bash(mypy *), Bash(pytest *), Bash(gh *)
argument-hint: [optional PR title]
description: Run checks, then open a pull request with a structured description
---

## Pre-flight checks

Run these in order and stop if any fail:

1. `ruff check .` — fix any lint errors before continuing
2. `ruff format --check .` — format check
3. `mypy app` — type check
4. `pytest` — all tests must pass

## Context

- Branch: !`git branch --show-current`
- Commits vs main: !`git log main..HEAD --oneline`
- Full diff: !`git diff main...HEAD --stat`

## Task

Create a PR using `gh pr create`. Use $ARGUMENTS as the title if provided, otherwise derive it from the commits.

The PR body must follow the project template structure:

```
## What

[1-3 bullets: what changed]

## Why

[1-2 sentences: motivation — which stage, what problem solved]

## Testing

- [ ] ruff + mypy pass
- [ ] pytest pass
- [ ] Docker build pass (if Dockerfile touched)
- [ ] Manual smoke test: [describe what you ran]

## Notes

[Anything a reviewer should know — tradeoffs, follow-ups, known issues]

---
AI-assisted: yes
Prompt context: [what was asked / which stage of CLAUDE.md this implements]
```

Keep the diff focused — one stage at a time per the CLAUDE.md build stages.
