#!/usr/bin/env bash
# Second-solver recertify. Safe on Mac or pod. Not a hunt.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
if [[ ! -f data/yu_r4_20.json ]]; then
  echo "Need data/yu_r4_20.json in ${ROOT}"
  exit 1
fi

export PYTHONUNBUFFERED=1
export RAMSEY_6A_LIMIT="${RAMSEY_6A_LIMIT:-180}"
python3 -m pip install --user ortools
SCALE=local
if [[ "$(uname -s)" != "Darwin" ]]; then
  SCALE="${RAMSEY_SCALE:-runpod}"
fi
python3 -u -m engine.cli --job 6a --scale "${SCALE}"
python3 - <<'PY'
import json
from pathlib import Path
p = Path("data/yu_r4_20.cert2.json")
c = json.loads(p.read_text())
print("cert2", p)
print("second_solver_agrees", c.get("second_solver_agrees"))
print("no_19_is", c.get("no_19_is"))
print("cpsat_19", c.get("cpsat_19"))
print("cpsat_18", c.get("cpsat_18"))
PY
