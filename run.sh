#!/usr/bin/env bash
# Convenience wrapper for a local docker run that mimics a RunPod post_start.
set -euo pipefail
export RAMSEY_JOB="${RAMSEY_JOB:-phase0}"
export RAMSEY_SCALE="${RAMSEY_SCALE:-local}"
python3 -m engine.cli --job "${RAMSEY_JOB}" --scale "${RAMSEY_SCALE}"
