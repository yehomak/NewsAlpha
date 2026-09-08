---
description: Stress-test a plan or design decision with a structured interview before building
argument-hint: <plan or decision to grill>
---

Interview the user relentlessly about their plan until you reach a shared understanding. Map this as a design tree: every decision branches into the decisions that hang off it.

Work the tree in rounds. The frontier is every decision whose prerequisites are already settled — the questions you can ask now without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for answers before the next round.

Format each round like:

```
❓ **Q1** - **<question title>**: <question body>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body>

➡️ <your recommended answer>
```

Finding facts is your job, never the user's. When a frontier question needs a fact from the codebase (table schema, existing pipeline code, config values), read the relevant files — don't ask the user for anything you could look up yourself.

For butterfly-effect, frontier questions typically branch across: which stage this affects, whether it changes the eval harness, LangGraph node impact, DB schema changes needed, cost implications, and whether T+5 accuracy measurement is affected.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act until the user confirms shared understanding.
