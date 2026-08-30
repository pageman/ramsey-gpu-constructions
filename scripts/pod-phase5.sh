#!/usr/bin/env bash
# One command. Creates tmux ramsey5 and starts phase5 INSIDE it.
# Run this ON THE POD. Never on the Mac. Never paste tmux + python together.
set -euo pipefail

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "WRONG MACHINE. This script is for the RunPod container, not the Mac."
  echo "SSH to the pod first (RunPod UI → Connect → SSH over exposed TCP)."
  exit 2
fi

if [[ -n "${SSH_CONNECTION:-}" ]] && [[ "$(hostname)" == *Mac* ]]; then
  echo "WRONG MACHINE (hostname looks like a Mac)."
  exit 2
fi

ROOT=""
for cand in \
  /workspace/ramsey-gpu-constructions \
  /workspace \
  "$(cd "$(dirname "$0")/.." && pwd)"; do
  if [[ -f "${cand}/engine/cli.py" && -f "${cand}/data/yu_r4_20.json" ]]; then
    ROOT="${cand}"
    break
  fi
done
if [[ -z "${ROOT}" ]]; then
  echo "Cannot find the repo (engine/cli.py + data/yu_r4_20.json)."
  echo "On the pod: cd /workspace/ramsey-gpu-constructions && git pull && bash scripts/pod-phase5.sh"
  exit 1
fi
cd "${ROOT}"

SESSION="${RAMSEY_TMUX_SESSION:-ramsey5}"
LOG="${ROOT}/data/phase5.log"
mkdir -p "${ROOT}/data"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux missing. On the pod: apt-get update && apt-get install -y tmux"
  exit 1
fi

if ! command -v gcc >/dev/null 2>&1; then
  echo "gcc missing. On the pod: apt-get update && apt-get install -y build-essential"
  exit 1
fi

echo "[pod-phase5] root=${ROOT}"
echo "[pod-phase5] compiling native_decide (OpenMP) and native_mis"
gcc -O3 -shared -fPIC -fopenmp -o engine/kernels/native_decide.so engine/kernels/native_decide.c \
  || gcc -O3 -shared -fPIC -o engine/kernels/native_decide.so engine/kernels/native_decide.c
gcc -O3 -shared -fPIC -o engine/kernels/native_mis.so engine/kernels/native_mis.c

export PYTHONUNBUFFERED=1
export RAMSEY_SCALE="${RAMSEY_SCALE:-runpod}"
export RAMSEY_5A_LIMIT="${RAMSEY_5A_LIMIT:-1800}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-12}"

echo "[pod-phase5] python check"
python3 - <<'PY'
from engine.cli import main
from engine.jobs import JOBS
need = ["5a", "5b", "5c", "5d", "5e", "5f", "phase5"]
missing = [j for j in need if j not in JOBS]
if missing:
    raise SystemExit(f"CLI missing {missing}. Pull latest main.")
print("jobs_ok", " ".join(need))
from engine.kernels.decide_alpha import decide_alpha_le
print("decide", decide_alpha_le([0, 0], 2, time_limit=0.1))
PY

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  if tmux list-panes -t "${SESSION}" -F "#{pane_current_command}" | grep -Eiq 'python|engine'; then
    echo "[pod-phase5] ${SESSION} already has a python pane. Refusing to start a second hunt."
    echo "  attach:  tmux attach -t ${SESSION}"
    echo "  status:  bash scripts/phase5-status.sh"
    echo "  kill:    tmux kill-session -t ${SESSION}   # only if you mean it"
    exit 3
  fi
  echo "[pod-phase5] leftover session ${SESSION} with no python — killing it"
  tmux kill-session -t "${SESSION}"
fi

# Start python INSIDE tmux. Operator types ONE line. Detach is automatic.
tmux new-session -d -s "${SESSION}" -c "${ROOT}" \
  "export PYTHONUNBUFFERED=1 RAMSEY_SCALE=${RAMSEY_SCALE} RAMSEY_5A_LIMIT=${RAMSEY_5A_LIMIT} OMP_NUM_THREADS=${OMP_NUM_THREADS}; \
   echo \"[phase5] start \$(date -u +%Y-%m-%dT%H:%M:%SZ) Zulu\"; \
   python3 -u -m engine.cli --job phase5 --scale runpod 2>&1 | tee -a ${LOG}; \
   echo \"[phase5] exit \$? at \$(date -u +%Y-%m-%dT%H:%M:%SZ) Zulu\"; \
   echo '[phase5] pane will sit here so you can read the tail; Ctrl-B D to detach'"

sleep 1
if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session vanished. Last 40 lines of ${LOG}:"
  tail -n 40 "${LOG}" 2>/dev/null || true
  exit 1
fi

echo
echo "============================================================"
echo " phase5 is running in tmux session: ${SESSION}"
echo " log: ${LOG}"
echo " status: bash scripts/phase5-status.sh"
echo
echo " detach (if you attached):   Ctrl-B then D"
echo " attach later:               tmux attach -t ${SESSION}"
echo " live tail from a NEW ssh:   tail -f ${LOG}"
echo " do NOT  Terminate the pod.  Stop is OK after scp."
echo " do NOT  attach tmux ramsey (that is leftover 2a)."
echo "============================================================"
echo
tmux ls
echo
echo "first log lines:"
sleep 2
tail -n 20 "${LOG}" 2>/dev/null || echo "(log not flushed yet — attach or tail -f)"
