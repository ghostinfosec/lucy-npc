#!/usr/bin/env bash
# First flash of a Lucy. Trust-on-first-use: this tree is the root.
# Auto-updates are OFF unless you pass --consent-auto-update (or answer yes on a TTY).
# Later slots go through lucy-update. Cosign is still not implemented; git pull is TOFU.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${LUCY_PREFIX:-/opt/lucy}"
STATE="${LUCY_STATE_DIR:-/etc/lucy}"
CONSENT=0
ORIGIN="${LUCY_UPDATE_ORIGIN:-}"

for arg in "$@"; do
  case "$arg" in
    --consent-auto-update|--yes|-y) CONSENT=1 ;;
    --origin=*) ORIGIN="${arg#--origin=}" ;;
  esac
done

if [[ -z "$ORIGIN" ]] && git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ORIGIN="$(git -C "$ROOT" remote get-url origin 2>/dev/null || true)"
fi

if [[ "$CONSENT" -eq 0 && -t 0 && -t 1 ]]; then
  echo "Auto-updates pull code from GitHub into ${PREFIX}. They never replace ${STATE} (persona/env)."
  echo "This is git TOFU — the same trust as the clone you just ran. Signed releases are not wired yet."
  read -r -p "Enable pull-only auto-updates? [y/N] " ans || ans=""
  if [[ "$ans" == [yY]* ]]; then
    CONSENT=1
  fi
fi

if [[ "$CONSENT" -eq 1 && -z "$ORIGIN" ]]; then
  echo "consent requested but no origin (set LUCY_UPDATE_ORIGIN=owner/repo or git remote). continuing with updates OFF." >&2
  CONSENT=0
fi

export DEBIAN_FRONTEND=noninteractive
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip git rsync ca-certificates
fi

id -u lucy >/dev/null 2>&1 || sudo useradd --system --home /var/lib/lucy --shell /usr/sbin/nologin lucy
sudo mkdir -p "$PREFIX/slots" "$PREFIX/logs" "$PREFIX/ms-playwright" /var/lib/lucy "$STATE"
sudo rsync -a --exclude '.venv' --exclude '.git' --exclude '.dress' \
  "$ROOT/" "$PREFIX/slots/v0.1.0/"
sudo ln -sfn "$PREFIX/slots/v0.1.0" "$PREFIX/current"
if [[ ! -f "$STATE/env" ]]; then
  sudo cp "$ROOT/.env.template" "$STATE/env"
  sudo sed -i 's|^LUCY_PERSONA=.*|LUCY_PERSONA=/etc/lucy/persona.json|' "$STATE/env"
  sudo sed -i 's|^LUCY_LOG_DIR=.*|LUCY_LOG_DIR=/opt/lucy/logs|' "$STATE/env"
  sudo sed -i 's|^PLAYWRIGHT_BROWSERS_PATH=.*|PLAYWRIGHT_BROWSERS_PATH=/opt/lucy/ms-playwright|' "$STATE/env" || true
fi
if [[ ! -f "$STATE/persona.json" ]]; then
  sudo cp "$ROOT/data/personas/wool.json" "$STATE/persona.json"
fi
sudo cp "$ROOT/data/allowlist.json" "$STATE/allowlist.json"

cd "$PREFIX/current"
sudo python3 -m venv "$PREFIX/.venv"
sudo "$PREFIX/.venv/bin/pip" install -e ".[live]"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/opt/lucy/ms-playwright}"
sudo env PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_PATH" "$PREFIX/.venv/bin/playwright" install chromium
if command -v apt-get >/dev/null 2>&1; then
  sudo env PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_PATH" "$PREFIX/.venv/bin/playwright" install-deps chromium || true
fi

if [[ "$CONSENT" -eq 1 ]]; then
  SLUG="$(sudo env LUCY_ORIGIN_RAW="$ORIGIN" "$PREFIX/.venv/bin/python" -c 'import os; from lucy.update import parse_github_origin; print(parse_github_origin(os.environ["LUCY_ORIGIN_RAW"]))')"
  sudo sed -i 's|^LUCY_AUTO_UPDATE=.*|LUCY_AUTO_UPDATE=git|' "$STATE/env"
  sudo sed -i "s|^LUCY_UPDATE_ORIGIN=.*|LUCY_UPDATE_ORIGIN=${SLUG}|" "$STATE/env"
else
  sudo sed -i 's|^LUCY_AUTO_UPDATE=.*|LUCY_AUTO_UPDATE=off|' "$STATE/env"
fi

sudo cp "$ROOT/pi/lucy.service" /etc/systemd/system/lucy.service
sudo cp "$ROOT/pi/lucy-update.service" /etc/systemd/system/lucy-update.service
sudo cp "$ROOT/pi/lucy-update.timer" /etc/systemd/system/lucy-update.timer
sudo chown -R lucy:lucy /var/lib/lucy "$PREFIX/logs" "$PREFIX/ms-playwright"
sudo chown root:lucy "$STATE" "$STATE"/*
sudo chmod 750 "$STATE"
sudo chmod 640 "$STATE"/*
sudo systemctl daemon-reload
sudo systemctl enable --now lucy.service
if [[ "$CONSENT" -eq 1 ]]; then
  sudo systemctl enable --now lucy-update.timer
  echo "auto-updates ON (git TOFU) from ${ORIGIN}"
else
  sudo systemctl disable --now lucy-update.timer 2>/dev/null || true
  echo "auto-updates OFF. later: sudo $ROOT/pi/consent-updates.sh owner/repo"
fi
sudo systemctl --no-pager --full status lucy.service || true
