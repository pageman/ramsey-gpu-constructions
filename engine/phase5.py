"""Jobs 5a–5f and phase5 (5a then halt unless Yu residual is certified)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from .kernels.decide_alpha import (
    CERT_PATH,
    decide_alpha_le,
    load_yu_cert,
    mixed_set_check,
    shash_distances,
    write_yu_cert,
)
from .kernels.residual import distances_to_row, greedy_alpha_row, residual_nbr
from .kernels.bitset_mcs import greedy_mis
from .registry import append_record
from .scale import limits, scale_name
from .yu_pool import (
    R4_LOWER,
    certify_row_decision,
    iter_yu_pools,
    load_yu_witness,
    search_pool,
    verify_yu_witness,
)

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "data" / "phase5.status.json"
HALT_PATH = ROOT / "data" / "phase5.halt"


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


def phase5_halted() -> bool:
    return HALT_PATH.exists()


def _cpsat_lower_bound(nbr: list[int], want: int, seconds: float) -> dict:
    """Optional: find an independent set of size `want` (Yu used this for 18)."""
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return {"available": False, "found": False, "reason": "ortools not installed"}
    n = len(nbr)
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"v{i}") for i in range(n)]
    for i in range(n):
        mask = nbr[i]
        j = 0
        while mask and j < n:
            if mask & 1 and j > i:
                model.Add(xs[i] + xs[j] <= 1)
            mask >>= 1
            j += 1
    model.Add(sum(xs) >= want)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = int(os.environ.get("RAMSEY_SAT_WORKERS", "8"))
    t0 = time.perf_counter()
    status = solver.Solve(model)
    found = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return {
        "available": True,
        "found": found,
        "status": int(status),
        "seconds": time.perf_counter() - t0,
        "want": want,
    }


def job_5a() -> list[dict]:
    """Recertify Yu residual 186: decision α < 19 with the decide kernel."""
    from .jobs import _decision_cert, emit_decision

    lim = limits()
    tlim = float(os.environ.get("RAMSEY_5A_LIMIT", lim.get("yu_5a_limit", 600)))
    print(f"  [5a] Yu residual decision  α<19  limit={tlim}s  (decision, not Russian-doll)", flush=True)
    write_status(job="5a", state="running", alpha_certified=False, halt=False)
    if HALT_PATH.exists():
        HALT_PATH.unlink()

    w = load_yu_witness()
    p = int(w["p"])
    row = distances_to_row(p, w["S"])
    gate = verify_yu_witness(time_limit=min(8.0, tlim))
    print(
        f"  [5a] structural={gate['structural_ok']}  residual={gate['residual_n']}  "
        f"tri_free={gate['triangle_free']}  old_kernel={gate['cert'].get('reason')}",
        flush=True,
    )
    nbr = residual_nbr(row)
    print(f"  [5a] residual n={len(nbr)} greedyα={1 + greedy_mis(nbr)}", flush=True)

    sat = _cpsat_lower_bound(nbr, want=18, seconds=min(45.0, tlim / 4))
    print(f"  [5a] CP-SAT 18-IS {sat}", flush=True)

    dec = decide_alpha_le(nbr, target=19, time_limit=tlim)
    print(
        f"  [5a] decide α≥19 found={dec['found']} timed_out={dec['timed_out']} "
        f"nodes={dec['nodes']} {dec['seconds']:.3f}s backend={dec['backend']}",
        flush=True,
    )

    alpha_certified = bool(
        gate["structural_ok"]
        and not dec["found"]
        and not dec["timed_out"]
        and dec.get("exact")
    )
    payload = {
        "citation": w.get("citation"),
        "p": p,
        "residual_n": len(nbr),
        "structural_ok": gate["structural_ok"],
        "alpha_certified": alpha_certified,
        "decide": dec,
        "cpsat_lb18": sat,
        "seconds": dec["seconds"],
        "backend": dec.get("backend"),
        "written_utc": _now(),
        "note": (
            "Residual decision only. Mixed-set / full-graph α is job 5b. "
            "Do not print CELL? from this file."
        ),
    }
    write_yu_cert(payload)
    print(f"  [5a] wrote {CERT_PATH}  alpha_certified={alpha_certified}", flush=True)
    append_record(
        {
            "job": "5a",
            "cell": "R(4,20)",
            "graph_id": "yu_residual_186",
            "N": len(nbr),
            "exact": alpha_certified,
            "alpha_certified": alpha_certified,
            "nodes": dec.get("nodes"),
            "backend": dec.get("backend"),
        }
    )
    pack = _decision_cert(
        p,
        3 if gate["triangle_free"] else 4,
        1 + int(dec.get("lower") or 0),
        19 if alpha_certified else None,
        alpha_certified,
        f"decide:{dec.get('backend')}",
    )
    meta = {
        "construction_type": "yu_pool",
        "gpu_kernel": "decide_alpha_le residual 186",
        "field": f"Z/{p}Z",
        "params": {"p": p, "e": 5, "kind": "yu_5a_residual", "shash": shash_distances(w["S"])},
        "run001": "not_done",
    }
    rec = emit_decision(row, meta, pack, "5a", "R(4,20)")
    write_status(
        job="5a",
        state="done",
        alpha_certified=alpha_certified,
        halt=not alpha_certified,
        decide=dec,
        cpsat_lb18=sat,
    )
    if not alpha_certified:
        HALT_PATH.write_text(
            f"5a failed: found={dec['found']} timed_out={dec['timed_out']} "
            f"backend={dec.get('backend')} at {_now()}\n"
        )
        print(
            "  [5a] HALT. Residual 186 not decided. Do not start 5c. "
            "Published cell remains 252.",
            flush=True,
        )
    else:
        print("  [5a] GREEN. Residual has no 19-IS. Referee may hunt.", flush=True)
    return [rec]


def job_5b() -> list[dict]:
    """Freeze the referee: width, timeout≠accept, mixed-set rule."""
    from .jobs import _decision_cert, emit_decision
    from .kernels.sieve import quadratic_residue_row

    print("  [5b] referee contract", flush=True)
    write_status(job="5b", state="running")
    cert = load_yu_cert()
    if not cert or not cert.get("alpha_certified"):
        print("  [5b] Yu cert not green — still freeze the API, no hunt.", flush=True)

    # Complete graph: greedy α=1 < 19, so the width gate must fire (empty 257
    # would greedy-accept and never reach skip_n>256).
    complete = [((1 << 257) - 1) ^ (1 << i) for i in range(257)]
    skip = decide_alpha_le(complete, target=19, time_limit=0.2)
    if not (skip["timed_out"] and skip["backend"] == "skip_n>256" and not skip["exact"]):
        raise SystemExit(f"5b contract failed: n=257 must skip, got {skip}")
    print(f"  [5b] n=257 skip OK  {skip['backend']}", flush=True)

    # Paley(17) residual must still be exact (α=2 on 8 verts ⇒ α(G)=3).
    prow = quadratic_residue_row(17)
    pcert = certify_row_decision(prow, t_cell=4, time_limit=2.0)
    print(f"  [5b] Paley(17) decision {pcert.get('reason')} exact={pcert.get('exact')}", flush=True)

    # Toy circulant mixed-set (small).
    toy = distances_to_row(13, [1, 5])
    mix = mixed_set_check(toy, t_cell=4, time_limit=3.0)
    print(f"  [5b] toy mixed {mix}", flush=True)

    append_record(
        {
            "job": "5b",
            "cell": "cert",
            "graph_id": "decide_alpha_le",
            "N": 256,
            "exact": False,
            "skip_n257": True,
            "mixed_rule": "CELL? only if mixed_ok",
        }
    )
    pack = _decision_cert(17, 3, 3, 3 if pcert.get("exact") else None, bool(pcert.get("exact")), "decide")
    meta = {
        "construction_type": "paley_prime",
        "gpu_kernel": "5b referee freeze",
        "field": "F_17",
        "params": {"p": 17, "kind": "5b_referee"},
        "run001": "done",
    }
    rec = emit_decision(prow, meta, pack, "5b", "cert")
    write_status(job="5b", state="done", skip_n257=True, paley17_exact=bool(pcert.get("exact")))
    return [rec]


def job_5c() -> list[dict]:
    """Yu pool hunt only on residuals the referee can finish."""
    from .jobs import _decision_cert, emit_decision

    if phase5_halted() and os.environ.get("RAMSEY_FORCE_5C") != "1":
        print("  [5c] HALT file present — skip hunt.", flush=True)
        write_status(job="5c", state="skipped", reason="5a halt")
        return []
    cert = load_yu_cert()
    if not (cert and cert.get("alpha_certified")) and os.environ.get("RAMSEY_FORCE_5C") != "1":
        print("  [5c] no alpha_certified cert — skip.", flush=True)
        write_status(job="5c", state="skipped", reason="no cert")
        return []

    lim = limits()
    tlim = float(lim["yu_mis_limit"])
    p_lo, p_hi = int(lim["yu_p_lo"]), int(lim["yu_p_hi"])
    walks = int(lim["yu_walks"])
    anneal = int(lim["yu_anneal"])
    rng = np.random.default_rng(20260830)
    print(f"  [5c] hunt p∈[{p_lo},{p_hi}] walks={walks} anneal={anneal} mis={tlim}s", flush=True)
    write_status(job="5c", state="running", p_lo=p_lo, p_hi=p_hi)
    rows: list[dict] = []
    last_p = None
    for spec in iter_yu_pools(p_lo, p_hi):
        if spec["p"] != last_p:
            last_p = spec["p"]
            append_record({"job": "5c", "checkpoint": True, "p": last_p})
            write_status(job="5c", state="running", p=last_p)
        t_cell = 20
        for t, lb in sorted(R4_LOWER.items()):
            if spec["p"] + 1 > lb:
                t_cell = t
                break
        # Skip pools whose *minimum* residual (max |S|=|pool|) still exceeds width.
        max_s = len(spec["pool"])
        min_resid = spec["p"] - 1 - 2 * max_s
        if min_resid > 256:
            print(
                f"  [5c] skip p={spec['p']} e={spec['e']} min_resid={min_resid}>256",
                flush=True,
            )
            continue
        print(
            f"  [5c] p={spec['p']} e={spec['e']} D{spec['i']}∪D{spec['j']} "
            f"pool={len(spec['pool'])} t={t_cell}",
            flush=True,
        )
        hits = search_pool(spec, walks, anneal, t_cell, tlim, rng, mis_keep=int(lim.get("yu_mis_keep", 4)))
        for h in hits:
            S = h["S"]
            r = h["row"]
            c = h["cert"]
            resid = spec["p"] - 1 - int(r.sum())
            if resid > 256:
                print(f"  [5c] drop residual {resid}>256", flush=True)
                continue
            mix = mixed_set_check(r, t_cell, time_limit=min(20.0, tlim))
            cell_ok = bool(c.get("exact") and not c.get("rejected") and mix.get("mixed_ok"))
            meta = {
                "construction_type": "yu_pool",
                "gpu_kernel": "5c process + decide_alpha_le",
                "field": f"Z/{spec['p']}Z",
                "params": {
                    "p": spec["p"],
                    "e": spec["e"],
                    "i": spec["i"],
                    "j": spec["j"],
                    "kind": "5c",
                    "shash": shash_distances(S),
                    "S": S,
                },
                "run001": "not_done",
            }
            pack = _decision_cert(
                spec["p"],
                3,
                int(c.get("alpha_lower") or 0),
                c.get("alpha_upper") if cell_ok else None,
                cell_ok,
                "decide",
            )
            rows.append(emit_decision(r, meta, pack, "5c", "R(4,t)"))
            published = R4_LOWER.get(t_cell, 0)
            if cell_ok and spec["p"] + 1 > published:
                print(
                    f"  [5c] CELL? R(4,{t_cell}) ≥ {spec['p'] + 1}  (published ≥ {published})  mixed_ok",
                    flush=True,
                )
            elif c.get("exact") and not c.get("rejected"):
                print(
                    f"  [5c] residual_only p={spec['p']} resid={resid}  {mix.get('reason')}",
                    flush=True,
                )
    write_status(job="5c", state="done", graphs=len(rows))
    return rows


def _middle_third_bits(n: int) -> np.ndarray:
    """Nonempty Schur-ish seed: distances in (⌊n/3⌋, ⌊n/2⌋]."""
    half = n // 2
    bits = np.zeros(half, dtype=np.uint8)
    lo = n // 3
    for d in range(lo + 1, half):
        bits[d] = 1
    if int(bits.sum()) == 0 and half > 1:
        bits[half - 1] = 1
    return bits


def job_5d() -> list[dict]:
    """R(3,t) t≥50 from a nonempty middle-third seed."""
    from .jobs import _decision_cert, emit_decision
    from .kernels.cayley import row_from_bits, triangle_free_circulant

    if phase5_halted() and os.environ.get("RAMSEY_FORCE_5DEF") != "1":
        print("  [5d] HALT — skip.", flush=True)
        write_status(job="5d", state="skipped")
        return []
    lim = limits()
    t_cell = int(lim["r3_t"])
    steps = int(lim["r3_steps"])
    tlim = float(lim["yu_mis_limit"])
    rng = np.random.default_rng(50)
    rows: list[dict] = []
    print(f"  [5d] t={t_cell} n={lim['r3_n']}  middle-third seed", flush=True)
    write_status(job="5d", state="running")
    for n in lim["r3_n"]:
        n = int(n)
        if n % 2 == 0:
            continue
        half = n // 2
        bits = _middle_third_bits(n)
        row = row_from_bits(n, bits)
        if not triangle_free_circulant(row):
            # peel until Schur-legal
            for d in range(half - 1, 0, -1):
                if bits[d]:
                    bits[d] = 0
                    row = row_from_bits(n, bits)
                    if triangle_free_circulant(row) and int(bits.sum()):
                        break
        if not triangle_free_circulant(row) or int(row.sum()) == 0:
            print(f"  [5d] n={n} seed collapsed", flush=True)
            continue
        best_row = row.copy()
        best_g = greedy_alpha_row(row)
        print(f"  [5d] n={n} seed |S|={int(row.sum())//2} greedyα={best_g} ILS {steps}", flush=True)
        for s in range(steps):
            i = int(rng.integers(1, half))
            bits[i] ^= 1
            trial = row_from_bits(n, bits)
            if not triangle_free_circulant(trial):
                bits[i] ^= 1
                continue
            g = greedy_alpha_row(trial)
            row = trial
            if g < best_g or (g == best_g and int(trial.sum()) > int(best_row.sum())):
                best_g = g
                best_row = trial.copy()
            if s % 20 == 0:
                print(f"    step {s} |S|={int(row.sum())//2} greedyα={g} best={best_g}", flush=True)
        row = best_row
        residual = n - 1 - int(row.sum())
        print(f"  [5d] n={n} residual={residual}", flush=True)
        if residual > 256:
            print(f"  [5d] skip residual>{256}", flush=True)
            append_record({"job": "5d", "n": n, "residual": residual, "exact": False})
            continue
        cert = certify_row_decision(row, t_cell, tlim)
        omega = 2 if cert["triangle_free"] else 3
        exact = bool(cert.get("exact") and omega == 2 and not cert.get("rejected"))
        pack = _decision_cert(
            n,
            omega,
            int(cert.get("alpha_lower") or cert.get("alpha_greedy") or 0),
            cert.get("alpha_upper") if exact else None,
            exact,
            "decide",
        )
        meta = {
            "construction_type": "circulant_r3",
            "gpu_kernel": "middle-third seed + incremental Schur + decide",
            "field": f"Z/{n}Z",
            "params": {"n": n, "t": t_cell, "kind": "5d", "S": np.flatnonzero(row).tolist()},
            "run001": "not_done",
        }
        rows.append(emit_decision(row, meta, pack, "5d", "R(3,k)"))
        if exact and n + 1 > 0:
            print(f"  [5d] residual-certified R(3,{t_cell}) > {n}  (check DS1 before shouting)", flush=True)
    write_status(job="5d", state="done", graphs=len(rows))
    return rows


def job_5e() -> list[dict]:
    """Polarity leftover only if n≤width and N+1 beats published R(4,t)."""
    from .constructions import polarity_gq
    from .jobs import _decision_cert, emit_decision, _gq_lines

    if phase5_halted() and os.environ.get("RAMSEY_FORCE_5DEF") != "1":
        print("  [5e] HALT — skip.", flush=True)
        write_status(job="5e", state="skipped")
        return []
    lim = limits()
    tlim = float(lim["yu_mis_limit"])
    rows: list[dict] = []
    write_status(job="5e", state="running")
    for q in lim["gq_clean_q"]:
        q = int(q)
        print(f"  [5e] W(3,{q}) K4-clean…", flush=True)
        adj, meta0 = polarity_gq(q)
        n = int(adj.shape[0])
        lines = _gq_lines(adj)
        live = np.ones(n, dtype=bool)
        for line in lines:
            verts = [v for v in line if live[v]]
            if len(verts) <= 3:
                continue
            deg = adj.sum(axis=1)
            verts.sort(key=lambda v: -int(deg[v]))
            for v in verts[3:]:
                live[v] = False
        keep = np.flatnonzero(live)
        leftover = int(keep.size)
        print(f"  [5e] q={q} raw={n} leftover={leftover}", flush=True)
        if leftover > 256 or leftover == 0:
            print("  [5e] leftover not in bitset range — skip", flush=True)
            append_record({"job": "5e", "q": q, "leftover": leftover, "exact": False})
            continue
        sub = adj[np.ix_(keep, keep)]
        nbr = [0] * leftover
        for i in range(leftover):
            bits = 0
            for j in np.flatnonzero(sub[i]):
                bits |= 1 << int(j)
            nbr[i] = bits
        glo = greedy_mis(nbr)
        mis = decide_alpha_le(nbr, target=glo + 1, time_limit=tlim)
        alpha = glo if (not mis["found"] and not mis["timed_out"]) else (glo + 1 if mis["found"] else None)
        exact = alpha is not None and not mis["timed_out"]
        t_cell = (alpha + 1) if alpha is not None else glo + 1
        published = R4_LOWER.get(t_cell)
        beats = published is not None and leftover + 1 > published
        print(
            f"  [5e] greedyα={glo} α={alpha} exact={exact} R(4,{t_cell})>{leftover} "
            f"published={published} beats={beats}",
            flush=True,
        )
        dummy = np.zeros(leftover, dtype=np.uint8)
        dummy[1 : min(3, leftover)] = 1
        pack = _decision_cert(leftover, 3, glo, alpha if exact and beats else None, bool(exact and beats), "decide")
        meta = {
            "construction_type": "polarity_gq",
            "gpu_kernel": "5e K4-clean + decide + floor gate",
            "field": f"W(3,{q}) leftover",
            "params": {"q": q, "n": leftover, "kind": "5e", "beats_floor": beats},
            "run001": "not_done",
        }
        rec = emit_decision(dummy, meta, pack, "5e", "R(4,t)-geom")
        rec["N"] = leftover
        rows.append(rec)
        if exact and not beats:
            print(
                f"  [5e] exact but below floor — catalogue, not CELL? "
                f"(4c already had R(4,22)>84 vs ≥314)",
                flush=True,
            )
        if exact and beats:
            print(f"  [5e] CELL? R(4,{t_cell}) > {leftover}  vs published ≥ {published}", flush=True)
    write_status(job="5e", state="done", graphs=len(rows))
    return rows


def job_5f() -> list[dict]:
    """Catalogue TG_{d,h} and Yip polynomial Paley. One flag, no night."""
    from .constructions import paley_prime, polynomial_paley_like, tg_dh
    from .jobs import emit
    from .certify_fast import certify_fast

    print("  [5f] catalogue TG / Yip — Hoffman vs Paley, no hunt", flush=True)
    write_status(job="5f", state="running")
    rows: list[dict] = []
    lim = limits()
    tlim = 0.2 if scale_name() == "local" else 1.0
    pairs = ((3, 2), (4, 2)) if scale_name() == "local" else ((3, 2), (4, 2), (5, 2))
    for d, h in pairs:
        try:
            adj, meta = tg_dh(d, h)
        except ValueError as exc:
            print(f"  [5f] TG_{d},{h} skip {exc}", flush=True)
            continue
        cert = certify_fast(adj, time_limit=tlim)
        print(
            f"  [5f] TG_{d},{h} n={adj.shape[0]} deg={meta['params']['degree']} "
            f"k>{cert.get('k_certified')} exact={cert.get('exact')}",
            flush=True,
        )
        rows.append(emit(adj, meta, cert, "5f", "cert"))
    for p in (17, 29, 37):
        if p > int(lim.get("paley_max", 101)) and scale_name() == "local" and p > 17:
            continue
        try:
            adj, meta = polynomial_paley_like(p)
            padj, _ = paley_prime(p)
        except ValueError:
            continue
        cert = certify_fast(adj, time_limit=tlim)
        pcert = certify_fast(padj, time_limit=tlim)
        print(
            f"  [5f] Yip-poly p={p} k>{cert.get('k_certified')} vs Paley k>{pcert.get('k_certified')}",
            flush=True,
        )
        rows.append(emit(adj, meta, cert, "5f", "cert"))
    write_status(job="5f", state="done", graphs=len(rows))
    return rows


def job_phase5() -> list[dict]:
    """5a then halt unless certified; else 5b→5f."""
    write_status(phase="phase5", started_utc=_now(), state="running", halt=False)
    rows = []
    rows.extend(job_5a())
    if phase5_halted() or not (load_yu_cert() or {}).get("alpha_certified"):
        print("== phase5 HALT after 5a. 5b still freezes the API; 5c–5e skipped. ==", flush=True)
        rows.extend(job_5b())
        write_status(phase="phase5", state="halted", finished_utc=_now())
        return rows
    for fn, name in (
        (job_5b, "5b"),
        (job_5c, "5c"),
        (job_5d, "5d"),
        (job_5e, "5e"),
        (job_5f, "5f"),
    ):
        print(f"== phase5 → {name} ==", flush=True)
        rows.extend(fn())
    write_status(phase="phase5", state="done", finished_utc=_now(), graphs=len(rows))
    print("== phase5 done ==", flush=True)
    return rows
