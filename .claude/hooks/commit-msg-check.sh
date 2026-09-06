#!/bin/bash
# Hook: PreToolUse — matcher: Bash
# Validates conventional commit format on any git commit -m call.
# Exit 2 blocks the commit with the reason.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null)

# Only intercept git commit -m commands
if ! echo "$COMMAND" | grep -qE "git commit.*-m"; then
  exit 0
fi

# Extract the commit message from the -m argument
MSG=$(echo "$COMMAND" | sed -n 's/.*-m[[:space:]]*["\x27]\(.*\)["\x27].*/\1/p' | head -1)
[ -z "$MSG" ] && exit 0

# Validate conventional commit prefix
VALID_TYPES="feat|fix|refactor|test|docs|chore|db|perf|ci|style"
if ! echo "$MSG" | grep -qE "^($VALID_TYPES)(\(.+\))?!?: .{1,72}"; then
  echo "❌ Commit message does not follow conventional commits format." >&2
  echo "   Expected: type(scope): description" >&2
  echo "   Valid types: feat, fix, refactor, test, docs, chore, db, perf, ci, style" >&2
  echo "   Got: $MSG" >&2
  exit 2
fi

exit 0
