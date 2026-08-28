#!/usr/bin/env bash
# Install NetworkManager + balena wifi-connect for Lucy's setup portal.
# Side effects: disables dhcpcd; installs packages; downloads or extracts wifi-connect binary.
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  exec sudo bash "$0" "$@"
fi

PI_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ ! -f "$PI_DIR/lucy-wifi-portal.service" ]]; then
  for candidate in /opt/lucy/current/pi "$PI_DIR"; do
    if [[ -f "$candidate/lucy-wifi-portal.service" ]]; then
      PI_DIR="$candidate"
      break
    fi
  done
fi
# shellcheck source=wifi-connect-release.sh
source "$PI_DIR/wifi-connect-release.sh"
WFC_INSTALL_ROOT="${WFC_INSTALL_ROOT:-/usr/local}"
INSTALL_BIN_DIR="${WFC_INSTALL_ROOT}/sbin"
INSTALL_UI_DIR="${WFC_INSTALL_ROOT}/share/wifi-connect/ui"
CONFIRMATION=true
BUNDLE=""

for arg in "$@"; do
  case "$arg" in
    -y|--yes) CONFIRMATION=false ;;
    --bundle=*) BUNDLE="${arg#--bundle=}" ;;
    -h|--help)
      echo "usage: $0 [-y] [--bundle=/path/to/wifi-connect-rpi.tar.gz]"
      exit 0
      ;;
  esac
done

for boot in /boot/firmware/lucy/wifi-connect-rpi.tar.gz /boot/lucy/wifi-connect-rpi.tar.gz; do
  if [[ -z "$BUNDLE" && -f "$boot" ]]; then
    BUNDLE="$boot"
    break
  fi
done

say() { printf 'lucy-wifi-portal: %s\n' "$1"; }
err() { printf 'lucy-wifi-portal: %s\n' "$1" >&2; exit 1; }

service_load_state() {
  systemctl -p LoadState --value show "$1"
}

service_active_state() {
  systemctl -p ActiveState --value show "$1"
}

confirm() {
  if [[ "$CONFIRMATION" == false ]]; then
    return 0
  fi
  read -r -p "Install NetworkManager and disable dhcpcd? [y/N] " ans || ans=""
  [[ "$ans" == [yY]* ]] || exit 0
}

disable_dhcpcd() {
  if [[ "$(service_active_state dhcpcd 2>/dev/null || echo inactive)" == "active" ]]; then
    say "deactivating dhcpcd"
    systemctl stop dhcpcd
    systemctl disable dhcpcd
  fi
}

activate_network_manager() {
  if [[ "$(service_load_state NetworkManager 2>/dev/null || echo not-found)" == "not-found" ]]; then
    confirm
    say "installing NetworkManager"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y -d network-manager curl
    disable_dhcpcd
    apt-get install -y network-manager curl
    apt-get clean
  elif [[ "$(service_active_state NetworkManager)" != "active" ]]; then
    confirm
    disable_dhcpcd
    systemctl enable NetworkManager
    systemctl start NetworkManager
  fi
  [[ "$(service_active_state NetworkManager)" == "active" ]] || err "NetworkManager is not active"
}

install_wifi_connect() {
  if command -v wifi-connect >/dev/null 2>&1; then
    say "wifi-connect already installed: $(wifi-connect --version 2>/dev/null || true)"
    return 0
  fi

  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT

  if [[ -n "$BUNDLE" && -f "$BUNDLE" ]]; then
    say "extracting bundled wifi-connect from ${BUNDLE}"
    tar -xzf "$BUNDLE" -C "$tmp"
  else
    local url
    url="$(wifi_connect_rpi_bundle_url)"
    say "downloading wifi-connect release (${WFC_RPI_RELEASE})"
    curl -sfL "$url" | tar -xz -C "$tmp"
  fi

  install -m 0755 "$tmp/wifi-connect" "$INSTALL_BIN_DIR/wifi-connect"
  rm -rf "$INSTALL_UI_DIR"
  mkdir -p "$INSTALL_UI_DIR"
  cp -a "$tmp/ui/." "$INSTALL_UI_DIR/"
  say "installed $(wifi-connect --version)"
}

install_units() {
  cp "$PI_DIR/lucy-wifi-portal.service" /etc/systemd/system/lucy-wifi-portal.service
  cp "$PI_DIR/lucy-connect-watch.service" /etc/systemd/system/lucy-connect-watch.service
  cp "$PI_DIR/lucy-connect-watch.timer" /etc/systemd/system/lucy-connect-watch.timer
  install -m 0755 "$PI_DIR/wifi-watch.sh" /usr/local/lib/lucy/wifi-watch.sh
  systemctl daemon-reload
  systemctl enable lucy-connect-watch.timer
  systemctl start lucy-connect-watch.timer
  say "enabled lucy-connect-watch.timer"
}

mkdir -p /usr/local/lib/lucy
activate_network_manager
install_wifi_connect
install_units
say "done. portal SSID: Lucy-Setup (open). watch interval: 45s."
