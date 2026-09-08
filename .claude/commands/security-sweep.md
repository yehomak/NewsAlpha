---
allowed-tools: Bash(grep *), Bash(ruff *), Bash(git *), Read
description: OWASP Top 10 + LLM-specific vulnerability scan via parallel sub-agents
---

Two parallel sub-agents: one for OWASP, one for LLM-specific issues. Report Critical / High / Medium with file+line+remediation.

## OWASP sub-agent — scan for:

1. **Injection** — SQL injection via raw string concat in SQLAlchemy queries; command injection in any `subprocess` or `Bash` call
2. **Broken auth** — missing auth on FastAPI routes, API keys in code or logs, weak token validation
3. **Sensitive data exposure** — LLM reasoning logged with PII, tickers/signals returned without auth, cost_usd visible in public responses
4. **Security misconfiguration** — debug mode in prod, overly permissive CORS (`allow_origins=["*"]`), default DB credentials
5. **Vulnerable dependencies** — flag any pinned version in pyproject.toml with a known CVE (grep against `pip-audit` output if available)
6. **Logging sensitive data** — API keys, DB URLs, or LLM prompts in structlog output

## LLM-specific sub-agent — scan for:

1. **Prompt injection** — user-supplied content inserted directly into LLM prompts without sanitization
2. **Data exfiltration** — LLM output used to construct file paths, shell commands, or DB queries
3. **Over-permissive tool grants** — Claude Code hooks or agents with broader `allowed-tools` than needed
4. **Unbounded LLM cost** — no per-request cost cap, no daily spend guard, no rate limiting on `/signals/run`
5. **Ticker resolver bypass** — any path that writes a signal to DB without going through the whitelist validator
6. **Look-ahead bias** — any eval code that reads future price data before the signal's `created_at` timestamp

## Output format

```
## Critical
- [file:line] Description — Remediation

## High
- [file:line] Description — Remediation

## Medium
- [file:line] Description — Remediation
```
