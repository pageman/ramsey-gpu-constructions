#!/usr/bin/env bash
# Read phase5 heartbeat. Run on the POD (or on a copy of data/).
set -euo pipefail
ROOT=""
for cand in \
  /workspace/ramsey-gpu-constructions \
  /workspace \
  "$(cd "$(dirname "$0")/.." && pwd)"; do
  if [[ -d "${cand}/data" ]]; then
    ROOT="${cand}"
    break
  fi
done
cd "${ROOT}"
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) Zulu / $(TZ=Asia/Singapore date +%Y-%m-%dT%H:%M:%S) GMT+8 ==="
echo "root ${ROOT}"
echo
if tmux has-session -t ramsey5 2>/dev/null; then
  echo "tmux ramsey5: ALIVE"
  tmux list-panes -t ramsey5 -F "  pane cmd=#{pane_current_command}"
else
  echo "tmux ramsey5: gone (finished, crashed, or never started)"
fi
echo
if [[ -f data/phase5.halt ]]; then
  echo "HALT FILE:"
  cat data/phase5.halt
  echo
fi
if [[ -f data/phase5.status.json ]]; then
  echo "STATUS:"
  python3 -m json.tool data/phase5.status.json
  echo
fi
if [[ -f data/yu_r4_20.cert.json ]]; then
  echo "YU CERT (alpha_certified is the only green light):"
  python3 - <<'PY'
import json
c=json.load(open("data/yu_r4_20.cert.json"))
print("  alpha_certified", c.get("alpha_certified"))
print("  residual_n", c.get("residual_n"))
print("  backend", c.get("backend"))
d=c.get("decide") or {}
print("  found", d.get("found"), "timed_out", d.get("timed_out"), "nodes", d.get("nodes"), "s", d.get("seconds"))
PY
  echo
fi
echo "LOG TAIL:"
tail -n 25 data/phase5.log 2>/dev/null || echo "  (no data/phase5.log yet)"
echo
echo "CELL? lines (must be none unless mixed_ok and residual ≤256):"
grep -n "CELL?" data/phase5.log 2>/dev/null || echo "  none"
