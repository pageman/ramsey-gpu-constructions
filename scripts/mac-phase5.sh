#!/usr/bin/env bash
# SAFE TO RUN ON THE MAC. This does not start the hunt.
# The hunt lives on the RunPod container. /workspace/... is a pod path.
set -euo pipefail

echo "============================================================"
echo " You are on: $(hostname)  uname=$(uname -s)"
echo " Prompt looks like a Mac if it says MacBook-Pro."
echo " /workspace/ramsey-gpu-constructions exists ONLY on the pod."
echo " Do not cd /workspace/... from this laptop."
echo "============================================================"
echo

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This helper is for the Mac clone. On the pod run:"
  echo "  bash scripts/pod-phase5.sh"
  exit 2
fi

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "${HERE}"

if [[ ! -f engine/cli.py ]]; then
  echo "This folder is not the git clone. Use:"
  echo "  cd ~/ramsey-gpu-constructions"
  echo "not ~/Downloads/Ramsey-GPU-Constructions (that snapshot has no .git)."
  exit 1
fi

if [[ ! -f scripts/pod-phase5.sh ]]; then
  echo "This clone is BEHIND. The phase5 scripts are not here yet."
  echo "In THIS same directory (the git clone):"
  echo
  echo "  git fetch origin"
  echo "  git merge origin/main"
  echo "  git push github main"
  echo
  echo "Then run this helper again:  bash scripts/mac-phase5.sh"
  exit 1
fi

echo "Mac clone OK: ${HERE}"
git log -1 --oneline 2>/dev/null || true
echo

HOST="${RAMSEY_POD_HOST:-}"
PORT="${RAMSEY_POD_PORT:-}"
KEY="${RAMSEY_POD_KEY:-$HOME/.ssh/id_ed25519}"
REMOTE="${RAMSEY_POD_REPO:-/workspace/ramsey-gpu-constructions}"

if [[ -z "${HOST}" || -z "${PORT}" ]]; then
  echo "NEXT: open RunPod → the A40 pod → Connect → SSH over exposed TCP."
  echo "Copy host and port (they change after Stop/Start). Then EITHER:"
  echo
  echo "  export RAMSEY_POD_HOST=A.B.C.D"
  echo "  export RAMSEY_POD_PORT=NNNNN"
  echo "  bash scripts/mac-phase5.sh"
  echo
  echo "OR, by hand:"
  echo
  echo "  ssh root@HOST -p PORT -i ${KEY}"
  echo "After login the prompt must say root, not paulpajo."
  echo "  cd ${REMOTE}"
  echo "  git pull origin main || true"
  echo "  bash scripts/pod-phase5.sh"
  echo
  echo "Do not run bash scripts/pod-phase5.sh on this Mac."
  echo "Do not attach tmux session ramsey (that is leftover 2a)."
  exit 0
fi

echo "Syncing phase5 files → root@${HOST}:${PORT}:${REMOTE}"
if [[ ! -f "${KEY}" ]]; then
  echo "SSH key not found: ${KEY}"
  echo "Set RAMSEY_POD_KEY to your RunPod key."
  exit 1
fi

ssh -o StrictHostKeyChecking=accept-new -i "${KEY}" -p "${PORT}" "root@${HOST}" \
  "mkdir -p ${REMOTE}/engine/kernels ${REMOTE}/scripts ${REMOTE}/data ${REMOTE}/docs"

# Small set: enough to start phase5 even if git pull on the pod fails.
scp -o StrictHostKeyChecking=accept-new -i "${KEY}" -P "${PORT}" \
  engine/phase5.py engine/jobs.py engine/cli.py engine/registry.py engine/scale.py \
  engine/yu_pool.py engine/constructions.py engine/test_kernels.py \
  "root@${HOST}:${REMOTE}/engine/"

scp -o StrictHostKeyChecking=accept-new -i "${KEY}" -P "${PORT}" \
  engine/kernels/native_decide.c engine/kernels/decide_alpha.py engine/kernels/bitset_mcs.py \
  engine/kernels/native_mis.c engine/kernels/residual.py \
  "root@${HOST}:${REMOTE}/engine/kernels/"

scp -o StrictHostKeyChecking=accept-new -i "${KEY}" -P "${PORT}" \
  scripts/pod-phase5.sh scripts/phase5-status.sh \
  "root@${HOST}:${REMOTE}/scripts/"

scp -o StrictHostKeyChecking=accept-new -i "${KEY}" -P "${PORT}" \
  data/yu_r4_20.json \
  "root@${HOST}:${REMOTE}/data/"

ssh -i "${KEY}" -p "${PORT}" "root@${HOST}" "chmod +x ${REMOTE}/scripts/pod-phase5.sh ${REMOTE}/scripts/phase5-status.sh"

echo
echo "Starting phase5 ON THE POD (tmux ramsey5)."
ssh -i "${KEY}" -p "${PORT}" "root@${HOST}" "bash ${REMOTE}/scripts/pod-phase5.sh"
echo
echo "Hunt is on the pod. This Mac window can close."
echo "Watch later:"
echo "  ssh root@${HOST} -p ${PORT} -i ${KEY}  'cd ${REMOTE} && bash scripts/phase5-status.sh'"
