#!/usr/bin/env bash
# Copy this repo (and optionally A40 pod data) to ~/Downloads/Ramsey-GPU-Constructions
set -euo pipefail

DEST="${RAMSEY_DOWNLOADS:-$HOME/Downloads/Ramsey-GPU-Constructions}"
# Repo root: this script lives in <repo>/scripts/
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$DEST"/{data,docs,engine,src,public,a40-from-pod}

echo "== copy repo → $DEST =="
if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.git/' \
    --exclude 'node_modules/' \
    --exclude '.next/' \
    --exclude 'Downloads/' \
    --exclude '__pycache__/' \
    --exclude '*.so' \
    --exclude 'data/adj/' \
    --exclude '.venv/' \
    --exclude 'agent-tools/' \
    "$ROOT/" "$DEST/"
else
  # Cloud agent image has no rsync; tar excludes are portable.
  tar -C "$ROOT" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='Downloads' \
    --exclude='__pycache__' \
    --exclude='*.so' \
    --exclude='data/adj' \
    --exclude='.venv' \
    --exclude='agent-tools' \
    -cf - . | tar -C "$DEST" -xf -
fi

# Keep a40-from-pod if we already pulled (rsync --delete would wipe it if empty in ROOT)
mkdir -p "$DEST/a40-from-pod"

if [[ -n "${RAMSEY_POD_HOST:-}" && -n "${RAMSEY_POD_PORT:-}" ]]; then
  KEY="${RAMSEY_POD_KEY:-$HOME/.ssh/id_ed25519}"
  echo "== scp A40 data $RAMSEY_POD_HOST:$RAMSEY_POD_PORT → $DEST/a40-from-pod =="
  scp -o StrictHostKeyChecking=accept-new \
    -P "$RAMSEY_POD_PORT" -i "$KEY" \
    "root@${RAMSEY_POD_HOST}:/workspace/ramsey-gpu-constructions/data/catalog.json" \
    "root@${RAMSEY_POD_HOST}:/workspace/ramsey-gpu-constructions/data/registry.jsonl" \
    "root@${RAMSEY_POD_HOST}:/workspace/ramsey-gpu-constructions/data/mask_ranker.json" \
    "root@${RAMSEY_POD_HOST}:/workspace/ramsey-gpu-constructions/data/bound_ledger.json" \
    "root@${RAMSEY_POD_HOST}:/workspace/ramsey-gpu-constructions/data/ramsey_constructions.csv" \
    "$DEST/a40-from-pod/" || echo "scp failed — check RunPod IP/port in the UI"
else
  echo "Skip pod scp (set RAMSEY_POD_HOST and RAMSEY_POD_PORT to pull A40 data)."
fi

cat > "$DEST/SNAPSHOT.txt" <<EOF
Ramsey-GPU-Constructions snapshot
copied_from=$ROOT
copied_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
git=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)

This folder is a full copy of the repo minus node_modules/.next/.git.

A40 (RunPod) campaign dumps:
  data/a40/           jobs 2a + 4abc (committed)
  data/phase5/        jobs 5a–5f archive
  data/phase7/        jobs 6a–7f + 7c1 (after mac-finish-archive.sh)
  a40-from-pod/       labelled copy of data/a40
  phase5-from-pod/    labelled copy of data/phase5
  phase7-from-pod/    labelled copy of data/phase7

The in-tree data/catalog.json may be a local-scale dashboard extract.
Do not Terminate the pod (volume wipe). Stop is OK after archive.
Published cell is still 252.
EOF

echo "Done. Open $DEST"
ls -la "$DEST/data" "$DEST/a40-from-pod" 2>/dev/null || true
