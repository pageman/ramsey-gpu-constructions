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

A40 (RunPod) catalogue — if a40-from-pod/catalog.json exists it is the
2a Hoffman sweep (~9288 graphs) plus registry lines for 3d n=13/14.
The in-tree data/ folder is the *local-scale* catalogue (this laptop/cloud
agent), including jobs 4a/4b/4c dry-runs.

Do not Terminate the pod (volume wipe). Stop is OK after scp.
EOF

echo "Done. Open $DEST"
ls -la "$DEST/data" "$DEST/a40-from-pod" 2>/dev/null || true
