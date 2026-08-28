#!/usr/bin/env bash
# Full Lucy OS image build on Linux with Docker (not macOS-native).
# Side effects: clones pi-gen, writes deploy/*.img under pi-gen/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PIGEN_DIR="${PIGEN_DIR:-${ROOT}/pi-gen}"
RELEASE="${LUCY_PI_RELEASE:-bookworm}"

if ! command -v docker >/dev/null 2>&1; then
  echo "error: docker required. Install Docker Desktop or run on Linux." >&2
  echo "Mac alternative: bash pi/image/test-local.sh (smoke only)" >&2
  echo "CI alternative: merge PR, then Actions → build-image → Run workflow" >&2
  exit 1
fi

if [[ ! -d "${PIGEN_DIR}/.git" ]]; then
  git clone --depth 1 --branch master https://github.com/RPi-Distro/pi-gen.git "${PIGEN_DIR}"
fi

export LUCY_SRC="${ROOT}"
export GITHUB_WORKSPACE="${ROOT}"
export LUCY_IMAGE_ENGINE="${LUCY_IMAGE_ENGINE:-live_http}"

cat >"${PIGEN_DIR}/config" <<EOF
IMG_NAME='lucy-zero-w'
RELEASE='${RELEASE}'
HOSTNAME='lucy-zero'
ENABLE_SSH=1
STAGE_LIST='stage0 stage1 stage2 ${ROOT}/pi/image/stage-lucy'
EOF

cd "${PIGEN_DIR}"
./build-docker.sh

echo "done. image: ${PIGEN_DIR}/deploy/lucy-zero-w.img (or .zip/.xz depending on pi-gen config)"
