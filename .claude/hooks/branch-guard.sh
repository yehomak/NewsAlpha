#!/usr/bin/env bash
CMD=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.command // ""')
echo "$CMD" | grep -q 'git push' || exit 0
BRANCH=$(git branch --show-current 2>/dev/null)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"Direct push to main blocked — use a feature branch and open a PR with /pr"}}' && exit 0
fi
exit 0
