#!/bin/bash
# Uno Studio connector — install / reinstall / upgrade / rollback for Claude Code (macOS).
#   bash install.sh                    install, or upgrade to the newest tagged version
#   bash install.sh --version v1.0.0   install exactly this version
#   bash install.sh --rollback         go back to the version that was installed before
#   bash install.sh --source <git url> (testing) use another copy of this repository
# Changes only Claude Code's plugin list (marketplace "uno-studio", plugin "uno-studio@uno-studio") and the folder
# ~/.uno-studio-connector (downloaded versions). Before any change it backs up Claude Code's settings and plugin lists.
# Never removes other MCP servers or plugins, never touches Uno projects or media, never updates by itself.
set -euo pipefail
SRC="https://github.com/reensstudio1/uno-studio-connector.git"; REF=""; ROLLBACK=""
while [ $# -gt 0 ]; do case "$1" in
  --version) REF="$2"; shift 2;;
  --source) SRC="$2"; shift 2;;
  --rollback) ROLLBACK=1; shift;;
  *) echo "unknown option: $1"; exit 2;;
esac; done
CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"; HOMEDIR="$HOME/.uno-studio-connector"; mkdir -p "$HOMEDIR/releases"
say(){ printf '%s\n' "$*"; }

# 1. תלויות
command -v claude >/dev/null 2>&1 || { say "✗ Claude Code (claude) is not installed — install it first, then run this again."; exit 1; }
command -v python3 >/dev/null 2>&1 || { say "✗ python3 is missing — run: xcode-select --install"; exit 1; }
command -v git >/dev/null 2>&1 || { say "✗ git is missing — run: xcode-select --install"; exit 1; }
say "✓ $(claude --version 2>/dev/null | head -1) · $(python3 --version 2>&1) · git"

# 2. איזו גרסה
if [ -n "$ROLLBACK" ]; then
  [ -f "$HOMEDIR/previous" ] || { say "✗ no previous version recorded — nothing to roll back to"; exit 1; }
  REF="$(cat "$HOMEDIR/previous")"
elif [ -z "$REF" ]; then
  REF="$(git ls-remote --tags --refs "$SRC" 'v*' 2>/dev/null | sed 's#.*refs/tags/##' | sort -V | tail -1)"
  [ -n "$REF" ] || { say "✗ could not read versions from $SRC (offline?)"; exit 1; }
fi
CUR="$(cat "$HOMEDIR/current" 2>/dev/null || true)"
say "→ version $REF${CUR:+ (installed now: $CUR)}"

# 3. הורדת הגרסה (פעם אחת לכל גרסה)
DEST="$HOMEDIR/releases/$REF"
if [ ! -f "$DEST/.claude-plugin/marketplace.json" ]; then
  rm -rf "$DEST.tmp"; git clone -q --depth 1 --branch "$REF" "$SRC" "$DEST.tmp" && mv "$DEST.tmp" "$DEST"
fi

# 4. גיבוי לפני שינוי
B="$CFG/backups/uno-connector-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$B"
for f in "$CFG/settings.json" "$CFG/plugins/known_marketplaces.json" "$CFG/plugins/installed_plugins.json"; do [ -f "$f" ] && cp -p "$f" "$B/" || true; done
say "✓ backup: $B"

# 5. רישום ב-Claude Code (חוזר בבטחה: אם כבר מותקן — מוחלף לגרסה המבוקשת, שאר החיבורים לא נוגעים)
if claude plugin marketplace list 2>/dev/null | grep -q "uno-studio"; then
  claude plugin uninstall uno-studio@uno-studio >/dev/null 2>&1 || true
  claude plugin marketplace remove uno-studio >/dev/null 2>&1 || true
fi
claude plugin marketplace add "$DEST"
claude plugin install uno-studio@uno-studio
[ "$CUR" != "$REF" ] && [ -n "$CUR" ] && echo "$CUR" > "$HOMEDIR/previous"
echo "$REF" > "$HOMEDIR/current"

# 6. בדיקה
say ""; python3 "$DEST/plugins/uno-studio/connector/uno_connector.py" --where || true
claude mcp list 2>/dev/null | grep -i "uno-studio" || true
say "done ($REF). Restart Claude Code, type /mcp and check that uno-studio is connected."
