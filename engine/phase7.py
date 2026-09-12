"""Phase 7: Look 1–6 after job 6a (WHERE-TO-LOOK.md).

Order: 6a gate → 7a referee bench → 7b 2-class hunt → 7c SAT-on-pool
if walks die → 7d R(3,t) t≥50 → 7e 2-polycirculant → 7f polarity leftover.
Standalone follow-on: 7c1 = SAT-on-pool + residual-IS CEGIS cuts (not max |S|).
Never Hoffman. Timeout ≠ accept. Residual >256 is a skip, not a cell.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from .kernels.decide_alpha import decide_alpha_le, mixed_set_check, shash_distances
from .kernels.residual import distances_to_row, greedy_alpha_row, nbhd_triangle_free, residual_nbr
from .kernels.bitset_mcs import greedy_mis
from .phase6 import job_6a, load_cert2, six_a_green
from .registry import append_record
from .scale import limits, scale_name
from .yu_pool import (
    R3_LOWER,
    R4_LOWER,
    anneal_pool,
    certify_row_decision,
    iter_yu_pools,
    lexmin_distances,
    load_yu_witness,
    min_residual,
    r4_cells_open,
    restricted_process,
)

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "data" / "phase7.status.json"
HALT_PATH = ROOT / "data" / "phase7.halt"
YU_S = set(int(x) for x in load_yu_witness()["S"])


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_status(**kwargs) -> None:
    prev = {}
    if STATUS_PATH.exists():
        try:
            prev = json.loads(STATUS_PATH.read_text())
        except json.JSONDecodeError:
            prev = {}
    prev.update(kwargs)
    prev["updated_utc"] = _now()
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(prev, indent=2, default=str) + "\n")


def require_6a() -> bool:
    """Run 6a if needed. Return True iff the hunt may start."""
    if six_a_green():
        print("  [phase7] 6a GREEN (second_solver_agrees)", flush=True)
        return True
    if os.environ.get("RAMSEY_FORCE_7") == "1":
        print("  [phase7] RAMSEY_FORCE_7=1 — hunt without 6a agree", flush=True)
        return True
    rec = load_cert2()
    if rec and rec.get("cpsat_19", {}).get("found"):
        print("  [phase7] HALT. CP-SAT found a 19-IS. Replay before hunting.", flush=True)
        HALT_PATH.write_text(f"6a found 19-IS at {_now()}\n")
        return False
    print("  [phase7] 6a not green — running job 6a first", flush=True)
    job_6a()
    if six_a_green():
        print("  [phase7] 6a GREEN after this run", flush=True)
        return True
    rec = load_cert2() or {}
    print(
        f"  [phase7] 6a did not agree  backend={rec.get('backend')} "
        f"timed_out={rec.get('cpsat_19', {}).get('timed_out')} "
        f"available={rec.get('cpsat_19', {}).get('available')}",
        flush=True,
    )
    if rec.get("cpsat_19", {}).get("timed_out"):
        print("  [phase7] HALT. 6a timeout ≠ proof. Raise RAMSEY_6A_LIMIT or FORCE_7=1.", flush=True)
    else:
        print("  [phase7] HALT. Install ortools (or cliquer) and rerun 6a.", flush=True)
    HALT_PATH.write_text(f"6a not green at {_now()}\n")
    write_status(job="6a", state="blocked", cert2=rec)
    return False


def job_7a() -> list[dict]:
    """Look 3: referee bench. Paley(17) regression; optional Yu 186 retime."""
    from .jobs import _decision_cert, emit_decision
    from .kernels.sieve import quadratic_residue_row

    print("  [7a] Look 3 referee bench (matching colour + flatten + complement χ)", flush=True)
    write_status(job="7a", state="running")
    prow = quadratic_residue_row(17)
    from .yu_pool import certify_row_decision as cert_row

    pcert = cert_row(prow, t_cell=4, time_limit=2.0)
    print(f"  [7a] Paley(17) {pcert.get('reason')} exact={pcert.get('exact')}", flush=True)
    if not pcert.get("exact"):
        raise SystemExit("7a Paley(17) regression failed")

    yu_bench = None
    if os.environ.get("RAMSEY_7A_YU") == "1" or scale_name() == "runpod":
        w = load_yu_witness()
        row = distances_to_row(int(w["p"]), w["S"])
        nbr = residual_nbr(row)
        tlim = float(os.environ.get("RAMSEY_7A_LIMIT", "180"))
        t0 = time.perf_counter()
        dec = decide_alpha_le(nbr, target=19, time_limit=tlim)
        yu_bench = {
            "found": dec["found"],
            "timed_out": dec["timed_out"],
            "nodes": dec["nodes"],
            "seconds": time.perf_counter() - t0,
            "backend": dec.get("backend"),
            "phase5_seconds": 63.17,
            "phase5_nodes": 216275634,
        }
        print(f"  [7a] Yu 186 retime {yu_bench}", flush=True)
        if dec["found"] and not dec["timed_out"]:
            raise SystemExit("7a found a 19-IS on Yu residual — bug until replayed")

    pack = _decision_cert(17, 3, 3, 3, True, "decide")
    meta = {
        "construction_type": "paley_prime",
        "gpu_kernel": "7a colour+flatten referee",
        "field": "F_17",
        "params": {"p": 17, "kind": "7a", "yu_bench": yu_bench},
        "run001": "done",
    }
    rec = emit_decision(prow, meta, pack, "7a", "cert")
    write_status(job="7a", state="done", paley17_exact=True, yu_bench=yu_bench)
    append_record({"job": "7a", "cell": "cert", "yu_bench": yu_bench, "exact": True})
    return [rec]


def _emit_yu_hit(spec: dict, S: list[int], row, cert: dict, t_cell: int, job: str) -> dict | None:
    from .jobs import _decision_cert, emit_decision

    resid = spec["p"] - 1 - int(row.sum())
    if resid > 256:
        print(f"  [{job}] drop residual {resid}>256", flush=True)
        return None
    mix = mixed_set_check(row, t_cell, time_limit=min(20.0, float(limits()["yu_mis_limit"])))
    cell_ok = bool(cert.get("exact") and not cert.get("rejected") and mix.get("mixed_ok"))
    published = R4_LOWER.get(t_cell, 0)
    beats = cell_ok and spec["p"] + 1 > published
    meta = {
        "construction_type": "yu_pool",
        "gpu_kernel": f"{job} process + decide_alpha_le",
        "field": f"Z/{spec['p']}Z",
        "params": {
            "p": spec["p"],
            "e": spec["e"],
            "i": spec["i"],
            "j": spec["j"],
            "kind": job,
            "t_cell": t_cell,
            "shash": shash_distances(S),
            "S": list(S),
            "mixed": mix.get("reason"),
        },
        "run001": "not_done",
    }
    pack = _decision_cert(
        spec["p"],
        3,
        int(cert.get("alpha_lower") or 0),
        cert.get("alpha_upper") if cell_ok else None,
        bool(beats),
        "decide",
    )
    rec = emit_decision(row, meta, pack, job, "R(4,t)")
    if beats:
        note = ""
        if t_cell in (23, 24):
            note = "  (floor is monotonic from R(4,22)≥314 — check DS1 r18)"
        print(
            f"  [{job}] CELL? R(4,{t_cell}) ≥ {spec['p'] + 1}  "
            f"(published ≥ {published})  mixed_ok{note}",
            flush=True,
        )
    elif cert.get("exact") and not cert.get("rejected"):
        print(
            f"  [{job}] residual_only p={spec['p']} resid={resid} t={t_cell}  {mix.get('reason')}",
            flush=True,
        )
    return rec


def _pick_t(spec: dict, greedy: int) -> int | None:
    """Smallest open t with greedy α < t. None if this n cannot beat any cell."""
    open_t = [t for t in r4_cells_open(spec["p"]) if greedy < t]
    return open_t[0] if open_t else None


def job_7b() -> list[dict]:
    """Look 1: other (i,j) at 251, then primes with min_resid≤256."""
    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        print("  [7b] HALT file — skip", flush=True)
        return []
    lim = limits()
    tlim = float(lim["yu_mis_limit"])
    walks = int(lim.get("look1_walks", lim["yu_walks"]))
    anneal = int(lim.get("look1_anneal", lim["yu_anneal"]))
    rng = np.random.default_rng(20260830)
    p_lo = int(lim.get("look1_p_lo", 251))
    p_hi = int(lim.get("look1_p_hi", lim["yu_p_hi"]))
    print(
        f"  [7b] Look 1 hunt p∈[{p_lo},{p_hi}] walks={walks} anneal={anneal} mis={tlim}s",
        flush=True,
    )
    write_status(job="7b", state="running", p_lo=p_lo, p_hi=p_hi)
    rows: list[dict] = []
    last_p = None
    for spec in iter_yu_pools(p_lo, p_hi):
        if spec["p"] != last_p:
            last_p = spec["p"]
            append_record({"job": "7b", "checkpoint": True, "p": last_p})
            write_status(job="7b", state="running", p=last_p)
        if min_residual(spec["p"], len(spec["pool"])) > 256:
            print(
                f"  [7b] skip p={spec['p']} e={spec['e']} min_resid="
                f"{min_residual(spec['p'], len(spec['pool']))}>256",
                flush=True,
            )
            continue
        if not r4_cells_open(spec["p"]):
            print(f"  [7b] skip p={spec['p']} no open R(4,t) cell", flush=True)
            continue
        print(
            f"  [7b] p={spec['p']} e={spec['e']} D{spec['i']}∪D{spec['j']} "
            f"pool={len(spec['pool'])} open_t={r4_cells_open(spec['p'])}",
            flush=True,
        )
        cand = []
        seen: set[tuple[int, ...]] = set()
        for w in range(walks):
            S = restricted_process(spec["p"], spec["pool"], rng)
            if anneal:
                S = anneal_pool(spec["p"], spec["pool"], S, anneal, rng, t_cell=25)
            if set(S) == YU_S:
                continue
            key = tuple(lexmin_distances(spec["p"], S))
            if key in seen:
                print(f"    walk {w + 1}/{walks} |S|={len(S)} orbit-dup skip", flush=True)
                continue
            seen.add(key)
            row = distances_to_row(spec["p"], S)
            tri = nbhd_triangle_free(row)
            gα = greedy_alpha_row(row)
            print(f"    walk {w + 1}/{walks} |S|={len(S)} tri_free={tri} greedyα={gα}", flush=True)
            if not tri:
                continue
            t_cell = _pick_t(spec, gα)
            if t_cell is None:
                continue
            cand.append((gα, -len(S), S, row, t_cell))
        cand.sort()
        for gα, _, S, row, t_cell in cand[: int(lim.get("yu_mis_keep", 4))]:
            cert = certify_row_decision(row, t_cell, tlim)
            print(f"      MIS |S|={len(S)} greedyα={gα} t={t_cell} {cert['reason']}", flush=True)
            rec = _emit_yu_hit(spec, S, row, cert, t_cell, "7b")
            if rec:
                rows.append(rec)
    write_status(job="7b", state="done", graphs=len(rows))
    return rows


def _sat_max_pool(spec: dict, seconds: float) -> list[int] | None:
    """Look 6: maximise |S| inside the pool with N(0) triangle-free."""
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return None
    pool = list(spec["pool"])
    p = spec["p"]
    idx = {d: i for i, d in enumerate(pool)}
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"d{d}") for d in pool]
    from itertools import combinations

    for k in (1, 2, 3):
        for subset in combinations(pool, k):
            row = distances_to_row(p, subset)
            if not nbhd_triangle_free(row):
                model.Add(sum(xs[idx[d]] for d in subset) <= k - 1)
    model.Maximize(sum(xs))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = int(os.environ.get("RAMSEY_SAT_WORKERS", "8"))
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return sorted(d for d, x in zip(pool, xs) if solver.Value(x))


def job_7c() -> list[dict]:
    """Look 6: SAT/IP on the connection set (Yu pools), then residual referee."""
    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        print("  [7c] HALT — skip", flush=True)
        return []
    lim = limits()
    tlim = float(lim["yu_mis_limit"])
    sat_lim = float(lim.get("look6_sat", 30.0))
    p_lo = int(lim.get("look1_p_lo", 251))
    p_hi = int(lim.get("look1_p_hi", 251 if scale_name() == "local" else 313))
    print(f"  [7c] Look 6 SAT-on-pool p∈[{p_lo},{p_hi}] sat={sat_lim}s", flush=True)
    write_status(job="7c", state="running")
    rows: list[dict] = []
    n_pools = 0
    for spec in iter_yu_pools(p_lo, p_hi):
        if min_residual(spec["p"], len(spec["pool"])) > 256:
            continue
        if not r4_cells_open(spec["p"]):
            continue
        n_pools += 1
        if scale_name() == "local" and n_pools > 3:
            break
        print(
            f"  [7c] SAT p={spec['p']} e={spec['e']} D{spec['i']}∪D{spec['j']} pool={len(spec['pool'])}",
            flush=True,
        )
        S = _sat_max_pool(spec, sat_lim)
        if S is None:
            print("  [7c] SAT unavailable or unsat — skip pool", flush=True)
            continue
        if set(S) == YU_S:
            print("  [7c] recovered Yu S — skip", flush=True)
            continue
        row = distances_to_row(spec["p"], S)
        gα = greedy_alpha_row(row)
        t_cell = _pick_t(spec, gα)
        print(f"  [7c] |S|={len(S)} greedyα={gα} t={t_cell}", flush=True)
        if t_cell is None:
            continue
        resid = spec["p"] - 1 - int(row.sum())
        if resid > 256:
            print(f"  [7c] residual {resid}>256 — skip (not a cell)", flush=True)
            continue
        cert = certify_row_decision(row, t_cell, tlim)
        rec = _emit_yu_hit(spec, S, row, cert, t_cell, "7c")
        if rec:
            rows.append(rec)
    write_status(job="7c", state="done", graphs=len(rows))
    return rows


def job_7c1() -> list[dict]:
    """Look 6 CEGIS: SAT-on-pool + residual-IS cuts. Not max |S|. Not 7c again."""
    from .cegis_pool import (
        assignment_nogood,
        build_triangle_free_model,
        cut_kills_this_s,
        extract_is_local,
        first_triangle_support_dists,
        is_cut_pool_lits,
        local_is_to_zp,
        solve_pool_model,
        verify_is_independent,
    )
    from .yu_pool import restricted_process

    rng = np.random.default_rng(20260830)

    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        print("  [7c1] HALT file — skip (set RAMSEY_FORCE_7=1 to hunt on 5a c-decide alone)", flush=True)
        return []
    try:
        from ortools.sat.python import cp_model  # noqa: F401
    except ImportError:
        print("  [7c1] ortools missing — pip install ortools. No hunt.", flush=True)
        write_status(job="7c1", state="blocked", reason="no_ortools")
        return []

    lim = limits()
    tlim = float(lim["yu_mis_limit"])
    sat_lim = float(lim.get("look6_sat", 30.0))
    rounds = int(lim.get("look6_rounds", 4))
    pool_wall = float(lim.get("look6_cegis", sat_lim))
    wit_lim = float(lim.get("look6_witness", 2.0))
    anneal = int(lim.get("look1_anneal", lim.get("yu_anneal", 8)))
    p_lo = int(lim.get("look1_p_lo", 251))
    p_hi = int(lim.get("look1_p_hi", 251 if scale_name() == "local" else 313))
    print(
        f"  [7c1] Look 6 CEGIS p∈[{p_lo},{p_hi}] rounds≤{rounds} "
        f"pool_wall={pool_wall}s sat={sat_lim}s mis={tlim}s  "
        f"per-round=max|S|; learning=leftover-IS-cuts (not one-shot 7c)",
        flush=True,
    )
    write_status(job="7c1", state="running", p_lo=p_lo, p_hi=p_hi, rounds=rounds)
    rows: list[dict] = []
    n_pools = 0
    n_cuts = 0
    n_timeouts = 0
    n_unsat_pools = 0
    for spec in iter_yu_pools(p_lo, p_hi):
        if min_residual(spec["p"], len(spec["pool"])) > 256:
            print(
                f"  [7c1] skip p={spec['p']} e={spec['e']} D{spec['i']}∪D{spec['j']} "
                f"min_resid={min_residual(spec['p'], len(spec['pool']))}>256",
                flush=True,
            )
            continue
        open_t = r4_cells_open(spec["p"])
        if not open_t:
            print(f"  [7c1] skip p={spec['p']} no open R(4,t) cell", flush=True)
            continue
        n_pools += 1
        if scale_name() == "local" and n_pools > 2:
            print("  [7c1] local cap: 2 pools — stop", flush=True)
            n_pools -= 1
            break
        p = int(spec["p"])
        print(
            f"  [7c1] pool #{n_pools} p={p} e={spec['e']} D{spec['i']}∪D{spec['j']} "
            f"pool={len(spec['pool'])} open_t={open_t} min_resid={min_residual(p, len(spec['pool']))}",
            flush=True,
        )
        model, xs, idx, pool = build_triangle_free_model(spec)
        t_pool = time.perf_counter()
        pool_done = "rounds"
        for rnd in range(1, rounds + 1):
            left = pool_wall - (time.perf_counter() - t_pool)
            if left <= 0.05:
                print(f"    [7c1] round {rnd}/{rounds} pool_wall exhausted ({pool_wall}s) — next pool", flush=True)
                pool_done = "wall"
                break
            sat_budget = min(sat_lim, left)
            status, S, sat_s = solve_pool_model(model, xs, pool, sat_budget, seed=20260830 + rnd)
            print(
                f"    [7c1] round {rnd}/{rounds} SAT {status} {sat_s:.3f}s "
                f"(budget {sat_budget:.2f}s left {left:.2f}s)",
                flush=True,
            )
            if status == "INFEASIBLE":
                print(
                    "    [7c1]   pool UNSAT under triangle-free + width + IS-cuts — "
                    "every feasible S was cut. Not a cell.",
                    flush=True,
                )
                n_unsat_pools += 1
                pool_done = "unsat"
                break
            if S is None:
                print(
                    "    [7c1]   SAT UNKNOWN/timeout ≠ accept. No S, so no cut. Next pool.",
                    flush=True,
                )
                n_timeouts += 1
                pool_done = "sat_timeout"
                break
            if set(S) == YU_S:
                print(
                    f"    [7c1]   recovered Yu S |S|={len(S)} — nogood published 32-set, not a new cell",
                    flush=True,
                )
                model.Add(assignment_nogood(xs, pool, idx, S))
                continue
            row = distances_to_row(p, S)
            resid = p - 1 - int(row.sum())
            print(
                f"    [7c1]   |S|={len(S)} resid={resid} S[:12]={S[:12]}{'…' if len(S) > 12 else ''}",
                flush=True,
            )
            tri_fix = 0
            while not nbhd_triangle_free(row):
                tri_fix += 1
                support = first_triangle_support_dists(row) or []
                lits = [idx[d] for d in support if d in idx]
                print(
                    f"    [7c1]   N(0) triangle (3-subset encoding incomplete) "
                    f"fix={tri_fix} TRIANGLE-CUT |lits|={len(lits)} support={support[:8]}",
                    flush=True,
                )
                if len(lits) >= 2:
                    model.Add(sum(xs[i] for i in lits) <= len(lits) - 1)
                    n_cuts += 1
                else:
                    model.Add(assignment_nogood(xs, pool, idx, S))
                left = pool_wall - (time.perf_counter() - t_pool)
                if left <= 0.05 or tri_fix >= 4:
                    S = restricted_process(p, pool, rng)
                    if anneal:
                        S = anneal_pool(p, pool, S, anneal, rng, t_cell=25)
                    row = distances_to_row(p, S)
                    resid = p - 1 - int(row.sum())
                    print(
                        f"    [7c1]   triangle-repair cap — fallback process+anneal "
                        f"|S|={len(S)} resid={resid} greedyα={greedy_alpha_row(row)} "
                        f"tri_free={nbhd_triangle_free(row)}",
                        flush=True,
                    )
                    break
                status, S, sat_s = solve_pool_model(
                    model, xs, pool, min(sat_lim, left), seed=20260830 + rnd + tri_fix
                )
                print(f"    [7c1]   re-SAT {status} {sat_s:.3f}s after triangle-cut", flush=True)
                if status == "INFEASIBLE":
                    n_unsat_pools += 1
                    pool_done = "unsat"
                    S = None
                    break
                if S is None:
                    n_timeouts += 1
                    pool_done = "sat_timeout"
                    break
                if set(S) == YU_S:
                    print("    [7c1]   re-SAT hit Yu S — nogood, solve again", flush=True)
                    model.Add(assignment_nogood(xs, pool, idx, S))
                    status, S, sat_s = solve_pool_model(
                        model, xs, pool, min(sat_lim, left), seed=20260830 + rnd + tri_fix + 17
                    )
                    if status == "INFEASIBLE" or S is None:
                        pool_done = "unsat" if status == "INFEASIBLE" else "sat_timeout"
                        S = None
                        break
                    row = distances_to_row(p, S)
                    resid = p - 1 - int(row.sum())
                    continue
                row = distances_to_row(p, S)
                resid = p - 1 - int(row.sum())
                print(
                    f"    [7c1]   |S|={len(S)} resid={resid} after {tri_fix} triangle-cut(s)",
                    flush=True,
                )
            if pool_done in ("unsat", "sat_timeout"):
                break
            if S is None or not nbhd_triangle_free(row):
                continue
            gα = greedy_alpha_row(row)
            t_cell = _pick_t(spec, gα)
            print(
                f"    [7c1]   greedyα={gα} t_cell={t_cell}",
                flush=True,
            )
            if resid > 256:
                print(f"    [7c1]   residual {resid}>256 — skip (same void as 4a). Nogood this S.", flush=True)
                model.Add(assignment_nogood(xs, pool, idx, S))
                continue
            if t_cell is None:
                print(
                    f"    [7c1]   greedyα={gα} does not open a cell at n={p} "
                    f"(open_t={open_t}). Nogood this S.",
                    flush=True,
                )
                model.Add(assignment_nogood(xs, pool, idx, S))
                continue
            cert = certify_row_decision(row, t_cell, tlim)
            mis = cert.get("mis") or {}
            print(
                f"    [7c1]   decide {cert.get('reason')} found={mis.get('found')} "
                f"timeout={mis.get('timed_out')} exact={cert.get('exact')} "
                f"rejected={cert.get('rejected')} backend={mis.get('backend')} "
                f"nodes={mis.get('nodes')} {mis.get('seconds')}",
                flush=True,
            )
            if cert.get("exact") and not cert.get("rejected"):
                rec = _emit_yu_hit(spec, S, row, cert, t_cell, "7c1")
                if rec:
                    rows.append(rec)
                print(
                    f"    [7c1]   residual ACCEPT t={t_cell} mixed logged above. "
                    "CELL? only if mixed_ok and n+1 beats published.",
                    flush=True,
                )
                pool_done = "accept"
                break
            if mis.get("timed_out") or cert.get("reason") == "MIS timed out":
                print("    [7c1]   timeout ≠ accept. Nogood this S (do not cut on a missing I).", flush=True)
                n_timeouts += 1
                model.Add(assignment_nogood(xs, pool, idx, S))
                continue
            if not mis.get("found") and not cert.get("rejected"):
                rec = _emit_yu_hit(spec, S, row, cert, t_cell, "7c1")
                if rec:
                    rows.append(rec)
                pool_done = "residual_only"
                break
            # Referee found a residual IS. Reconstruct I, then cut.
            nbr = residual_nbr(row)
            target = int(t_cell) - 1
            local = extract_is_local(nbr, target, seconds=wit_lim)
            if not local:
                print(
                    f"    [7c1]   found=True but witness extract failed (target={target}, "
                    f"wit_lim={wit_lim}s). Nogood S, no cut. Timeout≠cut.",
                    flush=True,
                )
                model.Add(assignment_nogood(xs, pool, idx, S))
                continue
            I = local_is_to_zp(row, local)
            ok_ind = verify_is_independent(row, I)
            print(
                f"    [7c1]   witness |I|={len(I)} independent={ok_ind} "
                f"I[:16]={I[:16]}{'…' if len(I) > 16 else ''}",
                flush=True,
            )
            if not ok_ind or len(I) < target:
                print("    [7c1]   witness failed check — nogood S, no cut.", flush=True)
                model.Add(assignment_nogood(xs, pool, idx, S))
                continue
            lits = is_cut_pool_lits(p, idx, I)
            kills = cut_kills_this_s(pool, S, lits, idx) if lits else False
            print(
                f"    [7c1]   CUT |lits|={len(lits)} kills_this_S={kills} "
                f"(hit I: put a vertex of I into N(0) or a difference into S)",
                flush=True,
            )
            if not lits:
                print(
                    "    [7c1]   empty cut — pool distances cannot hit I. "
                    "Model → unsat. Pool dead for this t. Not a cell.",
                    flush=True,
                )
                model.Add(sum(xs) <= -1)
                n_unsat_pools += 1
                pool_done = "empty_cut"
                break
            model.Add(sum(xs[i] for i in lits) >= 1)
            n_cuts += 1
            write_status(
                job="7c1",
                state="running",
                p=p,
                round=rnd,
                cuts=n_cuts,
                pools=n_pools,
            )
        else:
            print(f"    [7c1] rounds cap {rounds} on this pool — next pool", flush=True)
            pool_done = "rounds"
        print(
            f"  [7c1] pool p={p} e={spec['e']} D{spec['i']}∪D{spec['j']} done={pool_done} "
            f"wall={time.perf_counter() - t_pool:.2f}s cuts_so_far={n_cuts}",
            flush=True,
        )
        append_record(
            {
                "job": "7c1",
                "p": p,
                "e": spec["e"],
                "i": spec["i"],
                "j": spec["j"],
                "done": pool_done,
                "cuts": n_cuts,
            }
        )
    write_status(
        job="7c1",
        state="done",
        graphs=len(rows),
        pools=n_pools,
        cuts=n_cuts,
        timeouts=n_timeouts,
        unsat_pools=n_unsat_pools,
    )
    print(
        f"  [7c1] summary pools={n_pools} cuts={n_cuts} timeouts={n_timeouts} "
        f"unsat_pools={n_unsat_pools} graphs={len(rows)}  published cell still 252 unless CELL?",
        flush=True,
    )
    return rows


def job_7d() -> list[dict]:
    """Look 2: R(3,t) t≥50, nonempty Schur seed. Do not touch Coniglio 24–49."""
    from .phase5 import job_5d

    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        print("  [7d] HALT — skip", flush=True)
        return []
    t = int(limits()["r3_t"])
    if t < 50:
        print(f"  [7d] scale r3_t={t}<50 — skip (Coniglio owns 24–49)", flush=True)
        write_status(job="7d", state="skipped", reason="t<50")
        return []
    print(f"  [7d] Look 2 R(3,{t}) floor≥{R3_LOWER.get(50)}", flush=True)
    os.environ["RAMSEY_FORCE_5DEF"] = "1"
    rows = job_5d()
    for r in rows:
        r["job"] = "7d"
    write_status(job="7d", state="done", graphs=len(rows))
    return rows


def _adj_nbr(adj) -> list[int]:
    n = int(adj.shape[0])
    nbr = [0] * n
    for i in range(n):
        bits = 0
        for j in np.flatnonzero(adj[i]):
            bits |= 1 << int(j)
        nbr[i] = bits
    return nbr


def _k4_free_adj(adj) -> bool:
    """K4-free ⇔ every neighbourhood is triangle-free."""
    n = int(adj.shape[0])
    for v in range(n):
        nb = [int(x) for x in np.flatnonzero(adj[v])]
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                if not adj[nb[i], nb[j]]:
                    continue
                for k in range(j + 1, len(nb)):
                    if adj[nb[i], nb[k]] and adj[nb[j], nb[k]]:
                        return False
    return True


def job_7e() -> list[dict]:
    """Look 4: 2-polycirculant, n≤256, decision α — not Hoffman."""
    from .jobs import _decision_cert, emit
    from .kernels.cayley import two_block_adj
    from .kernels.sieve import quadratic_residue_row

    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        print("  [7e] HALT — skip", flush=True)
        return []
    lim = limits()
    tlim = float(lim["yu_mis_limit"])
    ms = (17, 29) if scale_name() == "local" else (29, 41, 53, 61)
    steps = 24 if scale_name() == "local" else 80
    rng = np.random.default_rng(7)
    print(f"  [7e] Look 4 2-block m={ms} n=2m≤256  score=greedy α, not Hoffman", flush=True)
    write_status(job="7e", state="running")
    rows: list[dict] = []
    for m in ms:
        n = 2 * m
        if n > 256:
            continue
        if m % 4 == 1:
            s0 = quadratic_residue_row(m).astype(np.uint8)
        else:
            s0 = np.zeros(m, dtype=np.uint8)
            s0[1::2] = 1
            s0[0] = 0
        s1 = np.roll(s0, m // 3)
        s0[0] = 0
        s1[0] = 0
        adj = two_block_adj(s0, s1)
        best_adj = adj
        best_g = greedy_mis(_adj_nbr(adj))
        for _ in range(steps):
            which = int(rng.integers(0, 2))
            i = int(rng.integers(1, m))
            vec = s0 if which == 0 else s1
            vec[i] ^= 1
            vec[(m - i) % m] = vec[i]
            trial = two_block_adj(s0, s1)
            if not _k4_free_adj(trial):
                vec[i] ^= 1
                vec[(m - i) % m] = vec[i]
                continue
            g = greedy_mis(_adj_nbr(trial))
            if g <= best_g:
                best_g = g
                best_adj = trial
        adj = best_adj
        k4 = _k4_free_adj(adj)
        nbr = _adj_nbr(adj)
        glo = greedy_mis(nbr)
        print(f"  [7e] m={m} n={n} K4_free={k4} greedyα={glo}", flush=True)
        if not k4:
            append_record({"job": "7e", "m": m, "n": n, "k4_free": False, "exact": False})
            continue
        t_cell = _pick_t({"p": n}, glo)
        if t_cell is None:
            print(f"  [7e] n={n} no open R(4,t) vs greedyα={glo}", flush=True)
            continue
        dec = decide_alpha_le(nbr, target=t_cell, time_limit=tlim)
        exact = (not dec["found"]) and (not dec["timed_out"]) and dec.get("exact")
        published = R4_LOWER.get(t_cell, 0)
        beats = bool(exact and n + 1 > published)
        print(
            f"  [7e] decide α≥{t_cell} found={dec['found']} timeout={dec['timed_out']} "
            f"beats={beats} published={published}",
            flush=True,
        )
        from .certify_fast import certify_fast

        cert = certify_fast(adj, time_limit=0.05)
        meta = {
            "construction_type": "block_circulant",
            "gpu_kernel": "7e two-orbit + decide α",
            "field": f"Z_2 × Z_{m}",
            "params": {"m": m, "n": n, "kind": "7e", "t_cell": t_cell, "k4_free": True},
            "run001": "not_done",
        }
        pack = cert
        pack["exact"] = beats
        if not beats:
            pack["omega_exact"] = None
            pack["alpha_exact"] = None
        row = emit(adj, meta, pack, "7e", "R(4,t)")
        row["exact"] = beats
        rows.append(row)
        if beats:
            print(f"  [7e] CELL? R(4,{t_cell}) ≥ {n + 1}  vs ≥ {published}", flush=True)
        if dec["timed_out"]:
            print("  [7e] timeout ≠ accept", flush=True)
    write_status(job="7e", state="done", graphs=len(rows))
    return rows


def job_7f() -> list[dict]:
    """Look 5: polarity leftover, leftover≤256 and N+1 beats the floor."""
    from .phase5 import job_5e

    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        print("  [7f] HALT — skip", flush=True)
        return []
    print("  [7f] Look 5 polarity leftover + floor gate", flush=True)
    os.environ["RAMSEY_FORCE_5DEF"] = "1"
    rows = job_5e()
    for r in rows:
        r["job"] = "7f"
    write_status(job="7f", state="done", graphs=len(rows))
    return rows


def _prioritize_open_t(open_t: list[int]) -> list[int]:
    """Prioritize t=20,21 first, then remaining ascending."""
    priority = [t for t in (20, 21) if t in open_t]
    rest = sorted(t for t in open_t if t not in (20, 21))
    return priority + rest


def _extract_is_witness_greedy(nbr: list[int], target: int) -> list[int] | None:
    """Extract a greedy IS witness of size >= target."""
    from .kernels.bitset_mcs import greedy_mis_set
    witness = greedy_mis_set(nbr)
    return list(witness) if len(witness) >= target else None


def _extract_is_witness_decide(nbr: list[int], target: int, seconds: float) -> list[int] | None:
    """Extract an IS witness via decide_alpha_le with witness extraction."""
    n = len(nbr)
    if n > 256:
        return None
    from .kernels.decide_alpha import decide_alpha_le
    dec = decide_alpha_le(nbr, target=target, time_limit=seconds)
    if dec.get("found") and dec.get("witness"):
        return dec["witness"]
    return None


def job_7e1() -> list[dict]:
    """Look 4 extension: two-orbit 200≤n≤256, decide ALL open t (prioritize 20,21).
    
    NOT in phase7 loop — standalone CLI job. Minimal ILS (not stock ils_two_block).
    Uses decide_alpha_le(target=t) on full adjacency for EACH open t.
    Extracts and persists IS witnesses when found=True.
    Persists dumps to data/phase7/7e1/*.json.
    """
    from .jobs import emit_decision
    from .kernels.cayley import two_block_adj
    from .kernels.sieve import quadratic_residue_row
    from .kernels.decide_alpha import mixed_set_check

    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        print("  [7e1] HALT file exists — skip (set RAMSEY_FORCE_7=1 to override)", flush=True)
        return []
    
    lim = limits()
    tlim = float(lim["yu_mis_limit"])
    is_runpod = scale_name() == "runpod"
    
    # Environment overrides for deeper search
    focus_m_env = os.environ.get("RAMSEY_7E1_M", "")
    if focus_m_env:
        ms = tuple(int(x.strip()) for x in focus_m_env.split(",") if x.strip())
    else:
        ms = (126, 127, 128) if is_runpod else (127,)
    
    restarts_per_m = int(os.environ.get("RAMSEY_7E1_RESTARTS", "20" if is_runpod else "4"))
    steps_per_restart = int(os.environ.get("RAMSEY_7E1_STEPS", "120" if is_runpod else "24"))
    
    print(f"  [7e1] Two-orbit 200≤n≤256  m={ms}  scale={scale_name()}", flush=True)
    print(f"  [7e1] restarts={restarts_per_m} steps={steps_per_restart}", flush=True)
    print(f"  [7e1] R4_LOWER={dict(sorted((t, lb) for t, lb in R4_LOWER.items() if t >= 17))}", flush=True)
    write_status(job="7e1", state="running", ms=list(ms), restarts=restarts_per_m, steps=steps_per_restart)
    
    dump_dir = ROOT / "data" / "phase7" / "7e1"
    dump_dir.mkdir(parents=True, exist_ok=True)
    
    rows: list[dict] = []
    for m in ms:
        n = 2 * m
        if n < 200 or n > 256:
            print(f"  [7e1] skip m={m} n={n} (want 200≤n≤256)", flush=True)
            continue
        
        print(f"\n  [7e1] === m={m} n={n} ===", flush=True)
        
        for restart in range(restarts_per_m):
            rng = np.random.default_rng(20260901 + m * 1000 + restart)
            
            # Seed families: (a) roll, (b) random densities, (c) sparse s1
            seed_family = "roll"
            if restart % 3 == 1:
                seed_family = "random_density"
            elif restart % 3 == 2:
                seed_family = "sparse_s1"
            
            print(f"  [7e1] m={m} restart {restart + 1}/{restarts_per_m} family={seed_family}", flush=True)
            
            # Generate seed
            if seed_family == "roll":
                if m % 4 == 1:
                    try:
                        s0 = quadratic_residue_row(m).astype(np.uint8)
                    except Exception:
                        s0 = np.zeros(m, dtype=np.uint8)
                        s0[1::2] = 1
                else:
                    s0 = np.zeros(m, dtype=np.uint8)
                    s0[1::2] = 1
                s1 = np.roll(s0, m // 3 + restart)
            elif seed_family == "random_density":
                density = float(rng.choice([0.25, 0.33, 0.40]))
                s0 = (rng.random(m) < density).astype(np.uint8)
                s1 = (rng.random(m) < density).astype(np.uint8)
                # Inversion-closed
                for i in range(1, m):
                    s0[m - i] = s0[i]
                    s1[m - i] = s1[i]
            else:  # sparse_s1
                s0 = (rng.random(m) < 0.35).astype(np.uint8)
                s1 = (rng.random(m) < 0.12).astype(np.uint8)
                for i in range(1, m):
                    s0[m - i] = s0[i]
                    s1[m - i] = s1[i]
            
            s0[0] = 0
            s1[0] = 0
            
            adj = two_block_adj(s0, s1)
            best_adj = adj
            best_s0 = s0.copy()
            best_s1 = s1.copy()
            best_g = greedy_mis(_adj_nbr(adj))
            
            # Minimal ILS
            for step in range(steps_per_restart):
                which = int(rng.integers(0, 2))
                i = int(rng.integers(1, m))
                vec = s0 if which == 0 else s1
                vec[i] ^= 1
                vec[(m - i) % m] = vec[i]
                trial = two_block_adj(s0, s1)
                if not _k4_free_adj(trial):
                    vec[i] ^= 1
                    vec[(m - i) % m] = vec[i]
                    continue
                g = greedy_mis(_adj_nbr(trial))
                if g < best_g:
                    best_g = g
                    best_adj = trial
                    best_s0 = s0.copy()
                    best_s1 = s1.copy()
                    if step % 40 == 0 or step < 10:
                        print(f"      step {step + 1}/{steps_per_restart} greedyα={g} (improvement)", flush=True)
            
            adj = best_adj
            s0 = best_s0
            s1 = best_s1
            k4_free = _k4_free_adj(adj)
            nbr = _adj_nbr(adj)
            glo = greedy_mis(nbr)
            print(f"  [7e1] restart {restart + 1} K4_free={k4_free} greedyα={glo}", flush=True)
            
            if not k4_free:
                dump = {
                    "m": m,
                    "n": n,
                    "restart": restart,
                    "seed_family": seed_family,
                    "k4_free": False,
                    "s0": s0.tolist(),
                    "s1": s1.tolist(),
                }
                dump_path = dump_dir / f"m{m}_r{restart}_k4fail.json"
                dump_path.write_text(json.dumps(dump, indent=2) + "\n")
                append_record({"job": "7e1", "m": m, "restart": restart, "k4_free": False})
                continue
            
            # Determine ALL open t, prioritized
            open_t_raw = [t for t in r4_cells_open(n) if glo < t]
            if not open_t_raw:
                print(f"  [7e1] n={n} greedyα={glo} no open R(4,t) cell", flush=True)
                continue
            
            open_t = _prioritize_open_t(open_t_raw)
            print(f"  [7e1] open_t={open_t_raw} prioritized={open_t}", flush=True)
            
            # Decide EVERY open t
            decisions = {}
            best_residual_accept_t = None
            for t_cell in open_t:
                published = R4_LOWER.get(t_cell, 0)
                print(f"  [7e1]   decide t={t_cell} (published≥{published}) α<{t_cell}…", flush=True)
                
                dec = decide_alpha_le(nbr, target=t_cell, time_limit=tlim)
                print(
                    f"  [7e1]   t={t_cell} found={dec['found']} timeout={dec['timed_out']} "
                    f"exact={dec.get('exact')} backend={dec.get('backend')} nodes={dec.get('nodes')}",
                    flush=True,
                )
                
                # Extract witness if found
                witness = None
                if dec.get("found"):
                    if glo >= t_cell:
                        witness = _extract_is_witness_greedy(nbr, t_cell)
                        print(f"  [7e1]   t={t_cell} witness: greedy |I|={len(witness) if witness else 0}", flush=True)
                    else:
                        witness = _extract_is_witness_decide(nbr, t_cell, min(10.0, tlim))
                        print(f"  [7e1]   t={t_cell} witness: decide extract |I|={len(witness) if witness else 0}", flush=True)
                
                residual_accept = (not dec["found"]) and (not dec["timed_out"]) and dec.get("exact")
                decisions[t_cell] = {
                    "found": dec["found"],
                    "timed_out": dec["timed_out"],
                    "exact": dec.get("exact"),
                    "backend": dec.get("backend"),
                    "nodes": dec.get("nodes"),
                    "seconds": dec.get("seconds"),
                    "residual_accept": residual_accept,
                    "witness": witness,
                }
                
                if residual_accept and best_residual_accept_t is None:
                    best_residual_accept_t = t_cell
                
                if dec.get("found"):
                    print(f"  [7e1]   t={t_cell} REJECT (found {t_cell}-IS)", flush=True)
                elif dec.get("timed_out"):
                    print(f"  [7e1]   t={t_cell} TIMEOUT (≠ accept)", flush=True)
                elif residual_accept:
                    print(f"  [7e1]   t={t_cell} residual-accept (α<{t_cell} proven)", flush=True)
                else:
                    print(f"  [7e1]   t={t_cell} inconclusive", flush=True)
            
            # Check mixed_set only on best residual_accept
            mixed_ok = False
            mix_reason = None
            if best_residual_accept_t is not None:
                t_cell = best_residual_accept_t
                row = adj[0].astype(np.uint8)
                # NOTE: mixed_set_check via adj[0] row is imperfect for two-block
                # TODO: Consider two-block-aware mixed_set or skip mixed_ok for two-orbit
                mix = mixed_set_check(row, t_cell, time_limit=min(20.0, tlim))
                mixed_ok = mix.get("mixed_ok", False)
                mix_reason = mix.get("reason")
                print(f"  [7e1]   mixed_set t={t_cell} {mix_reason} mixed_ok={mixed_ok}", flush=True)
                print(f"  [7e1]   NOTE: two-block mixed_set via adj[0] is imperfect; treat as preliminary", flush=True)
            
            # Persist dump
            dump = {
                "m": m,
                "n": n,
                "restart": restart,
                "seed_family": seed_family,
                "s0": s0.tolist(),
                "s1": s1.tolist(),
                "k4_free": k4_free,
                "greedy_alpha": glo,
                "open_t": open_t,
                "decisions": decisions,
                "best_residual_accept_t": best_residual_accept_t,
                "mixed_ok": mixed_ok,
                "mixed_reason": mix_reason,
            }
            dump_path = dump_dir / f"m{m}_r{restart}.json"
            dump_path.write_text(json.dumps(dump, indent=2, default=str) + "\n")
            print(f"  [7e1]   wrote {dump_path}", flush=True)
            
            # Emit to catalog if we have a best residual_accept
            if best_residual_accept_t is not None:
                t_cell = best_residual_accept_t
                published = R4_LOWER.get(t_cell, 0)
                cell_ok = decisions[t_cell]["residual_accept"] and mixed_ok
                beats = cell_ok and n + 1 > published
                
                from .certify_fast import certify_fast
                cert = certify_fast(adj, time_limit=0.05)
                meta = {
                    "construction_type": "block_circulant",
                    "gpu_kernel": "7e1 two-orbit + decide_alpha_le(target=t) for all open t",
                    "field": f"Z_2 × Z_{m}",
                    "params": {
                        "m": m,
                        "n": n,
                        "restart": restart,
                        "seed_family": seed_family,
                        "kind": "7e1",
                        "t_cell": t_cell,
                        "k4_free": True,
                        "mixed_ok": mixed_ok,
                        "open_t": open_t,
                    },
                    "run001": "not_done",
                }
                pack = cert
                pack["exact"] = beats
                if not beats:
                    pack["omega_exact"] = None
                    pack["alpha_exact"] = None
                
                rec = emit_decision(adj[0], meta, pack, "7e1", "R(4,t)")
                rec["exact"] = beats
                rows.append(rec)
                
                if beats:
                    print(
                        f"  [7e1]   CELL? R(4,{t_cell}) ≥ {n + 1}  (published ≥ {published})  mixed_ok",
                        flush=True,
                    )
                elif decisions[t_cell]["residual_accept"] and not mixed_ok:
                    print(
                        f"  [7e1]   residual_only n={n} t={t_cell}  {mix_reason}  not CELL?",
                        flush=True,
                    )
    
    write_status(job="7e1", state="done", graphs=len(rows), dumps_in=str(dump_dir))
    print(f"\n  [7e1] done  graphs={len(rows)}  dumps in {dump_dir}", flush=True)
    return rows


def job_7e4() -> list[dict]:
    """Look 4: CP-SAT CEGIS on two-orbit (S0,S1) with leftover-IS cuts.
    
    7e.4 = CP-SAT on O(m) inversion-closed free bits of (S0,S1), hard 
    neighbourhood-triangle-free clauses, soft search that does NOT maximize |S|, 
    leftover/full-graph IS CEGIS capped at 20 cuts/m, referee = decide_alpha_le 
    on full graph with target=t (prioritize t=20,21). Success = CELL? with 
    mixed-set OK, or written pool-UNSAT / cut-saturated negative at P0 {126,128}.
    
    NOT --job 7c. NOT maximize |S|. NOT reopen 7c/pod-phase7.sh.
    """
    from .cegis_two_block import (
        assignment_nogood,
        bits_to_s0_s1,
        build_triangle_free_two_block_model,
        extract_is_full_graph,
        first_triangle_support_two_block,
        free_bit_index,
        is_cut_two_block_lits,
        solve_two_block_model,
        verify_is_independent_full,
    )
    from .jobs import _decision_cert, emit_decision
    from .kernels.cayley import two_block_adj
    
    rng = np.random.default_rng(20260912)
    
    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        print("  [7e4] HALT file — skip (set RAMSEY_FORCE_7=1 to hunt on 5a c-decide alone)", flush=True)
        return []
    
    try:
        from ortools.sat.python import cp_model  # noqa: F401
    except ImportError:
        print("  [7e4] ortools missing — pip install ortools. No hunt.", flush=True)
        write_status(job="7e4", state="blocked", reason="no_ortools")
        return []
    
    lim = limits()
    
    # Environment knobs
    if scale_name() == "local":
        ms_default = "17,29"
        cuts_default = 5
        rounds_default = 4
        sat_default = 8.0
        pool_wall_default = 20.0
        mis_default = 8.0
    else:
        ms_default = "126,128"
        cuts_default = 20
        rounds_default = 16
        sat_default = 30.0
        pool_wall_default = 90.0
        mis_default = 25.0
    
    ms_str = os.environ.get("RAMSEY_7E4_M", ms_default)
    ms = [int(x.strip()) for x in ms_str.split(",")]
    cuts_cap = int(os.environ.get("RAMSEY_7E4_CUTS", cuts_default))
    rounds = int(os.environ.get("RAMSEY_7E4_ROUNDS", rounds_default))
    sat_lim = float(os.environ.get("RAMSEY_7E4_SAT", sat_default))
    pool_wall = float(os.environ.get("RAMSEY_7E4_POOL_WALL", pool_wall_default))
    mis_lim = float(os.environ.get("RAMSEY_7E4_MIS", mis_default))
    warm_start = os.environ.get("RAMSEY_7E4_WARM") == "1"
    
    print(
        f"  [7e4] Look 4 / R(4,20)≥252 CEGIS on two-orbit (S0,S1) m={ms} "
        f"rounds≤{rounds} cuts_cap={cuts_cap} pool_wall={pool_wall}s sat={sat_lim}s mis={mis_lim}s  "
        f"NOT maximize |S|; learning=leftover-IS-cuts (NOT --job 7c)",
        flush=True,
    )
    write_status(job="7e4", state="running", ms=ms, rounds=rounds, cuts_cap=cuts_cap)
    
    rows: list[dict] = []
    total_cuts = 0
    total_timeouts = 0
    total_unsat = 0
    
    dump_dir = ROOT / "data" / "phase7" / "7e4"
    dump_dir.mkdir(parents=True, exist_ok=True)
    
    for m_idx, m in enumerate(ms):
        n = 2 * m
        if n > 256:
            print(f"  [7e4] skip m={m} n={n}>256 (referee gate)", flush=True)
            continue
        
        open_t = r4_cells_open(n)
        if not open_t:
            print(f"  [7e4] skip m={m} n={n} no open R(4,t) cell", flush=True)
            continue
        
        # Prioritize t=20,21 then other open_t with n+1>R4_LOWER[t]
        priority_t = []
        for t in [20, 21]:
            if t in open_t:
                priority_t.append(t)
        for t in open_t:
            if t not in priority_t:
                priority_t.append(t)
        
        print(
            f"  [7e4] m={m} n={n} open_t={open_t} priority={priority_t} free_bits={2*free_bit_index(m)}",
            flush=True,
        )
        
        # Optional warm-start loading
        warm_bits = None
        if warm_start:
            warm_path = ROOT / "data" / "phase7" / "7e1" / f"m{m}_best.json"
            if warm_path.exists():
                try:
                    import json
                    warm_data = json.loads(warm_path.read_text())
                    warm_bits = warm_data.get("bits")
                    print(f"  [7e4] loaded warm-start from {warm_path}", flush=True)
                except Exception:
                    pass
        
        model, xs, _ = build_triangle_free_two_block_model(m)
        
        t_pool = time.perf_counter()
        pool_done = "rounds"
        cut_count = 0
        
        for rnd in range(1, rounds + 1):
            left = pool_wall - (time.perf_counter() - t_pool)
            if left <= 0.05:
                print(
                    f"    [7e4] round {rnd}/{rounds} pool_wall exhausted ({pool_wall}s) — next m",
                    flush=True,
                )
                pool_done = "wall"
                break
            
            if cut_count >= cuts_cap:
                print(
                    f"    [7e4] round {rnd}/{rounds} cuts saturated at {cuts_cap} — next m",
                    flush=True,
                )
                pool_done = "cuts_saturated"
                break
            
            sat_budget = min(sat_lim, left)
            status, bits, sat_s = solve_two_block_model(
                model, xs, m, sat_budget, seed=20260912 + rnd + m_idx * 1000
            )
            
            print(
                f"    [7e4] round {rnd}/{rounds} SAT {status} {sat_s:.3f}s "
                f"(budget {sat_budget:.2f}s left {left:.2f}s)",
                flush=True,
            )
            
            if status == "INFEASIBLE":
                print(
                    "    [7e4]   pool UNSAT under triangle-free + IS-cuts — "
                    "every feasible (S0,S1) was cut. Not a cell.",
                    flush=True,
                )
                total_unsat += 1
                pool_done = "unsat"
                break
            
            if bits is None:
                print(
                    "    [7e4]   SAT UNKNOWN/timeout ≠ accept. No bits, so no cut. Next m.",
                    flush=True,
                )
                total_timeouts += 1
                pool_done = "sat_timeout"
                break
            
            S0, S1 = bits_to_s0_s1(m, bits)
            
            s0_arr = np.zeros(m, dtype=np.uint8)
            s1_arr = np.zeros(m, dtype=np.uint8)
            for d in S0:
                s0_arr[d % m] = 1
            for d in S1:
                s1_arr[d % m] = 1
            
            adj = two_block_adj(s0_arr, s1_arr)
            
            # Triangle repair loop (lazy CEGIS)
            tri_fix = 0
            while not _k4_free_adj(adj):
                tri_fix += 1
                support = first_triangle_support_two_block(m, bits)
                if not support or len(support) < 1:
                    print(
                        f"    [7e4]   N(0) triangle but no support bits found — nogood",
                        flush=True,
                    )
                    model.Add(assignment_nogood(xs, m, bits))
                    break
                
                print(
                    f"    [7e4]   N(0) triangle fix={tri_fix} TRIANGLE-CUT |lits|={len(support)}",
                    flush=True,
                )
                model.Add(sum(xs[i] for i in support) <= len(support) - 1)
                total_cuts += 1
                
                left = pool_wall - (time.perf_counter() - t_pool)
                if left <= 0.05 or tri_fix >= 4:
                    print(
                        f"    [7e4]   triangle-repair cap — nogood and continue",
                        flush=True,
                    )
                    model.Add(assignment_nogood(xs, m, bits))
                    break
                
                # Re-solve after triangle cut
                status, bits, sat_s = solve_two_block_model(
                    model, xs, m, min(sat_lim, left), seed=20260912 + rnd + m_idx * 1000 + tri_fix
                )
                print(f"    [7e4]   re-SAT {status} {sat_s:.3f}s after triangle-cut", flush=True)
                
                if status == "INFEASIBLE":
                    total_unsat += 1
                    pool_done = "unsat"
                    bits = None
                    break
                
                if bits is None:
                    total_timeouts += 1
                    pool_done = "sat_timeout"
                    break
                
                # Rebuild adj for next iteration
                S0, S1 = bits_to_s0_s1(m, bits)
                s0_arr = np.zeros(m, dtype=np.uint8)
                s1_arr = np.zeros(m, dtype=np.uint8)
                for d in S0:
                    s0_arr[d % m] = 1
                for d in S1:
                    s1_arr[d % m] = 1
                adj = two_block_adj(s0_arr, s1_arr)
            
            if pool_done in ("unsat", "sat_timeout"):
                break
            
            if bits is None or not _k4_free_adj(adj):
                continue
            
            # Convert to nbr format
            nbr = _adj_nbr(adj)
            greedy_alpha = greedy_mis(nbr)
<<<<<<< HEAD
            
            # Calculate degree and leftover for logging
            deg_0 = int(adj[0].sum())
            leftover = n - deg_0 - 1
=======
>>>>>>> d807510 (Fix PR #2 blockers: lazy triangle repair + drop greedy +1)
            
            print(
                f"    [7e4]   |S0|={len(S0)} |S1|={len(S1)} deg(0)={deg_0} leftover={leftover} "
                f"K4_free=True greedyα={greedy_alpha}",
                flush=True,
            )
            
            # All-zero check: if empty (S0,S1), treat as useless
            if len(S0) == 0 and len(S1) == 0:
                print(
                    "    [7e4]   all-zero assignment (empty S0,S1) — nogood and continue",
                    flush=True,
                )
                model.Add(assignment_nogood(xs, m, bits))
                continue
            
            # Try decide_alpha_le for priority targets
            found_witness = False
            for t_cell in priority_t:
                if greedy_alpha >= t_cell:
                    print(
                        f"    [7e4]   greedyα={greedy_alpha}≥{t_cell} — skip decide for t={t_cell}",
                        flush=True,
                    )
                    continue
                
                dec = decide_alpha_le(nbr, target=t_cell, time_limit=mis_lim)
                
                print(
                    f"    [7e4]   decide α≥{t_cell} found={dec['found']} timeout={dec['timed_out']} "
                    f"exact={dec.get('exact')} backend={dec.get('backend')} nodes={dec.get('nodes')}",
                    flush=True,
                )
                
                if dec["timed_out"]:
                    print(
                        "    [7e4]   timeout ≠ accept. Nogood this (S0,S1) (do not cut on missing I).",
                        flush=True,
                    )
                    total_timeouts += 1
                    model.Add(assignment_nogood(xs, m, bits))
                    found_witness = False
                    break
                
                if not dec["found"] and dec.get("exact"):
                    # Residual accept
                    mix = mixed_set_check(adj[0], t_cell, time_limit=min(20.0, mis_lim))
                    cell_ok = bool(dec.get("exact") and mix.get("mixed_ok"))
                    published = R4_LOWER.get(t_cell, 0)
                    beats = cell_ok and n + 1 > published
                    
                    if beats:
                        print(
                            f"    [7e4]   CELL? R(4,{t_cell}) ≥ {n + 1}  "
                            f"(published ≥ {published})  mixed_ok",
                            flush=True,
                        )
                    else:
                        print(
                            f"    [7e4]   residual_only n={n} t={t_cell}  {mix.get('reason')}",
                            flush=True,
                        )
                    
                    # Emit decision record
                    meta = {
                        "construction_type": "block_circulant_two_orbit",
                        "gpu_kernel": "7e4 two-orbit CEGIS + decide α",
                        "field": f"Z_2 × Z_{m}",
                        "params": {
                            "m": m,
                            "n": n,
                            "kind": "7e4",
                            "t_cell": t_cell,
                            "k4_free": True,
                            "rounds": rnd,
                            "cuts": cut_count,
                            "S0": list(S0),
                            "S1": list(S1),
                        },
                        "run001": "not_done",
                    }
                    from .certify_fast import certify_fast
                    cert = certify_fast(adj, time_limit=0.05)
                    pack = cert
                    pack["exact"] = beats
                    if not beats:
                        pack["omega_exact"] = None
                        pack["alpha_exact"] = None
                    
                    rec = emit_decision(adj[0] if adj.ndim == 2 else adj, meta, pack, "7e4", "R(4,t)")
                    rec["exact"] = beats
                    rows.append(rec)
                    
                    pool_done = "accept" if beats else "residual_only"
                    found_witness = False
                    break
                
                if dec["found"]:
                    # Extract witness
                    I = extract_is_full_graph(nbr, t_cell, seconds=min(2.0, left))
                    
                    if not I:
                        print(
                            f"    [7e4]   found=True but witness extract failed (target={t_cell}). "
                            "Nogood (S0,S1), no cut. Timeout≠cut.",
                            flush=True,
                        )
                        model.Add(assignment_nogood(xs, m, bits))
                        found_witness = False
                        break
                    
                    ok_ind = verify_is_independent_full(adj, I)
                    print(
                        f"    [7e4]   witness |I|={len(I)} independent={ok_ind} "
                        f"I[:16]={I[:16]}{'…' if len(I) > 16 else ''}",
                        flush=True,
                    )
                    
                    if not ok_ind or len(I) < t_cell:
                        print("    [7e4]   witness failed check — nogood (S0,S1), no cut.", flush=True)
                        model.Add(assignment_nogood(xs, m, bits))
                        found_witness = False
                        break
                    
                    lits = is_cut_two_block_lits(m, I)
                    
                    if not lits:
                        print(
                            "    [7e4]   empty cut — free bits cannot hit I. "
                            "Model → unsat. Pool dead for this t. Not a cell.",
                            flush=True,
                        )
                        model.Add(sum(xs) <= -1)
                        total_unsat += 1
                        pool_done = "empty_cut"
                        found_witness = False
                        break
                    
                    print(
                        f"    [7e4]   CUT |lits|={len(lits)} (hit I: put edge inside I)",
                        flush=True,
                    )
                    model.Add(sum(xs[i] for i in lits) >= 1)
                    cut_count += 1
                    total_cuts += 1
                    found_witness = True
                    
                    write_status(
                        job="7e4",
                        state="running",
                        m=m,
                        round=rnd,
                        cuts=total_cuts,
                        ms_done=m_idx,
                    )
                    break
            
            if found_witness:
                # Continue to next round
                continue
            
            if pool_done in ("accept", "residual_only", "unsat", "empty_cut", "sat_timeout"):
                break
        
        print(
            f"  [7e4] m={m} done={pool_done} wall={time.perf_counter() - t_pool:.2f}s "
            f"cuts_this_m={cut_count} cuts_so_far={total_cuts}",
            flush=True,
        )
        
        append_record(
            {
                "job": "7e4",
                "m": m,
                "n": n,
                "done": pool_done,
                "cuts": cut_count,
                "rounds": rnd if 'rnd' in locals() else 0,
            }
        )
        
        # Write summary for this m
        summary_path = dump_dir / f"m{m}_SUMMARY.json"
        summary = {
            "m": m,
            "n": n,
            "done": pool_done,
            "cuts": cut_count,
            "total_cuts": total_cuts,
            "rounds": rnd if 'rnd' in locals() else 0,
        }
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    
    write_status(
        job="7e4",
        state="done",
        graphs=len(rows),
        ms=ms,
        cuts=total_cuts,
        timeouts=total_timeouts,
        unsat_pools=total_unsat,
    )
    
    print(
        f"  [7e4] summary ms={ms} cuts={total_cuts} timeouts={total_timeouts} "
        f"unsat_pools={total_unsat} graphs={len(rows)}  published cell still 252 unless CELL?",
        flush=True,
    )
    
    return rows


def job_phase7() -> list[dict]:
    """6a gate, then Looks 3 → 1 → 6 → 2 → 4 → 5."""
    if HALT_PATH.exists() and os.environ.get("RAMSEY_FORCE_7") != "1":
        HALT_PATH.unlink()
    write_status(phase="phase7", started_utc=_now(), state="running")
    if not require_6a():
        write_status(phase="phase7", state="halted_6a", finished_utc=_now())
        return []
    rows: list[dict] = []
    for fn, name in (
        (job_7a, "7a"),
        (job_7b, "7b"),
        (job_7c, "7c"),
        (job_7d, "7d"),
        (job_7e, "7e"),
        (job_7f, "7f"),
    ):
        print(f"== phase7 → {name} ==", flush=True)
        rows.extend(fn())
    write_status(phase="phase7", state="done", finished_utc=_now(), graphs=len(rows))
    print("== phase7 done. Published cell is still 252 unless a CELL? line fired. ==", flush=True)
    return rows
