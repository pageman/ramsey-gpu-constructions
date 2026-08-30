#!/usr/bin/env bash
# Run ON THE MAC after 7a–7f + 7c1.
# 1) Promote the scp'd phase7 log into data/phase7/
# 2) Optionally pull leftover gitignored files from the pod
# 3) Rsync the clone to ~/Downloads/Ramsey-GPU-Constructions/
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "WRONG MACHINE. Prompt must be paulpajo@…MacBook-Pro, not root@."
  echo "This script writes ~/Downloads/Ramsey-GPU-Constructions/ on the Mac."
  exit 2
fi

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "${HERE}"
if [[ ! -f engine/cli.py ]]; then
  echo "Use the git clone ~/ramsey-gpu-constructions — not Downloads."
  exit 1
fi

DEST="${RAMSEY_DOWNLOADS:-$HOME/Downloads/Ramsey-GPU-Constructions}"
HOST="${RAMSEY_POD_HOST:-69.30.85.91}"
PORT="${RAMSEY_POD_PORT:-22061}"
KEY="${RAMSEY_POD_KEY:-$HOME/.ssh/id_ed25519}"
REMOTE="${RAMSEY_POD_REPO:-/workspace/ramsey-gpu-constructions}"
SKIP_POD="${RAMSEY_SKIP_POD:-0}"

mkdir -p "${HERE}/data/phase7" "${DEST}/phase7-from-pod" "${DEST}/phase5-from-pod" "${DEST}/a40-from-pod"

# --- 1. Promote the log the operator already scp'd ---
if [[ -f "${HERE}/data/phase7-7c1.log" ]]; then
  cp -f "${HERE}/data/phase7-7c1.log" "${HERE}/data/phase7/phase7.log"
  echo "promoted data/phase7-7c1.log → data/phase7/phase7.log ($(wc -c < "${HERE}/data/phase7/phase7.log") bytes)"
elif [[ -f "${HERE}/data/phase7/phase7.log" ]]; then
  echo "data/phase7/phase7.log already present"
else
  echo "WARNING: no data/phase7-7c1.log. If the pod is still up, this script will try scp."
fi

# --- 2. Optional live pod pull ---
pod_ok=0
if [[ "${SKIP_POD}" != "1" && -f "${KEY}" ]]; then
  if ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new \
       -i "${KEY}" -p "${PORT}" "root@${HOST}" "test -f ${REMOTE}/engine/cli.py" 2>/dev/null; then
    pod_ok=1
    echo "pod reachable ${HOST}:${PORT}"
    mkdir -p /tmp/ramsey-phase7-pull
    scp -o StrictHostKeyChecking=accept-new -i "${KEY}" -P "${PORT}" \
      "root@${HOST}:${REMOTE}/data/phase7.log" \
      "root@${HOST}:${REMOTE}/data/phase7.status.json" \
      "root@${HOST}:${REMOTE}/data/yu_r4_20.cert2.json" \
      "root@${HOST}:${REMOTE}/data/yu_r4_20.complement.clq" \
      /tmp/ramsey-phase7-pull/ 2>/dev/null || true
    [[ -f /tmp/ramsey-phase7-pull/phase7.log ]] && cp -f /tmp/ramsey-phase7-pull/phase7.log "${HERE}/data/phase7/phase7.log"
    [[ -f /tmp/ramsey-phase7-pull/phase7.status.json ]] && cp -f /tmp/ramsey-phase7-pull/phase7.status.json "${HERE}/data/phase7/phase7.status.json"
    [[ -f /tmp/ramsey-phase7-pull/yu_r4_20.cert2.json ]] && cp -f /tmp/ramsey-phase7-pull/yu_r4_20.cert2.json "${HERE}/data/phase7/yu_r4_20.cert2.json"
    [[ -f /tmp/ramsey-phase7-pull/yu_r4_20.complement.clq ]] && cp -f /tmp/ramsey-phase7-pull/yu_r4_20.complement.clq "${HERE}/data/phase7/yu_r4_20.complement.clq"
    scp -o StrictHostKeyChecking=accept-new -i "${KEY}" -P "${PORT}" \
      "root@${HOST}:${REMOTE}/engine/kernels/native_decide.so" \
      "root@${HOST}:${REMOTE}/engine/kernels/native_mis.so" \
      "${HERE}/data/phase7/" 2>/dev/null || true
  else
    echo "pod not reachable at ${HOST}:${PORT} — using Mac files only (OK if you already Stopped)."
  fi
