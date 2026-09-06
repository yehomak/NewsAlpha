#!/bin/bash
# Hook: PostToolUse — matcher: Write
# Scans newly written files for hardcoded secrets before they land on disk.
# Exit 2 surfaces a warning — the write already happened, so this is advisory.

FILE=$(echo "$CLAUDE_TOOL_INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)

[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0

# Skip non-text files and test fixtures
case "$FILE" in
  *.png|*.jpg|*.gif|*.ico|*.db|*.pyc) exit 0 ;;
  */tests/*|*/.git/*) exit 0 ;;
esac

FOUND=0

check() {
  local pattern="$1"
  local label="$2"
  if grep -qE "$pattern" "$FILE" 2>/dev/null; then
    echo "⚠️  Possible $label detected in $FILE" >&2
    FOUND=1
  fi
}

check 'sk-ant-[A-Za-z0-9_-]{20,}' "Anthropic API key"
check 'sk-[A-Za-z0-9]{20,}' "OpenAI API key"
check 'ghp_[A-Za-z0-9]{36}' "GitHub personal access token"
check 'ANTHROPIC_API_KEY\s*=\s*["\x27]sk-' "hardcoded ANTHROPIC_API_KEY value"
check 'password\s*=\s*["\x27][^"\x27]{8,}' "hardcoded password"
check 'secret\s*=\s*["\x27][^"\x27]{8,}' "hardcoded secret"

if [ $FOUND -eq 1 ]; then
  echo "Review the file and use environment variables instead. Check .env.example for the right pattern." >&2
  exit 2
fi

exit 0
