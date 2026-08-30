"""CLI: python3 -m engine.cli --job 1a   (or RAMSEY_JOB=1a)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="RunPod-ready Ramsey construction jobs")
    p.add_argument("--job", default=os.environ.get("RAMSEY_JOB", "phase0"), help="phase0|1a…5f|phase5|6a|7a…7f|phase7")
    p.add_argument("--scale", default=os.environ.get("RAMSEY_SCALE"), help="local|runpod")
    p.add_argument("--list", action="store_true")
    args = p.parse_args(argv)
    if args.scale:
        os.environ["RAMSEY_SCALE"] = args.scale
    from engine.jobs import JOBS, run_job
    from engine.scale import scale_name
    from engine import backend

    if args.list:
        print("scale", scale_name(), "device", backend.device_name())
        print("jobs", " ".join(JOBS))
        return 0
    jobs = [j.strip() for j in args.job.split(",") if j.strip()]
    if args.job in ("phase1", "all-phase1"):
        jobs = ["1a", "1b", "1c", "1d"]
    elif args.job in ("phase2", "all-phase2"):
        jobs = ["2a", "2b", "2c"]
    elif args.job in ("phase3", "all-phase3"):
        jobs = ["3a", "3b", "3c", "3d"]
    elif args.job in ("phase4", "all-phase4"):
        jobs = ["4a", "4b", "4c"]
    elif args.job in ("phase5", "all-phase5"):
        jobs = ["phase5"]
    elif args.job in ("phase7", "all-phase7"):
        jobs = ["phase7"]
    elif args.job in ("all",):
        jobs = ["phase0", "1a", "1b", "1c", "1d", "2a", "2c", "3a", "3b", "3c", "3d", "4a", "4b", "4c", "phase5"]
    for j in jobs:
        run_job(j)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
