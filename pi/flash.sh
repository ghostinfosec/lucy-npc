#!/usr/bin/env bash
# Laptop-side SD card prep: inject Lucy first-boot + optional WiFi/token before eject.
# Side effects: writes to the mounted Raspberry Pi boot partition only.
set -euo pipefail

# Avoid macOS AppleDouble (._*) sidecars on the FAT boot partition.
export COPYFILE_DISABLE=1

PI_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=wifi-connect-release.sh
source "$PI_DIR/wifi-connect-release.sh"
BOOT=""
SSID=""
WIFI_PASS=""
WIFI_COUNTRY="${LUCY_WIFI_COUNTRY:-US}"
HOSTNAME="${LUCY_HOSTNAME:-lucy-zero}"
SSH_KEY=""
LUCY_USER="${LUCY_USER:-pi}"
LUCY_TOKEN=""
LUCY_ENGINE="${LUCY_ENGINE:-live_http}"
LUCY_REPO="${LUCY_REPO:-https://github.com/ghostinfosec/lucy-npc.git}"
WIFI_PORTAL=1
BUNDLE_WIFI=1
BUNDLE_DEBS=1
ENABLE_SSH=1
CONSENT_AUTO_UPDATE=0
UPDATE_ORIGIN="ghostinfosec/lucy-npc"

usage() {
  cat <<'EOF'
usage: ./pi/flash.sh --boot /Volumes/bootfs [options]

  --boot PATH           Mounted Raspberry Pi boot partition (required)
  --ssid SSID           Pre-configure WiFi (optional; portal still available as fallback)
  --wifi-pass PASS      WiFi password (optional)
  --wifi-country CC     ISO country for WiFi (default: US)
  --hostname NAME       Pi hostname (default: lucy-zero)
  --user NAME           OS user for SSH key (default: pi)
  --ssh-key PATH        SSH public key file to authorize
  --lucy-token TOKEN    LUCY_STATUS_TOKEN for hatch admin login
  --engine ENGINE       live_http (Zero W) or live_public (Pi 4+)
  --repo URL            Git clone URL (default: ghostinfosec/lucy-npc)
  --no-wifi-portal      Skip bundling portal stack on SD
  --no-bundle-wifi      Do not download wifi-connect tarball to SD
  --no-bundle-debs      Skip bundling NetworkManager debs (~26 MB)
  --consent-auto-update Opt in to git pull auto-updates on first install
  --origin owner/repo   Update origin slug (default: ghostinfosec/lucy-npc)
  -h, --help            Show this help

Environment overrides: LUCY_SSID, LUCY_WIFI_PASS, LUCY_TOKEN, LUCY_HOSTNAME, LUCY_ENGINE

Examples:
  ./pi/flash.sh --boot /Volumes/bootfs
  ./pi/flash.sh --boot /Volumes/bootfs --ssid HomeNet --wifi-pass secret --ssh-key ~/.ssh/id_ed25519.pub
  LUCY_SSID=Guest LUCY_WIFI_PASS=x ./pi/flash.sh --boot /Volumes/bootfs --lucy-token "$(openssl rand -hex 24)"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --boot) BOOT="$2"; shift 2 ;;
    --ssid) SSID="$2"; shift 2 ;;
    --wifi-pass) WIFI_PASS="$2"; shift 2 ;;
    --wifi-country) WIFI_COUNTRY="$2"; shift 2 ;;
    --hostname) HOSTNAME="$2"; shift 2 ;;
    --user) LUCY_USER="$2"; shift 2 ;;
    --ssh-key) SSH_KEY="$2"; shift 2 ;;
    --lucy-token) LUCY_TOKEN="$2"; shift 2 ;;
    --engine) LUCY_ENGINE="$2"; shift 2 ;;
    --repo) LUCY_REPO="$2"; shift 2 ;;
    --no-wifi-portal) WIFI_PORTAL=0; shift ;;
    --no-bundle-wifi) BUNDLE_WIFI=0; shift ;;
    --no-bundle-debs) BUNDLE_DEBS=0; shift ;;
    --consent-auto-update) CONSENT_AUTO_UPDATE=1; shift ;;
    --origin) UPDATE_ORIGIN="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

SSID="${LUCY_SSID:-$SSID}"
WIFI_PASS="${LUCY_WIFI_PASS:-$WIFI_PASS}"
LUCY_TOKEN="${LUCY_TOKEN:-}"
HOSTNAME="${LUCY_HOSTNAME:-$HOSTNAME}"
LUCY_ENGINE="${LUCY_ENGINE:-$LUCY_ENGINE}"

[[ -n "$BOOT" ]] || { echo "error: --boot is required" >&2; usage; exit 1; }
[[ -d "$BOOT" ]] || { echo "error: boot path not found: $BOOT" >&2; exit 1; }

