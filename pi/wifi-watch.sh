#!/usr/bin/env bash
# Connectivity watchdog for Lucy. Starts the WiFi portal after sustained failure.
# Side effects: reads/writes /var/lib/lucy/connect-watch.state; may start/stop lucy-wifi-portal.
set -euo pipefail

STATE_DIR="${LUCY_STATE_DIR:-/var/lib/lucy}"
STATE_FILE="${STATE_DIR}/connect-watch.state"
FAIL_THRESHOLD="${LUCY_CONNECT_FAIL_THRESHOLD:-3}"
COOLDOWN_SEC="${LUCY_CONNECT_COOLDOWN_SEC:-300}"
PORTAL_UNIT="${LUCY_WIFI_PORTAL_UNIT:-lucy-wifi-portal.service}"
PROBE_URL="${LUCY_CONNECT_PROBE_URL:-http://connectivitycheck.gstatic.com/generate_204}"
WLAN_IF="${LUCY_WLAN_IF:-wlan0}"

mkdir -p "$STATE_DIR"
touch "$STATE_FILE"

read_state() {
  # shellcheck disable=SC1090
  source "$STATE_FILE" 2>/dev/null || true
  : "${fail_count:=0}"
  : "${portal_active:=0}"
  : "${cooldown_until:=0}"
}

write_state() {
  cat >"$STATE_FILE" <<EOF
fail_count=${fail_count}
portal_active=${portal_active}
cooldown_until=${cooldown_until}
EOF
}

wlan_associated() {
  iwgetid -r "$WLAN_IF" >/dev/null 2>&1
}

has_ipv4() {
  ip -4 addr show dev "$WLAN_IF" 2>/dev/null | grep -q 'inet '
}

gateway_ok() {
  ip route show default dev "$WLAN_IF" 2>/dev/null | grep -q .
}

internet_ok() {
  curl -sf --max-time 8 -o /dev/null "$PROBE_URL"
}

fully_connected() {
  wlan_associated && has_ipv4 && gateway_ok && internet_ok
}

portal_running() {
  systemctl is-active --quiet "$PORTAL_UNIT"
}

start_portal() {
  systemctl start "$PORTAL_UNIT"
  portal_active=1
}

stop_portal() {
  if portal_running; then
    systemctl stop "$PORTAL_UNIT" || true
  fi
  portal_active=0
  cooldown_until=$(( $(date +%s) + COOLDOWN_SEC ))
}

read_state
now=$(date +%s)

if fully_connected; then
  fail_count=0
  if portal_running || [[ "$portal_active" -eq 1 ]]; then
    stop_portal
  fi
  write_state
  exit 0
fi

if [[ "$cooldown_until" -gt "$now" && "$portal_active" -eq 0 ]]; then
  write_state
  exit 0
fi

fail_count=$(( fail_count + 1 ))

if [[ "$fail_count" -ge "$FAIL_THRESHOLD" ]]; then
  if ! portal_running; then
    start_portal
  fi
else
  if portal_running; then
    stop_portal
  fi
fi

write_state
