#!/usr/bin/env bash
# Local stand-in for CI. No GitHub, no Pi, no live internet required.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -e ".[dev]" -q
.venv/bin/pytest -q

DRESS="${LUCY_DRESS:-$ROOT/.dress}"
rm -rf "$DRESS"
mkdir -p "$DRESS/src" "$DRESS/slots" "$DRESS/etc" "$DRESS/logs"
cp VERSION "$DRESS/src/VERSION"
.venv/bin/python - <<PY
from pathlib import Path
from lucy.update import sha256_file
root = Path("$DRESS/src")
digest = sha256_file(root / "VERSION")
(root / "SHA256SUMS").write_text(f"{digest}  VERSION\n", encoding="utf-8")
PY
export LUCY_SLOT_ROOT="$DRESS/slots"
export LUCY_CURRENT_LINK="$DRESS/current"
export LUCY_STATE_DIR="$DRESS/etc"
.venv/bin/lucy-update --from-dir "$DRESS/src" --tag v0.1.0-dress
test -L "$DRESS/current"
test "$(tr -d '[:space:]' < "$DRESS/current/VERSION")" = "0.1.0"

.venv/bin/lucy-daemon --engine local --once \
  --persona "$ROOT/data/personas/wool.json" \
  --log-dir "$DRESS/logs" \
  --host 127.0.0.1 \
  --port 8798

if LUCY_STATUS_TOKEN= .venv/bin/lucy-daemon --host 0.0.0.0 --port 8797 --once; then
  echo "expected LAN bind without token to fail" >&2
  exit 1
fi

echo "verify ok"
