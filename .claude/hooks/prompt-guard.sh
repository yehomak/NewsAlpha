#!/bin/bash
# Hook: UserPromptSubmit
# Blocks prompts containing destructive DB operations without an explicit confirmation phrase.
# Reads the prompt from stdin as JSON: {"prompt": "..."}

PROMPT=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prompt',''))" 2>/dev/null)

CONFIRMED=false
if echo "$PROMPT" | grep -qiE "i confirm|yes.*drop|confirmed.*delete|force.*reset"; then
  CONFIRMED=true
fi

if [ "$CONFIRMED" = false ]; then
  if echo "$PROMPT" | grep -qiE "drop table|alembic downgrade base|delete from signals|delete from eval_results|truncate"; then
    echo "Blocked: destructive DB operation detected. Add 'I confirm' to your prompt if you intend this." >&2
    exit 2
  fi
fi

exit 0
