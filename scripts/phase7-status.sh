#!/usr/bin/env bash
# Read phase7 status. Safe on Mac or pod.
set -euo pipefail
ROOT=""
for cand in \
  /workspace/ramsey-gpu-constructions \
  /workspace \
  "$(cd "$(dirname "$0")/.." && pwd)"; do
  if [[ -f "${cand}/engine/phase7.py" ]]; then
    ROOT="${cand}"
    break
  fi
done
if [[ -z "${ROOT}" ]]; then
  echo "repo not found"
  exit 1
fi
echo "root ${ROOT}"
if [[ -f "${ROOT}/data/phase7.status.json" ]]; then
  python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1])), indent=2))" \
    "${ROOT}/data/phase7.status.json"
else
  echo "no data/phase7.status.json yet"
fi
if [[ -f "${ROOT}/data/yu_r4_20.cert2.json" ]]; then
  python3 -c "import json; c=json.load(open('${ROOT}/data/yu_r4_20.cert2.json')); print('6a second_solver_agrees', c.get('second_solver_agrees'), 'backend', c.get('backend'))"
else
  echo "6a cert2 missing"
fi
if [[ -f "${ROOT}/data/phase7.halt" ]]; then
  echo "HALT:" "$(cat "${ROOT}/data/phase7.halt")"
fi
if [[ -f "${ROOT}/data/phase7.log" ]]; then
  echo "---- last 15 log lines ----"
  tail -n 15 "${ROOT}/data/phase7.log"
fi
if command -v tmux >/dev/null 2>&1; then
  tmux has-session -t ramsey7 2>/dev/null && echo "tmux ramsey7: live" || echo "tmux ramsey7: none"
fi
