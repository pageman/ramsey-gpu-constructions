"""Phase 7: Look 1–6 after job 6a (WHERE-TO-LOOK.md).

Order: 6a gate → 7a referee bench → 7b 2-class hunt → 7c SAT-on-pool
if walks die → 7d R(3,t) t≥50 → 7e 2-polycirculant → 7f polarity leftover.
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
