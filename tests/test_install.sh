#!/bin/bash
# Local Desktop route. Usage: bash tests/test_install.sh <git URL> <isolated Uno fixture>
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$HERE/tests/test_roundtrip.py" "$1" "$2"
