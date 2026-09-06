---
allowed-tools: Bash(psql *), Bash(python *), Read
argument-hint: <langfuse_trace_id or signal_id>
description: Look up a signal's Langfuse trace and summarize what the LLM did
---

## Context

- Langfuse host: !`grep LANGFUSE_HOST .env 2>/dev/null || echo "http://localhost:3000"`

## Task

Given $ARGUMENTS (either a `langfuse_trace_id` string or a `signal_id` integer), look up the signal and summarize the trace.

If $ARGUMENTS is numeric, fetch the trace ID from the DB first:
```
python -c "
import asyncio
from app.db.session import get_session
from app.db.models import Signal
from sqlalchemy import select

async def main():
    async with get_session() as s:
        r = await s.execute(select(Signal).where(Signal.id == $ARGUMENTS))
        sig = r.scalar_one_or_none()
        if sig:
            print(f'ticker={sig.ticker} direction={sig.direction} confidence={sig.confidence}')
            print(f'trace_id={sig.langfuse_trace_id}')
            print(f'cost_usd={sig.cost_usd}')
        else:
            print('Signal not found')
asyncio.run(main())
"
```

Then open the Langfuse trace URL:
```
{LANGFUSE_HOST}/trace/{trace_id}
```

Summarize:
- What the model was asked at each node (extract → resolve → generate)
- What it returned at each node
- Token usage and cost per node
- Any errors or unexpected outputs
- Whether the ticker was validated or rejected

This is useful for debugging signals that seem wrong — the trace shows exactly what the model saw and decided.
