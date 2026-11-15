#!/bin/bash
# Uno Studio connector — install / reinstall / upgrade / rollback for Claude Code (macOS).
#   bash install.sh                      install or update to the latest version
#   bash install.sh --version v1.0.0     install exactly this tagged version (also the way to roll back)
#   bash install.sh --source <git url or folder>   (testing) use another copy of this repository
# What it changes: only Claude Code's plugin list (marketplace "uno-studio", plugin "uno-studio@uno-studio").
# Before any change it backs up Claude Code's settings and plugin lists to ~/.claude/backups/uno-connector-<time>/.
# It never removes other MCP servers or plugins, and never touches Uno projects or media.
set -euo pipefail
REPO="https://github.com/reensstudio1/uno-studio-connector.git"
SRC="$REPO"; REF=""
while [ $# -gt 0 ]; do case "$1" in
  --version) REF="$2"; shift 2;;
  --source) SRC="$2"; shift 2;;
  *) echo "unknown option: $1"; exit 2;;
esac; done
CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
say(){ printf '%s\n' "$*"; }

# 1. תלויות
command -v claude >/dev/null 2>&1 || { say "✗ Claude Code (claude) is not installed — install it first: https://claude.com/claude-code"; exit 1; }
command -v python3 >/dev/null 2>&1 || { say "✗ python3 is missing — run: xcode-select --install"; exit 1; }
say "✓ Claude Code $(claude --version 2>/dev/null | head -1)"
say "✓ $(python3 --version 2>&1)"

# 2. גיבוי לפני שינוי
B="$CFG/backups/uno-connector-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$B"
for f in "$CFG/settings.json" "$CFG/plugins/known_marketplaces.json" "$CFG/plugins/installed_plugins.json"; do
  [ -f "$f" ] && cp -p "$f" "$B/" || true
done
say "✓ backup: $B"

# 3. מקור (עם גרסה אם ביקשו)
SOURCE="$SRC"; [ -n "$REF" ] && SOURCE="$SRC#$REF"

# 4. הוספה / עדכון — חוזר בבטחה
if claude plugin marketplace list 2>/dev/null | grep -q "uno-studio"; then
  if [ -n "$REF" ] || [ "$SRC" != "$REPO" ]; then
    claude plugin marketplace remove uno-studio >/dev/null
    claude plugin marketplace add "$SOURCE"
  else
    claude plugin marketplace update uno-studio
  fi
else
  claude plugin marketplace add "$SOURCE"
fi
if claude plugin list 2>/dev/null | grep -q "uno-studio@uno-studio"; then
  claude plugin update uno-studio@uno-studio || true
else
  claude plugin install uno-studio@uno-studio
fi

# 5. בדיקה
PLUG=$(ls -d "$CFG"/plugins/cache/uno-studio/uno-studio/*/ 2>/dev/null | tail -1)
[ -n "$PLUG" ] && python3 "$PLUG/connector/uno_connector.py" --where || true
say ""
claude mcp list 2>/dev/null | grep -i "uno-studio" || say "(restart Claude Code, then type /mcp — you should see plugin:uno-studio:uno-studio)"
say "done. Restart Claude Code, type /mcp and check that uno-studio is connected."
