---
allowed-tools: Read, Bash(alembic *), Bash(python *), Bash(grep *)
argument-hint: [migration description]
description: Generate an Alembic migration from model changes and apply it
---

## Context

- Current models: !`grep -n "class.*Base" app/db/models.py`
- Latest migration: !`ls alembic/versions/ | sort | tail -3`
- Current DB revision: !`alembic current 2>&1`

## Task

Generate a new Alembic migration for the changes described in $ARGUMENTS (or infer from recent model edits).

Steps:
1. Read `app/db/models.py` to understand what changed
2. Read the latest file in `alembic/versions/` to get the current `revision` ID for `down_revision`
3. Write the new migration file to `alembic/versions/NNN_description.py` where NNN is the next number
4. Ensure `upgrade()` and `downgrade()` are both complete — never leave `downgrade()` as `pass`
5. Run `alembic upgrade head` to apply
6. Verify with `alembic current` — should show the new revision

## Safety checks before applying

- If the migration drops a column or table, state explicitly what data will be lost
- If the migration changes a NOT NULL constraint on an existing column, confirm a default is set
- If the migration renames an enum, flag that PostgreSQL requires a multi-step approach
- Never run `alembic downgrade base` — that drops everything

## After applying

Run `alembic check` to confirm no further autogenerate changes are detected.
