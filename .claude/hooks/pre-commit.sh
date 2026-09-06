#!/bin/bash
# Hook: PreToolUse — matcher: Bash
# Runs ruff and mypy before any git commit. Exit 2 blocks the commit.

# Only intercept git commit commands
if ! echo "$CLAUDE_TOOL_INPUT" | grep -q '"git commit"'; then
  exit 0
fi

echo "Running pre-commit checks..."

# Ruff lint
ruff check . 2>&1
if [ $? -ne 0 ]; then
  echo "❌ ruff check failed — fix lint errors before committing." >&2
  exit 2
fi

# Ruff format
ruff format --check . 2>&1
if [ $? -ne 0 ]; then
  echo "❌ ruff format check failed — run 'ruff format .' to fix." >&2
  exit 2
fi

# Mypy
mypy app 2>&1
if [ $? -ne 0 ]; then
  echo "❌ mypy failed — fix type errors before committing." >&2
  exit 2
fi

echo "✅ Pre-commit checks passed."
exit 0