LUCY_BOOT="$BOOT/lucy"
mkdir -p "$LUCY_BOOT"

copy_pi_files() {
  local f
  for f in lucy-firstrun.sh first-boot.sh install-wifi-portal.sh wifi-watch.sh \
    wifi-connect-release.sh \
    lucy-first-boot.service lucy-wifi-portal.service lucy-connect-watch.service lucy-connect-watch.timer; do
    install -m 0755 "$PI_DIR/$f" "$LUCY_BOOT/$f"
  done
  find "$LUCY_BOOT" -name '._*' -delete 2>/dev/null || true
}

write_flash_env() {
  local ssh_line=""
  if [[ -n "$SSH_KEY" && -f "$SSH_KEY" ]]; then
    ssh_line="$(tr -d '\n\r' <"$SSH_KEY")"
  fi
  if [[ -z "$LUCY_TOKEN" ]]; then
    if command -v openssl >/dev/null 2>&1; then
      LUCY_TOKEN="$(openssl rand -hex 24)"
      echo "generated LUCY_STATUS_TOKEN: $LUCY_TOKEN"
    fi
  fi
  cat >"$LUCY_BOOT/lucy-flash.env" <<EOF
LUCY_SSID=${SSID}
LUCY_WIFI_PASS=${WIFI_PASS}
WIFI_COUNTRY=${WIFI_COUNTRY}
LUCY_HOSTNAME=${HOSTNAME}
LUCY_USER=${LUCY_USER}
LUCY_SSH_KEY=${ssh_line}
LUCY_ENABLE_SSH=${ENABLE_SSH}
LUCY_STATUS_TOKEN=${LUCY_TOKEN}
LUCY_ENGINE=${LUCY_ENGINE}
LUCY_REPO=${LUCY_REPO}
LUCY_WIFI_PORTAL=${WIFI_PORTAL}
LUCY_CONSENT_AUTO_UPDATE=${CONSENT_AUTO_UPDATE}
LUCY_UPDATE_ORIGIN=${UPDATE_ORIGIN}
LUCY_WLAN_IF=wlan0
EOF
  chmod 0600 "$LUCY_BOOT/lucy-flash.env"
}

bundle_os_debs() {
  [[ "$BUNDLE_DEBS" -eq 1 && "$WIFI_PORTAL" -eq 1 ]] || return 0
  echo "bundling NetworkManager debs for offline first boot (~26 MB, one-time download)..."
  if ! bash "$PI_DIR/bundle-debs.sh" "$LUCY_BOOT/debs"; then
    echo "error: could not bundle NetworkManager debs" >&2
    exit 1
  fi
  find "$LUCY_BOOT/debs" -name '._*' -delete 2>/dev/null || true
}

bundle_wifi_connect() {
  [[ "$BUNDLE_WIFI" -eq 1 && "$WIFI_PORTAL" -eq 1 ]] || return 0
  if [[ -f "$LUCY_BOOT/wifi-connect-rpi.tar.gz" ]]; then
    echo "wifi-connect bundle already on SD"
    return 0
  fi
  local url
  url="$(wifi_connect_rpi_bundle_url)"
  echo "downloading wifi-connect rpi bundle (${WFC_RPI_RELEASE}) for offline first boot..."
  if ! curl -sfL "$url" -o "$LUCY_BOOT/wifi-connect-rpi.tar.gz"; then
    echo "error: could not download wifi-connect bundle from ${url}" >&2
    exit 1
  fi
}

write_firstrun() {
  local target="$BOOT/firstrun.sh"
  local hook='for _b in /boot/firmware /boot; do [ -x "$_b/lucy/lucy-firstrun.sh" ] && "$_b/lucy/lucy-firstrun.sh" && break; done'
  if [[ -f "$target" ]] && ! grep -Fq 'lucy/lucy-firstrun.sh' "$target" 2>/dev/null; then
    COPYFILE_DISABLE=1 cp "$target" "$BOOT/firstrun.sh.lucy-bak"
    {
      cat "$target"
      echo ""
      echo "# lucy-npc first-boot hook"
      echo "$hook"
    } >"$target"
  else
    cat >"$target" <<EOF
#!/bin/bash
set -e
$hook
EOF
  fi
  chmod 0755 "$target"
}

copy_pi_files
write_flash_env
bundle_wifi_connect
bundle_os_debs
write_firstrun

cat <<EOF

Lucy flash staged on: $BOOT

Next:
  1. Eject SD, boot the Pi on a desk (power + time; first boot is slow).
  2. If WiFi was not injected, join AP "Lucy-Setup" from your phone and pick your network.
  3. SSH: ssh ${LUCY_USER}@${HOSTNAME}.local  (after mDNS comes up)
  4. Hatch: http://${HOSTNAME}.local:8787/  (token above if generated)

Portal recovery: if she loses WiFi for ~2 minutes, Lucy-Setup returns automatically.

EOF
