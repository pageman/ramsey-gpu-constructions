#!/usr/bin/env bash
# Run ON THE MAC. Pulls the pod tarball into the git clone and Downloads.
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This helper is for the Mac clone. On the pod run:  bash scripts/pod-pack-repro.sh"
  exit 2
fi

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "${HERE}"

if [[ ! -f engine/cli.py ]]; then
  echo "Use the git clone ~/ramsey-gpu-constructions not Downloads."
  exit 1
fi

HOST="${RAMSEY_POD_HOST:-}"
PORT="${RAMSEY_POD_PORT:-}"
KEY="${RAMSEY_POD_KEY:-$HOME/.ssh/id_ed25519}"
REMOTE="${RAMSEY_POD_REPO:-/workspace/ramsey-gpu-constructions}"
DEST="${RAMSEY_DOWNLOADS:-$HOME/Downloads/Ramsey-GPU-Constructions}"

if [[ -z "${HOST}" || -z "${PORT}" ]]; then
  echo "Set the live RunPod SSH-over-TCP values first:"
  echo "  export RAMSEY_POD_HOST=69.30.85.91"
  echo "  export RAMSEY_POD_PORT=22061"
  echo "  bash scripts/mac-archive-repro.sh"
  exit 1
fi

if [[ ! -f "${KEY}" ]]; then
  echo "SSH key not found: ${KEY}"
  exit 1
fi

echo "Copying pack script to the pod..."
scp -o StrictHostKeyChecking=accept-new -i "${KEY}" -P "${PORT}" \
  "${HERE}/scripts/pod-pack-repro.sh" \
  "root@${HOST}:${REMOTE}/scripts/pod-pack-repro.sh"
ssh -i "${KEY}" -p "${PORT}" "root@${HOST}" "chmod +x ${REMOTE}/scripts/pod-pack-repro.sh"

echo "Packing on the pod (this takes a few seconds)..."
PACK_LINE="$(
  ssh -o StrictHostKeyChecking=accept-new -i "${KEY}" -p "${PORT}" "root@${HOST}" \
    "bash ${REMOTE}/scripts/pod-pack-repro.sh" | tail -n 1
)"
if [[ "${PACK_LINE}" != PACK_OK* ]]; then
  echo "Pod pack failed. Last line was:"
  echo "${PACK_LINE}"
  echo "On the pod run:  bash scripts/pod-pack-repro.sh"
  exit 1
fi
REMOTE_TGZ="${PACK_LINE#PACK_OK }"
LOCAL_TGZ="${DEST}/repro-from-pod/ramsey-repro.tgz"
mkdir -p "${DEST}/repro-from-pod" "${DEST}/phase5-from-pod" "${DEST}/phase7-from-pod" "${DEST}/a40-from-pod/keep-a40"
mkdir -p "${HERE}/data/phase5" "${HERE}/data/phase7" "${HERE}/data/a40/pod-keep"

echo "Copying ${REMOTE_TGZ} to the Mac..."
scp -o StrictHostKeyChecking=accept-new -i "${KEY}" -P "${PORT}" \
  "root@${HOST}:${REMOTE_TGZ}" "${LOCAL_TGZ}"

echo "Unpacking..."
UNPACK="${DEST}/repro-from-pod/unpack"
rm -rf "${UNPACK}"
mkdir -p "${UNPACK}"
tar -C "${UNPACK}" -xzf "${LOCAL_TGZ}"

if [[ -d "${UNPACK}/phase5" ]]; then
  cp -a "${UNPACK}/phase5/." "${DEST}/phase5-from-pod/"
  cp -a "${UNPACK}/phase5/." "${HERE}/data/phase5/"
fi
if [[ -d "${UNPACK}/phase7" ]]; then
  cp -a "${UNPACK}/phase7/." "${DEST}/phase7-from-pod/"
  cp -a "${UNPACK}/phase7/." "${HERE}/data/phase7/"
fi
if [[ -d "${UNPACK}/keep-a40" ]]; then
  cp -a "${UNPACK}/keep-a40/." "${DEST}/a40-from-pod/keep-a40/"
  cp -a "${UNPACK}/keep-a40/." "${HERE}/data/a40/pod-keep/"
fi
if [[ -d "${UNPACK}/binaries" ]]; then
  mkdir -p "${HERE}/data/phase5/binaries" "${DEST}/phase5-from-pod/binaries"
  cp -a "${UNPACK}/binaries/." "${HERE}/data/phase5/binaries/"
  cp -a "${UNPACK}/binaries/." "${DEST}/phase5-from-pod/binaries/"
fi
if [[ -d "${UNPACK}/meta" ]]; then
  mkdir -p "${HERE}/data/phase5/meta" "${DEST}/phase5-from-pod/meta"
  cp -a "${UNPACK}/meta/." "${HERE}/data/phase5/meta/"
  cp -a "${UNPACK}/meta/." "${DEST}/phase5-from-pod/meta/"
fi
if [[ -d "${UNPACK}/engine-src" ]]; then
  mkdir -p "${HERE}/data/phase5/engine-src"
  cp -a "${UNPACK}/engine-src/." "${HERE}/data/phase5/engine-src/"
fi

if [[ -f "${HERE}/scripts/sync-to-downloads.sh" ]]; then
  echo "Refreshing the Downloads snapshot of the clone..."
  RAMSEY_DOWNLOADS="${DEST}" bash "${HERE}/scripts/sync-to-downloads.sh" || true
fi

STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
HEAD="$(git -C "${HERE}" rev-parse HEAD)"
{
  echo "archived_utc=${STAMP}"
  echo "mac_clone=${HERE}"
  echo "downloads=${DEST}"
  echo "git_head=${HEAD}"
  echo "pod=${HOST}:${PORT}"
  echo "tarball=${LOCAL_TGZ}"
} > "${HERE}/data/phase5/ARCHIVE.txt"
cp "${HERE}/data/phase5/ARCHIVE.txt" "${DEST}/phase5-from-pod/ARCHIVE.txt"

if command -v shasum >/dev/null; then
  (cd "${HERE}/data/phase5" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 shasum -a 256) \
    > "${HERE}/data/phase5/SHA256SUMS"
  cp "${HERE}/data/phase5/SHA256SUMS" "${DEST}/phase5-from-pod/SHA256SUMS"
fi

echo
echo "Mac git clone archive:  ${HERE}/data/phase5"
echo "Old 2a/4a keep:         ${HERE}/data/a40/pod-keep"
echo "Downloads phase5:       ${DEST}/phase5-from-pod"
echo "Downloads 2a/4a keep:   ${DEST}/a40-from-pod/keep-a40"
echo "Downloads tarball:      ${LOCAL_TGZ}"
echo
echo "Publish to GitHub and Origin from this Mac clone:"
echo "  git add data/phase5 data/a40/pod-keep data/phase5/SHA256SUMS"
echo "  git commit -m \"Archive phase5 run and pod-keep 2a/4a catalogues.\""
echo "  git push github main"
echo "  git push origin main"
echo
ls -la "${HERE}/data/phase5" "${HERE}/data/a40/pod-keep" "${DEST}/phase5-from-pod" 2>/dev/null || true
