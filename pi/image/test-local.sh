#!/usr/bin/env bash
# Mac/laptop smoke tests for pi/image (not a full pi-gen build).
# Side effects: may download wifi-connect tarball to /tmp; no SD writes.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGE="${ROOT}/pi/image/stage-lucy"
PASS=0
FAIL=0

ok() { echo "ok: $1"; PASS=$((PASS + 1)); }
bad() { echo "FAIL: $1" >&2; FAIL=$((FAIL + 1)); }

echo "Lucy image local smoke test"
echo "repo: ${ROOT}"
echo "---"

for f in \
  pi/image/chroot-install.sh \
  pi/image/stage-lucy/prerun.sh \
  pi/image/stage-lucy/01-lucy/00-run.sh \
  pi/image/stage-lucy/01-lucy/01-run-chroot.sh \
  pi/wifi-connect-release.sh; do
  if bash -n "${ROOT}/${f}" 2>/dev/null || [[ "$f" == *.sh ]]; then
    bash -n "${ROOT}/${f}" && ok "syntax ${f}"
  fi
done

[[ -f "${STAGE}/EXPORT_IMAGE" ]] && ok "EXPORT_IMAGE present" || bad "missing EXPORT_IMAGE"
[[ -s "${STAGE}/00-pkg/00-packages" ]] && ok "00-packages present" || bad "missing 00-packages"
grep -q network-manager "${STAGE}/00-pkg/00-packages" && ok "network-manager in packages" || bad "network-manager missing"

URL="$("${ROOT}/pi/wifi-connect-release.sh")"
if curl -sfL --range 0-99 "$URL" >/dev/null; then
  ok "wifi-connect URL reachable: ${URL}"
else
  bad "wifi-connect URL not reachable: ${URL}"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAKE_ROOT="${TMP}/rootfs"
install -d "${FAKE_ROOT}/opt/lucy-build"
rsync -a "${ROOT}/" "${FAKE_ROOT}/opt/lucy-build/" --exclude .git --exclude pi-gen --exclude work
export ROOTFS_DIR="$FAKE_ROOT"
export LUCY_SRC="$ROOT"
bash "${STAGE}/01-lucy/00-run.sh" && ok "00-run.sh rsync into fake rootfs"

[[ -f "${FAKE_ROOT}/opt/lucy-build/VERSION" ]] && ok "lucy-build copied" || bad "lucy-build copy failed"

echo "---"
echo "pass=${PASS} fail=${FAIL}"
if [[ "$FAIL" -gt 0 ]]; then
  echo "Full pi-gen image build requires Linux + Docker — run: gh workflow run build-image.yml --ref feature/lucy-os-image"
  exit 1
fi
echo "Local smoke tests passed. For a full image, use GitHub Actions workflow_dispatch (see pi/image/README.md)."
