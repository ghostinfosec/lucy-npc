#!/usr/bin/env bash
# Pinned wifi-connect release for Pi Zero W through Pi 3 (linux-rpi bundle).
# Side effects: none (prints URL only).
set -euo pipefail

WFC_RPI_RELEASE="${WFC_RPI_RELEASE:-v4.4.6}"

wifi_connect_rpi_bundle_url() {
  printf 'https://github.com/balena-os/wifi-connect/releases/download/%s/wifi-connect-%s-linux-rpi.tar.gz' \
    "$WFC_RPI_RELEASE" "$WFC_RPI_RELEASE"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  wifi_connect_rpi_bundle_url
fi
