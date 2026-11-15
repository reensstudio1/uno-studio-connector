#!/bin/bash
# Install Uno as a local Claude Desktop MCP connector, not a plugin.
set -euo pipefail
SRC=https://github.com/reensstudio1/uno-studio-connector.git
REF=""; ROLLBACK=""
while [ $# -gt 0 ]; do
 case "$1" in
 --version) REF="$2"; shift 2;;
 --source) SRC="$2"; shift 2;;
 --rollback) ROLLBACK=1; shift;;
 *) echo "Unknown argument: $1" >&2; exit 2;;
 esac
done
[ "$(uname -s)" = Darwin ] || { echo 'macOS only'; exit 1; }
command -v python3 >/dev/null || { echo 'Python 3 required'; exit 1; }
command -v git >/dev/null || { echo 'Git required'; exit 1; }
BASE="$HOME/.uno-studio-connector"
if [ -n "$ROLLBACK" ]; then
 [ -f "$BASE/previous-desktop" ] || { echo 'No previous Desktop version'; exit 1; }
 REF="$(cat "$BASE/previous-desktop")"
elif [ -z "$REF" ]; then
 REF="$(git ls-remote --tags --refs "$SRC" 'v*' | sed 's#.*refs/tags/##' | python3 -c 'import re,sys; a=[s.strip() for s in sys.stdin if re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+\n?",s)]; print(max(a,key=lambda s:tuple(map(int,s[1:].split(".")))) if a else "")')"
fi
[[ "$REF" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Invalid release'; exit 1; }
mkdir -p "$BASE/releases"
DEST="$BASE/releases/$REF"
if [ ! -d "$DEST" ]; then
 STAGE="$(mktemp -d "$BASE/releases/.download.XXXXXX")"
 trap 'rm -rf "$STAGE"' EXIT
 git -c advice.detachedHead=false clone -q --depth 1 --branch "$REF" "$SRC" "$STAGE/repo"
 mv "$STAGE/repo" "$DEST"
fi
[ -f "$DEST/install_desktop.py" ] || { echo 'This release predates Desktop MCP; use v1.1.0 or later.'; exit 1; }
python3 "$DEST/install_desktop.py" --release "$REF"
