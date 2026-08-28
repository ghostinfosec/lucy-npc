#!/bin/bash -e
# pi-gen host hook: copy Lucy source tree into the rootfs before chroot install.
LUCY_SRC="${LUCY_SRC:-${GITHUB_WORKSPACE:-$(cd "$(dirname "$0")/../../../.." && pwd)}}"
install -d "${ROOTFS_DIR}/opt/lucy-build"
rsync -a "${LUCY_SRC}/" "${ROOTFS_DIR}/opt/lucy-build/" \
  --exclude .git \
  --exclude pi-gen \
  --exclude work \
  --exclude deploy
test -f "${ROOTFS_DIR}/opt/lucy-build/pi/image/chroot-install.sh"