else
  echo "skip pod (RAMSEY_SKIP_POD=1 or no SSH key)"
fi

# --- 3. Archive stamp ---
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
HEAD="$(git -C "${HERE}" rev-parse HEAD 2>/dev/null || echo unknown)"
{
  echo "archived_utc=${STAMP}"
  echo "mac_clone=${HERE}"
  echo "downloads=${DEST}"
  echo "git_head=${HEAD}"
  echo "pod=${HOST}:${PORT}"
  echo "pod_reached=${pod_ok}"
  echo "phase7_log=${HERE}/data/phase7/phase7.log"
} > "${HERE}/data/phase7/ARCHIVE.txt"

if command -v shasum >/dev/null; then
  (cd "${HERE}/data/phase7" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 shasum -a 256) \
    > "${HERE}/data/phase7/SHA256SUMS" || true
fi

# --- 4. Full Downloads rsync ---
echo "rsync clone → ${DEST}"
RAMSEY_DOWNLOADS="${DEST}" bash "${HERE}/scripts/sync-to-downloads.sh"

# Overlay labelled campaign folders (rsync already copied data/)
mkdir -p "${DEST}/phase7-from-pod" "${DEST}/phase5-from-pod" "${DEST}/a40-from-pod"
[[ -d "${HERE}/data/phase7" ]] && cp -a "${HERE}/data/phase7/." "${DEST}/phase7-from-pod/"
[[ -d "${HERE}/data/phase5" ]] && cp -a "${HERE}/data/phase5/." "${DEST}/phase5-from-pod/"
[[ -d "${HERE}/data/a40" ]] && cp -a "${HERE}/data/a40/." "${DEST}/a40-from-pod/"

cat > "${DEST}/SNAPSHOT.txt" <<EOF
Ramsey-GPU-Constructions reproducibility snapshot
copied_from=${HERE}
copied_at=${STAMP}
git_head=${HEAD}
pod_reached=${pod_ok}

This folder is a full copy of the git clone minus .git / node_modules / .so
at the kernel path. Do not git push from here.

Campaigns on disk
  2a–4c   data/a40/catalog-2a.json  data/a40/catalog-4abc.json
          data/a40/pod-keep/        (raw A40 catalogues before phase5 reset)
  5a–5f   data/phase5/              phase5-from-pod/
  6a–7f   data/phase7/phase7.log    (tee of the A40 night)
  7c1     same log; SUMMARY.txt     phase7-from-pod/

Docs to replay
  docs/REPRODUCING.md
  docs/PHASE5-CAMPAIGN.md
  docs/PHASE7-CAMPAIGN.md
  docs/JOB-PHASE7.md
  docs/JOB-7C1.md
  docs/JOB-6A.md
  docs/WHERE-TO-LOOK.md
  docs/A40-CAMPAIGN.md
  data/yu_r4_20.json

Published cell is still 252. No CELL? in 7a–7f or 7c1.

Stop the pod after this script. Do not Terminate.
EOF

cp "${DEST}/SNAPSHOT.txt" "${HERE}/data/phase7/SNAPSHOT-DOWNLOADS.txt" 2>/dev/null || true

echo
echo "git clone phase7 archive: ${HERE}/data/phase7"
echo "Downloads snapshot:       ${DEST}"
echo "Downloads phase7:         ${DEST}/phase7-from-pod"
echo "Downloads phase5:         ${DEST}/phase5-from-pod"
echo "Downloads 2a–4c:          ${DEST}/a40-from-pod"
echo
if [[ -f "${HERE}/data/phase7/phase7.log" ]]; then
  echo "phase7.log bytes: $(wc -c < "${HERE}/data/phase7/phase7.log")"
  grep -E '\[7c1\] summary|job 7c1 done|job 7[a-f] done' "${HERE}/data/phase7/phase7.log" | tail -n 20 || true
else
  echo "WARNING: data/phase7/phase7.log still missing."
fi
echo
echo "Then from this Mac clone:"
echo "  git add data/phase7 docs/PHASE7-CAMPAIGN.md docs/REPRODUCING.md"
echo "  git commit -m \"Archive phase7 and 7c1 A40 log.\""
echo "  git push github main && git push origin main"
echo
ls -la "${HERE}/data/phase7" "${DEST}/phase7-from-pod" 2>/dev/null | head -n 40
