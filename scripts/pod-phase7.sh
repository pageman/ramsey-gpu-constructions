#!/usr/bin/env bash
# One command. Creates tmux ramsey7 and starts phase7 INSIDE it.
# Run this ON THE POD. Never on the Mac. Never paste tmux + python together.
set -euo pipefail

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "WRONG MACHINE. Prompt is the Mac (MacBook-Pro). /workspace is the pod."
  echo "SSH first. Only after the prompt is root@… run:  bash scripts/pod-phase7.sh"
  exit 2
fi

ROOT=""
for cand in \
  /workspace/ramsey-gpu-constructions \
  /workspace \
  "$(cd "$(dirname "$0")/.." && pwd)"; do
  if [[ -f "${cand}/engine/cli.py" && -f "${cand}/engine/phase7.py" ]]; then
    ROOT="${cand}"
    break
  fi
done
if [[ -z "${ROOT}" ]]; then
  echo "Cannot find the repo (engine/phase7.py). git pull origin main first."
  exit 1
fi
cd "${ROOT}"

SESSION="${RAMSEY_TMUX_SESSION:-ramsey7}"
LOG="${ROOT}/data/phase7.log"
mkdir -p "${ROOT}/data"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux missing. On the pod: apt-get update && apt-get install -y tmux"
  exit 1
fi
if ! command -v gcc >/dev/null 2>&1; then
  echo "gcc missing. On the pod: apt-get update && apt-get install -y build-essential"
  exit 1
fi

echo "[pod-phase7] root=${ROOT}"
echo "[pod-phase7] compiling native_decide (OpenMP)"
gcc -O3 -shared -fPIC -fopenmp -o engine/kernels/native_decide.so engine/kernels/native_decide.c \
  || gcc -O3 -shared -fPIC -o engine/kernels/native_decide.so engine/kernels/native_decide.c

export PYTHONUNBUFFERED=1
export RAMSEY_SCALE="${RAMSEY_SCALE:-runpod}"
export RAMSEY_6A_LIMIT="${RAMSEY_6A_LIMIT:-600}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-12}"

echo "[pod-phase7] python check"
python3 - <<'PY'
from engine.jobs import JOBS
need = ["6a", "7a", "7b", "7c", "7d", "7e", "7f", "phase7"]
missing = [j for j in need if j not in JOBS]
if missing:
    raise SystemExit(f"CLI missing {missing}. Pull latest main.")
print("jobs_ok", " ".join(need))
PY

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  if tmux list-panes -t "${SESSION}" -F "#{pane_current_command}" | grep -Eiq 'python|engine'; then
    echo "[pod-phase7] ${SESSION} already has a python pane. Refusing a second hunt."
    echo "  attach:  tmux attach -t ${SESSION}"
    echo "  status:  bash scripts/phase7-status.sh"
    exit 3
  fi
  tmux kill-session -t "${SESSION}"
fi

tmux new-session -d -s "${SESSION}" -c "${ROOT}" \
  "export PYTHONUNBUFFERED=1 RAMSEY_SCALE=${RAMSEY_SCALE} RAMSEY_6A_LIMIT=${RAMSEY_6A_LIMIT} OMP_NUM_THREADS=${OMP_NUM_THREADS}; \
   echo \"[phase7] start \$(date -u +%Y-%m-%dT%H:%M:%SZ) Zulu\"; \
   python3 -u -m engine.cli --job phase7 --scale runpod 2>&1 | tee -a ${LOG}; \
   echo \"[phase7] exit \$? at \$(date -u +%Y-%m-%dT%H:%M:%SZ) Zulu\""

sleep 1
if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session vanished. Last 40 lines of ${LOG}:"
  tail -n 40 "${LOG}" 2>/dev/null || true
  exit 1
fi

echo
echo "============================================================"
echo " phase7 is running in tmux session: ${SESSION}"
echo " log: ${LOG}"
echo " status: bash scripts/phase7-status.sh"
echo " attach: tmux attach -t ${SESSION}"
echo " do NOT attach tmux ramsey (leftover 2a) or ramsey5 (phase5 done)."
echo " do NOT Terminate the pod. Stop is OK after scp."
echo "============================================================"
echo
sleep 2
tail -n 20 "${LOG}" 2>/dev/null || echo "(log not flushed yet)"
