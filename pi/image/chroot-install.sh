#!/usr/bin/env bash
# Install Lucy into a pi-gen rootfs (chroot). No sudo, no git clone, no apt from network.
# Side effects: writes /opt/lucy, /etc/lucy, systemd units; enables lucy + wifi portal.
set -euo pipefail

BUILD_ROOT="${LUCY_BUILD_ROOT:-/opt/lucy-build}"
PREFIX="${LUCY_PREFIX:-/opt/lucy}"
STATE="${LUCY_STATE_DIR:-/etc/lucy}"
ENGINE="${LUCY_IMAGE_ENGINE:-live_http}"
VERSION="$(tr -d ' \n\r' <"${BUILD_ROOT}/VERSION" 2>/dev/null || echo "0.0.0")"
PI_DIR="${BUILD_ROOT}/pi"

install -d "${PREFIX}/slots" "${PREFIX}/logs" "${PREFIX}/ms-playwright" /var/lib/lucy "${STATE}" /usr/local/lib/lucy

if ! id lucy >/dev/null 2>&1; then
  useradd --system --home /var/lib/lucy --shell /usr/sbin/nologin lucy
fi

rsync -a --exclude '.venv' --exclude '.git' --exclude '.dress' \
  "${BUILD_ROOT}/" "${PREFIX}/slots/v${VERSION}/"
ln -sfn "${PREFIX}/slots/v${VERSION}" "${PREFIX}/current"

if [[ ! -f "${STATE}/env" ]]; then
  cp "${BUILD_ROOT}/.env.template" "${STATE}/env"
  sed -i "s|^LUCY_PERSONA=.*|LUCY_PERSONA=${STATE}/persona.json|" "${STATE}/env"
  sed -i "s|^LUCY_LOG_DIR=.*|LUCY_LOG_DIR=${PREFIX}/logs|" "${STATE}/env"
  sed -i "s|^LUCY_ENGINE=.*|LUCY_ENGINE=${ENGINE}|" "${STATE}/env"
  sed -i 's|^LUCY_AUTO_UPDATE=.*|LUCY_AUTO_UPDATE=off|' "${STATE}/env"
  sed -i "s|^PLAYWRIGHT_BROWSERS_PATH=.*|PLAYWRIGHT_BROWSERS_PATH=${PREFIX}/ms-playwright|" "${STATE}/env" || true
fi

cp "${BUILD_ROOT}/data/personas/wool.json" "${STATE}/persona.json"
cp "${BUILD_ROOT}/data/allowlist.json" "${STATE}/allowlist.json"

python3 -m venv "${PREFIX}/.venv"
"${PREFIX}/.venv/bin/pip" install -e "${PREFIX}/current" "httpx==0.28.1"

# shellcheck source=/dev/null
source "${PI_DIR}/wifi-connect-release.sh"
tmp="$(mktemp -d)"
curl -sfL "$(wifi_connect_rpi_bundle_url)" | tar -xz -C "$tmp"
install -m 0755 "$tmp/wifi-connect" /usr/local/sbin/wifi-connect
install -d /usr/local/share/wifi-connect/ui
cp -a "$tmp/ui/." /usr/local/share/wifi-connect/ui/
rm -rf "$tmp"

for f in wifi-watch.sh wifi-connect-release.sh; do
  install -m 0755 "${PI_DIR}/${f}" "/usr/local/lib/lucy/${f}"
done
for unit in lucy.service lucy-update.service lucy-update.timer \
  lucy-wifi-portal.service lucy-connect-watch.service lucy-connect-watch.timer; do
  install -m 0644 "${PI_DIR}/${unit}" "/etc/systemd/system/${unit}"
done

chown -R lucy:lucy /var/lib/lucy "${PREFIX}/logs" "${PREFIX}/ms-playwright"
chown root:lucy "${STATE}"
chmod 750 "${STATE}"
chmod 640 "${STATE}/"* || true

systemctl disable dhcpcd.service 2>/dev/null || systemctl disable dhcpcd 2>/dev/null || true
systemctl enable NetworkManager.service
systemctl enable lucy-connect-watch.timer
systemctl enable lucy.service

install -d /etc/lucy
echo "${VERSION}" >/etc/lucy/image-version
echo "Lucy OS image — portal-first. Join Lucy-Setup from your phone if WiFi is not configured." >/etc/issue.lucy

echo "lucy-image: installed v${VERSION} engine=${ENGINE}"
