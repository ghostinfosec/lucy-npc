#!/usr/bin/env bash
# Opt in or out of pull-only git updates after install.
# Side effects: /etc/lucy/env, systemd timer. Never touches persona JSON.
set -euo pipefail
STATE="${LUCY_STATE_DIR:-/etc/lucy}"
ENVFILE="${STATE}/env"

usage() {
  echo "usage: $0 owner/repo     # enable git TOFU auto-updates" >&2
  echo "       $0 --off          # disable auto-updates" >&2
  exit 2
}

[[ $# -ge 1 ]] || usage
sudo test -f "$ENVFILE" || { echo "no $ENVFILE — run pi/install.sh first" >&2; exit 1; }

if [[ "$1" == "--off" ]]; then
  sudo sed -i 's|^LUCY_AUTO_UPDATE=.*|LUCY_AUTO_UPDATE=off|' "$ENVFILE"
  sudo systemctl disable --now lucy-update.timer
  echo "auto-updates OFF"
  exit 0
fi

ORIGIN="$1"
if [[ -x /opt/lucy/.venv/bin/python ]]; then
  ORIGIN="$(sudo env LUCY_ORIGIN_RAW="$1" /opt/lucy/.venv/bin/python -c 'import os; from lucy.update import parse_github_origin; print(parse_github_origin(os.environ["LUCY_ORIGIN_RAW"]))')"
fi

if grep -q '^LUCY_UPDATE_ORIGIN=' "$ENVFILE"; then
  sudo sed -i "s|^LUCY_UPDATE_ORIGIN=.*|LUCY_UPDATE_ORIGIN=${ORIGIN}|" "$ENVFILE"
else
  echo "LUCY_UPDATE_ORIGIN=${ORIGIN}" | sudo tee -a "$ENVFILE" >/dev/null
fi
if grep -q '^LUCY_AUTO_UPDATE=' "$ENVFILE"; then
  sudo sed -i 's|^LUCY_AUTO_UPDATE=.*|LUCY_AUTO_UPDATE=git|' "$ENVFILE"
else
  echo 'LUCY_AUTO_UPDATE=git' | sudo tee -a "$ENVFILE" >/dev/null
fi

sudo systemctl daemon-reload
sudo systemctl enable --now lucy-update.timer
echo "auto-updates ON (git TOFU) origin=${ORIGIN}"
echo "signed/cosign path is not implemented. this is the same trust as git clone."
sudo -E /opt/lucy/.venv/bin/lucy-update --check
