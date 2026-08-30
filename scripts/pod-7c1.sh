#!/usr/bin/env bash
# One 7c1 hunt. Not phase7. Not 7c. Run ON THE POD. Prompt must be root@…
set -euo pipefail

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "WRONG MACHINE. Prompt is the Mac. SSH first, then: bash scripts/pod-7c1.sh"
  exit 2
fi

ROOT=""
for cand in \
  /workspace/ramsey-gpu-constructions \
  /workspace \
  "$(cd "$(dirname "$0")/.." && pwd)"; do
  if [[ -f "${cand}/engine/cli.py" && -f "${cand}/engine/cegis_pool.py" ]]; then
    ROOT="${cand}"
    break
  fi
done
if [[ -z "${ROOT}" ]]; then
  echo "Cannot find engine/cegis_pool.py. git pull origin main first."
  exit 1
fi
cd "${ROOT}"

SESSION="${RAMSEY_TMUX_SESSION:-ramsey7c1}"
LOG="${ROOT}/data/phase7.log"
mkdir -p "${ROOT}/data"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux missing."
  exit 1
fi

python3 - <<'PY'
from engine.jobs import JOBS
if "7c1" not in JOBS:
    raise SystemExit("CLI missing 7c1. Pull latest main.")
print("7c1 registered")
try:
    from ortools.sat.python import cp_model  # noqa: F401
    print("ortools ok")
except ImportError:
    raise SystemExit("ortools missing. python3 -m pip install --user ortools")
PY

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "[pod-7c1] ${SESSION} already exists. Refusing a second hunt."
  echo "  capture: tmux capture-pane -t ${SESSION} -p | tail"
  echo "  log:     grep '\\[7c1\\]' data/phase7.log | tail"
  exit 3
fi

export PYTHONUNBUFFERED=1
export RAMSEY_SCALE="${RAMSEY_SCALE:-runpod}"
export RAMSEY_FORCE_7="${RAMSEY_FORCE_7:-1}"

tmux new-session -d -s "${SESSION}" -c "${ROOT}" \
  "export PYTHONUNBUFFERED=1 RAMSEY_SCALE=${RAMSEY_SCALE} RAMSEY_FORCE_7=${RAMSEY_FORCE_7}; \
   echo \"[7c1] start \$(date -u +%Y-%m-%dT%H:%M:%SZ) Zulu\"; \
   python3 -u -m engine.cli --job 7c1 --scale runpod 2>&1 | tee -a ${LOG}; \
   echo \"[7c1] exit \$? at \$(date -u +%Y-%m-%dT%H:%M:%SZ) Zulu\""

sleep 2
if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session vanished. Last 40 lines of ${LOG}:"
  tail -n 40 "${LOG}" 2>/dev/null || true
  exit 1
fi

echo
echo "============================================================"
echo " 7c1 is running in tmux session: ${SESSION}"
echo " log: ${LOG}"
echo " attach: tmux attach -t ${SESSION}   (prefix+d to detach; do not type)"
echo " do NOT attach tmux ramsey or ramsey5."
echo " do NOT run pod-phase7.sh or --job 7c."
echo " do NOT Terminate the pod."
echo "============================================================"
echo
grep -n '\[7c1\]\|job 7c1' "${LOG}" | tail -n 15 || echo "(no [7c1] lines yet — wait 5s and grep again)"
