#!/usr/bin/env bash
# RunPod base image executes /post_start.sh after SSH/Jupyter are up.
set -euo pipefail
cd /workspace 2>/dev/null || cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
export RAMSEY_SCALE="${RAMSEY_SCALE:-runpod}"
JOB="${RAMSEY_JOB:-phase0}"
echo "[ramsey] device check"
python3 - <<'PY'
from engine import backend
print("device", backend.device_name(), "cuda", backend.CUDA_AVAILABLE)
PY
echo "[ramsey] starting job=${JOB} scale=${RAMSEY_SCALE}"
python3 -m engine.cli --job "${JOB}" --scale "${RAMSEY_SCALE}"
echo "[ramsey] job ${JOB} finished"
