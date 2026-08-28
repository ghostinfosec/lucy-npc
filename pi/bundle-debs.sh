#!/usr/bin/env bash
# Laptop-side: bundle NetworkManager debs onto the SD for offline portal first boot.
# Side effects: writes .deb files to OUT_DIR; downloads from ftp.debian.org.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:?usage: bundle-debs.sh OUT_DIR}"

if [[ -f "$OUT/.complete" ]]; then
  echo "debs bundle already present in ${OUT}"
  exit 0
fi

mkdir -p "$OUT"
python3 "$ROOT/bundle_debs.py" "$OUT"
touch "$OUT/.complete"
echo "debs bundle ready: $(find "$OUT" -name '*.deb' | wc -l | tr -d ' ') packages"
