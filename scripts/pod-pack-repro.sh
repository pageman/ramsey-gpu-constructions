#!/usr/bin/env bash
# Run ON THE POD. Writes one tarball for extreme reproducibility.
set -euo pipefail

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "WRONG MACHINE. Run this on the pod:  bash scripts/pod-pack-repro.sh"
  exit 2
fi

ROOT=""
for cand in \
  /workspace/ramsey-gpu-constructions \
  /workspace \
  "$(cd "$(dirname "$0")/.." && pwd)"; do
  if [[ -f "${cand}/engine/cli.py" ]]; then
    ROOT="${cand}"
    break
  fi
done
if [[ -z "${ROOT}" ]]; then
  echo "Cannot find the repo on this machine."
  exit 1
fi
cd "${ROOT}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="/tmp/ramsey-repro-pack"
DEST="/workspace/ramsey-repro-${STAMP}.tgz"
rm -rf "${OUT}"
mkdir -p "${OUT}/phase5" "${OUT}/keep-a40" "${OUT}/binaries" "${OUT}/meta" "${OUT}/engine-src"

copy_if() {
  local src="$1"
  local dir="$2"
  if [[ -e "${src}" ]]; then
    cp -a "${src}" "${dir}/"
  fi
}

copy_if data/phase5.log "${OUT}/phase5"
copy_if data/phase5.status.json "${OUT}/phase5"
copy_if data/phase5.halt "${OUT}/phase5"
copy_if data/yu_r4_20.cert.json "${OUT}/phase5"
copy_if data/yu_r4_20.json "${OUT}/phase5"
copy_if data/catalog.json "${OUT}/phase5"
copy_if data/registry.jsonl "${OUT}/phase5"
copy_if data/bound_ledger.json "${OUT}/phase5"
copy_if data/ramsey_constructions.csv "${OUT}/phase5"

if [[ -d /workspace/keep-a40 ]]; then
  cp -a /workspace/keep-a40/. "${OUT}/keep-a40/"
fi

copy_if engine/kernels/native_decide.so "${OUT}/binaries"
copy_if engine/kernels/native_mis.so "${OUT}/binaries"
copy_if engine/kernels/native_decide.c "${OUT}/engine-src"
copy_if engine/kernels/native_mis.c "${OUT}/engine-src"
copy_if engine/kernels/decide_alpha.py "${OUT}/engine-src"
copy_if engine/phase5.py "${OUT}/engine-src"

{
  echo "packed_utc=${STAMP}"
  echo "repo_root=${ROOT}"
  echo "git_head=$(git rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "git_subject=$(git log -1 --pretty=%s 2>/dev/null || echo unknown)"
  echo "uname=$(uname -a)"
  echo "hostname=$(hostname)"
  command -v gcc >/dev/null && gcc -v 2>&1 | tail -n 1
  command -v python3 >/dev/null && python3 --version
  if command -v nvidia-smi >/dev/null; then
    nvidia-smi -L || true
  fi
  echo "OMP_NUM_THREADS=${OMP_NUM_THREADS:-unset}"
  echo "RAMSEY_SCALE=${RAMSEY_SCALE:-unset}"
  echo "RAMSEY_5A_LIMIT=${RAMSEY_5A_LIMIT:-unset}"
  python3 - <<'PY'
from engine.scale import limits, scale_name
print("scale_name", scale_name())
print("limits", limits())
PY
} > "${OUT}/meta/env.txt" 2>&1

git rev-parse HEAD > "${OUT}/meta/git-head.txt" 2>/dev/null || true
git log -1 --pretty=fuller > "${OUT}/meta/git-log.txt" 2>/dev/null || true
git status --short > "${OUT}/meta/git-status.txt" 2>/dev/null || true

if command -v sha256sum >/dev/null; then
  (cd "${OUT}" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "${OUT}/meta/SHA256SUMS"
else
  echo "sha256sum not installed" > "${OUT}/meta/SHA256SUMS"
fi

tar -C "${OUT}" -czf "${DEST}" .
ls -lh "${DEST}"
echo "${DEST}"
echo "PACK_OK ${DEST}"
