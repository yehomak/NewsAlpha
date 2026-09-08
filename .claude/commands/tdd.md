---
allowed-tools: Bash(pytest *), Bash(ruff *), Bash(mypy *), Read, Edit, Write
description: Test-driven development — red-green-refactor with seam-first thinking
argument-hint: <feature or bug to implement test-first>
---

Red-green-refactor discipline. Tests verify behavior through public interfaces, not implementation details.

## Before writing any test

Agree seams first. For butterfly-effect, valid seams are:
- `app/ingest/` — ingest functions (input: feed URL or API response fixture, output: Event rows in DB)
- `app/pipeline/` — LangGraph chain (input: Event, output: Signal)
- `app/eval/` — eval job (input: Signal with elapsed T+5, output: EvalResult)
- `app/api/` — FastAPI endpoints (input: HTTP request via `httpx.AsyncClient`, output: response JSON)

Invalid seams: internal LangGraph nodes, private helper functions, DB session internals.

## The loop

1. **Write a failing test** at the agreed seam. Run it: `pytest tests/<path>.py::test_<name> -x`. Watch it fail.
2. **Write the minimum code** to make it pass. No gold-plating.
3. **Refactor** — clean up without changing behavior. Re-run test after each change.
4. **Repeat** for the next behavior.

## Test conventions for this project

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_<behavior>(db_session: AsyncSession):
    # arrange — use real DB session, not mocks
    # act
    # assert
```

- Always use `pytest-asyncio` with `asyncio_mode = "auto"` (already in pyproject.toml)
- Never mock the DB — use the test session from the fixture
- Never mock the LangGraph chain for integration tests — test through the real chain with a stubbed Claude response
- Use `httpx.AsyncClient(app=app, base_url="http://test")` for API endpoint tests

## Done when

- All new behavior covered at the agreed seams
- `pytest` green
- `mypy app` clean
- No test skips or xfails added
