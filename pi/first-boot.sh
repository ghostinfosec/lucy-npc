#!/usr/bin/env bash
# Runs once on the Pi after lucy-firstrun.sh — portal bootstrap, optional clone, install.
# Side effects: installs Lucy, wifi portal stack; writes /var/lib/lucy/first-boot.done.
set -euo pipefail

DONE=/var/lib/lucy/first-boot.done
FLASH_ENV=/etc/lucy/flash.env
BOOT=""
for candidate in /boot/firmware /boot; do
  if [[ -d "$candidate/lucy" ]]; then
    BOOT="$candidate"
    break
  fi
done

mkdir -p /var/lib/lucy /etc/lucy
[[ -f "$DONE" ]] && exit 0

if [[ -f "$FLASH_ENV" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$FLASH_ENV"
  set +a
fi

LUCY_REPO="${LUCY_REPO:-https://github.com/ghostinfosec/lucy-npc.git}"
LUCY_ENGINE="${LUCY_ENGINE:-live_http}"
LUCY_WIFI_PORTAL="${LUCY_WIFI_PORTAL:-1}"
LUCY_CLONE_DIR="${LUCY_CLONE_DIR:-/tmp/lucy-npc-first-boot}"
WIFI_COUNTRY="${WIFI_COUNTRY:-US}"

install_scripts() {
  local src="${BOOT}/lucy"
  if [[ -d "$src" ]]; then
    install -m 0755 "$src/install-wifi-portal.sh" /usr/local/lib/lucy/install-wifi-portal.sh
    install -m 0755 "$src/wifi-watch.sh" /usr/local/lib/lucy/wifi-watch.sh
    install -m 0755 "$src/first-boot.sh" /usr/local/lib/lucy/first-boot.sh
    for unit in lucy-wifi-portal.service lucy-connect-watch.service lucy-connect-watch.timer; do
      [[ -f "$src/$unit" ]] && cp "$src/$unit" "/etc/systemd/system/$unit"
    done
  fi
}

apply_wifi_credentials() {
  [[ -n "${LUCY_SSID:-}" ]] || return 0
  command -v nmcli >/dev/null 2>&1 || return 0
  nmcli radio wifi on || true
  nmcli device set "$LUCY_WLAN_IF" managed yes 2>/dev/null || true
  if nmcli -t -f NAME connection show | grep -Fxq "lucy-flash"; then
    nmcli connection delete lucy-flash || true
  fi
  nmcli connection add type wifi ifname "${LUCY_WLAN_IF:-wlan0}" con-name lucy-flash \
    ssid "$LUCY_SSID" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "${LUCY_WIFI_PASS:-}" \
    802-11-wireless.country "$WIFI_COUNTRY"
  nmcli connection up lucy-flash || true
}

wait_for_internet() {
  local tries="${1:-12}"
  local i
  for ((i = 1; i <= tries; i++)); do
    if curl -sf --max-time 8 -o /dev/null http://connectivitycheck.gstatic.com/generate_204; then
      return 0
    fi
    sleep 5
  done
  return 1
}

run_portal_blocking() {
  echo "lucy-first-boot: starting Lucy-Setup portal (connect your phone)"
  wifi-connect --portal-ssid Lucy-Setup --portal-passphrase "" --portal-listening-port 80
}

install_scripts

if [[ "$LUCY_WIFI_PORTAL" == "1" ]]; then
  if [[ -x /usr/local/lib/lucy/install-wifi-portal.sh ]]; then
    /usr/local/lib/lucy/install-wifi-portal.sh -y
  elif [[ -d "${BOOT}/lucy" ]]; then
    bash "${BOOT}/lucy/install-wifi-portal.sh" -y
  fi
fi

apply_wifi_credentials

if ! wait_for_internet 12; then
  if command -v wifi-connect >/dev/null 2>&1; then
    run_portal_blocking
    wait_for_internet 24 || echo "lucy-first-boot: still offline after portal; continuing anyway" >&2
  else
    echo "lucy-first-boot: no internet and wifi-connect missing; SSH in and finish manually" >&2
  fi
fi

if [[ ! -f /opt/lucy/current/pi/install.sh ]]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends git ca-certificates
  rm -rf "$LUCY_CLONE_DIR"
  git clone --depth 1 "$LUCY_REPO" "$LUCY_CLONE_DIR"
  INSTALL_ARGS=(--engine "$LUCY_ENGINE")
  [[ "$LUCY_WIFI_PORTAL" == "1" ]] && INSTALL_ARGS+=(--wifi-portal)
  [[ -n "${LUCY_STATUS_TOKEN:-}" ]] && INSTALL_ARGS+=(--lucy-token "$LUCY_STATUS_TOKEN")
  [[ "${LUCY_CONSENT_AUTO_UPDATE:-0}" == "1" ]] && INSTALL_ARGS+=(--consent-auto-update)
  [[ -n "${LUCY_UPDATE_ORIGIN:-}" ]] && INSTALL_ARGS+=(--origin="$LUCY_UPDATE_ORIGIN")
  bash "$LUCY_CLONE_DIR/pi/install.sh" "${INSTALL_ARGS[@]}"
fi

touch "$DONE"
systemctl disable lucy-first-boot.service 2>/dev/null || true
echo "lucy-first-boot: complete"
