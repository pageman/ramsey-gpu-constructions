"""Job 6a: second-solver recertify of Yu residual 186 (not a hunt)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from .kernels.residual import distances_to_row, residual_nbr
from .kernels.bitset_mcs import greedy_mis
from .registry import append_record
from .yu_pool import load_yu_witness

ROOT = Path(__file__).resolve().parents[1]
CERT2 = ROOT / "data" / "yu_r4_20.cert2.json"
CERT2_ARCHIVE = ROOT / "data" / "phase5" / "yu_r4_20.cert2.json"
DIMACS = ROOT / "data" / "yu_r4_20.complement.clq"


def load_cert2() -> dict | None:
    for path in (CERT2, CERT2_ARCHIVE):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
    return None


def six_a_green() -> bool:
    """True only if a second solver finished and reported no 19-IS."""
    rec = load_cert2()
    if not rec:
        return False
    if rec.get("cpsat_19", {}).get("found"):
        return False
    return bool(rec.get("second_solver_agrees") and rec.get("no_19_is"))


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def residual_from_yu() -> tuple[list[int], dict]:
    w = load_yu_witness()
    row = distances_to_row(int(w["p"]), w["S"])
    nbr = residual_nbr(row)
    meta = {
        "p": int(w["p"]),
        "citation": w.get("citation"),
        "S": list(w["S"]),
        "residual_n": len(nbr),
        "greedy_alpha_residual": greedy_mis(nbr),
    }
    return nbr, meta


def write_complement_dimacs(nbr: list[int], path: Path = DIMACS) -> dict:
    """DIMACS clique instance: complement of the residual (clique 19 ⇔ IS 19)."""
    n = len(nbr)
    edges: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            if ((nbr[i] >> j) & 1) == 0:
                edges.append((i + 1, j + 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "c Yu residual complement. Clique of size 19 ⇔ residual IS of size 19.",
        f"c n={n} complement_edges={len(edges)}",
        f"p edge {n} {len(edges)}",
    ]
    lines.extend(f"e {u} {v}" for u, v in edges)
    path.write_text("\n".join(lines) + "\n")
    return {"path": str(path), "n": n, "edges": len(edges)}


def cpsat_decide(nbr: list[int], want: int, seconds: float) -> dict:
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return {"available": False, "found": False, "timed_out": False, "reason": "ortools not installed"}
    n = len(nbr)
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"v{i}") for i in range(n)]
    for i in range(n):
        mask = int(nbr[i])
        j = 0
        while mask and j < n:
            if (mask & 1) and j > i:
                model.Add(xs[i] + xs[j] <= 1)
            mask >>= 1
            j += 1
    model.Add(sum(xs) >= int(want))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = int(os.environ.get("RAMSEY_SAT_WORKERS", "8"))
    t0 = time.perf_counter()
    status = solver.Solve(model)
    elapsed = time.perf_counter() - t0
    found = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    unsat = status == cp_model.INFEASIBLE
    unknown = status == cp_model.UNKNOWN
    return {
        "available": True,
        "found": found,
        "unsat": unsat,
        "timed_out": unknown and not found and not unsat,
        "status": int(status),
        "status_name": solver.StatusName(status),
        "seconds": elapsed,
        "want": want,
        "backend": "ortools-cp-sat",
    }


def cliquer_decide(dimacs: Path, want: int, seconds: float) -> dict:
    exe = shutil.which("cliquer")
    if not exe:
        return {"available": False, "found": False, "reason": "cliquer not on PATH"}
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            [exe, "-u", str(want), str(dimacs)],
            capture_output=True,
            text=True,
            timeout=float(seconds) + 5,
        )
    except subprocess.TimeoutExpired:
        return {"available": True, "found": False, "timed_out": True, "backend": "cliquer", "seconds": seconds}
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    found = "size" in text.lower() and str(want) in text
    if "not found" in text.lower() or "no clique" in text.lower():
        found = False
    return {
        "available": True,
        "found": found,
        "timed_out": False,
        "seconds": time.perf_counter() - t0,
        "returncode": proc.returncode,
        "tail": text[-400:],
        "backend": "cliquer",
    }


def job_6a() -> list[dict]:
    """Second solver on Yu residual 186. Writes data/yu_r4_20.cert2.json."""
    tlim = float(os.environ.get("RAMSEY_6A_LIMIT", "180"))
    print(f"  [6a] second solver on Yu residual 186  limit={tlim}s", flush=True)
    nbr, meta = residual_from_yu()
    if meta["residual_n"] != 186:
        raise SystemExit(f"6a expected residual 186, got {meta['residual_n']}")
    dimacs = write_complement_dimacs(nbr)
    print(f"  [6a] wrote {dimacs['path']}  n={dimacs['n']} complement_edges={dimacs['edges']}", flush=True)

    sat19 = cpsat_decide(nbr, want=19, seconds=tlim)
    print(f"  [6a] CP-SAT α≥19 {sat19}", flush=True)
    sat18 = cpsat_decide(nbr, want=18, seconds=min(60.0, tlim))
    print(f"  [6a] CP-SAT α≥18 {sat18}", flush=True)
    clq = cliquer_decide(DIMACS, want=19, seconds=tlim)
    print(f"  [6a] Cliquer clique-19 {clq}", flush=True)

    no19 = False
    backend = None
    if sat19.get("available") and sat19.get("unsat") and not sat19.get("timed_out"):
        no19 = True
        backend = "ortools-cp-sat"
    clq_clear_no = bool(
        clq.get("available")
        and not clq.get("found")
        and not clq.get("timed_out")
        and ("not found" in (clq.get("tail") or "").lower() or "no clique" in (clq.get("tail") or "").lower())
    )
    if clq_clear_no:
        no19 = True
        backend = "cliquer" if backend is None else f"{backend}+cliquer"

    payload = {
        "job": "6a",
        "written_utc": _now(),
        "residual_n": 186,
        "target": 19,
        "dimacs": dimacs,
        "cpsat_19": sat19,
        "cpsat_18": sat18,
        "cliquer_19": clq,
        "no_19_is": no19,
        "second_solver_agrees": no19,
        "backend": backend,
        "note": (
            "Independent of c-decide. no_19_is true only if CP-SAT reports INFEASIBLE "
            "or Cliquer finishes without a 19-clique. An 18-IS is a lower bound only. "
            "This does not move R(4,20) off 252."
        ),
        **meta,
    }
    CERT2.parent.mkdir(parents=True, exist_ok=True)
    CERT2.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(f"  [6a] wrote {CERT2}  no_19_is={no19}  backend={backend}", flush=True)
    append_record(
        {
            "job": "6a",
            "cell": "R(4,20)",
            "graph_id": "yu_residual_186_cert2",
            "N": 186,
            "exact": no19,
            "second_solver_agrees": no19,
            "backend": backend,
        }
    )
    if not sat19.get("available") and not clq.get("available"):
        print(
            "  [6a] no second solver installed. On the pod or Mac:  python3 -m pip install ortools",
            flush=True,
        )
    return []
