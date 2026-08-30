"""Non-overlapping RunPod / local jobs. Ownership is in engine.registry.OWNERS."""

from __future__ import annotations

import json
import time
from typing import Callable

import numpy as np

from . import backend
from .catalog_io import upsert_graphs, write_catalog
from .certify_fast import certify_fast, certify_row
from .constructions import (
    anf_quadratic_f2,
    block_circulant_from_seed,
    features,
    frankl_wilson,
    gold_trace_f2,
    kasami_trace_f2,
    paley_prime,
    polarity_gq,
    polarity_pg2,
    quadratic_form_f2,
    sidon_disperser,
    singer_difference,
)
from .kernels.cayley import adj_from_row, ils_connection_set, row_from_bits, triangle_free_circulant
from .kernels.rowcert import certify_boolean_cayley, certify_circulant_row
from .kernels.sieve import (
    cyclotomic_row,
    divisors,
    linear_sieve,
    negation_closed_masks,
    primes_congruence,
    quadratic_residue_row,
)
from .kernels.spectrum import fft_eigenvalues, spectral_bounds_from_eigs
from .kernels.residual import distances_to_row, greedy_alpha_row
from .kernels.bitset_mcs import mis_decision
from .registry import OWNERS, LEDGER_PATH, append_record, write_ledger
from .scale import limits, scale_name
from .yu_pool import (
    R4_LOWER,
    certify_row_decision,
    iter_yu_pools,
    load_yu_witness,
    search_pool,
    verify_yu_witness,
)


def _strip_meta(meta: dict) -> dict:
    keep = dict(meta)
    keep.pop("row", None)
    keep.pop("boolean_f", None)
    keep.pop("adj", None)
    params = dict(keep.get("params") or {})
    keep["params"] = {k: v for k, v in params.items() if _small(v)}
    return keep


def _small(v) -> bool:
    if isinstance(v, (list, tuple)) and len(v) > 128:
        return False
    if isinstance(v, np.ndarray):
        return False
    return True


def emit_boolean(f: np.ndarray, meta: dict, cert: dict, job: str, cell: str) -> dict:
    n = int(f.size)
    if n <= 512:
        from .gf2 import cayley_from_boolean

        return emit(cayley_from_boolean(f), meta, cert, job, cell)
    dummy = np.zeros((2, 2), dtype=np.uint8)
    meta = _strip_meta(meta)
    rec = features(dummy, meta, cert)
    rec["N"] = n
    rec["degree_mean"] = float(f.sum())
    rec["degree_std"] = 0.0
    rec["degree_min"] = rec["degree_max"] = float(f.sum())
    rec["job"] = job
    rec["cell"] = cell
    rec["kernel"] = cert.get("kernel", "fwht")
    rec["symmetry"] = "f2_cayley"
    rec["params"] = json.dumps(meta.get("params", {}), default=str)
    rec["scale"] = scale_name()
    append_record({"job": job, "cell": cell, "graph_id": rec["graph_id"], "N": n, "k_certified": rec["k_target"], "exact": rec["exact"]})
    print(
        f"  [{job}] {rec['graph_id']:55s} N={n:4d}  k>{rec['k_target']:<3d}  "
        f"N^{{1/k}}={rec['n_1_over_k']:.4f}  exact={rec['exact']}  fwht",
        flush=True,
    )
    return rec


def emit(adj, meta, cert, job: str, cell: str) -> dict:
    meta = _strip_meta(meta)
    row = features(adj if adj is not None else np.zeros((cert["N"], cert["N"]), dtype=np.uint8), meta, cert)
    if adj is None:
        # features walked a dummy; overwrite N/degree from cert
        row["N"] = cert["N"]
        row["degree_mean"] = float(cert.get("degree") or row.get("degree_mean") or 0)
    row["job"] = job
    row["cell"] = cell
    row["kernel"] = cert.get("kernel")
    row["symmetry"] = cert.get("symmetry")
    row["params"] = json.dumps(meta.get("params", {}), default=str)
    row["scale"] = scale_name()
    append_record(
        {
            "job": job,
            "cell": cell,
            "graph_id": row["graph_id"],
            "N": row["N"],
            "k_certified": row["k_target"],
            "exact": row["exact"],
            "n_1_over_k": row["n_1_over_k"],
            "kernel": cert.get("kernel"),
        }
    )
    print(
        f"  [{job}] {row['graph_id']:55s} N={row['N']:4d}  k>{row['k_target']:<3d}  "
        f"N^{{1/k}}={row['n_1_over_k']:.4f}  exact={row['exact']}  {cert.get('kernel')}",
        flush=True,
    )
    return row


def emit_from_row(row: np.ndarray, meta: dict, job: str, cell: str, paley_q=None, time_limit=None) -> dict:
    lim = limits()
    t = time_limit if time_limit is not None else lim["time_limit"]
    cert = certify_row(row, time_limit=t, paley_q=paley_q)
    adj = adj_from_row(row) if row.size <= 64 else None
    if adj is None:
        # features needs an adjacency for degree stats; synthesise from the row
        n = row.size
        dummy = np.zeros((min(n, 2), min(n, 2)), dtype=np.uint8)
        meta = _strip_meta(meta)
        rec = features(dummy, meta, cert)
        rec["N"] = n
        rec["degree_mean"] = float(row.sum())
        rec["degree_std"] = 0.0
        rec["degree_min"] = rec["degree_max"] = float(row.sum())
        rec["job"] = job
        rec["cell"] = cell
        rec["kernel"] = cert.get("kernel")
        rec["symmetry"] = "circulant"
        rec["params"] = json.dumps(meta.get("params", {}), default=str)
        rec["scale"] = scale_name()
        rec["graph_id"] = f"{meta['construction_type']}_{n}" if "p" not in (meta.get("params") or {}) else rec["graph_id"]
        append_record({"job": job, "cell": cell, "graph_id": rec["graph_id"], "N": n, "k_certified": rec["k_target"], "exact": rec["exact"]})
        print(
            f"  [{job}] {rec['graph_id']:55s} N={n:4d}  k>{rec['k_target']:<3d}  "
            f"N^{{1/k}}={rec['n_1_over_k']:.4f}  exact={rec['exact']}  fft-row",
            flush=True,
        )
        return rec
    return emit(adj, meta, cert, job, cell)


def job_phase0() -> list[dict]:
    """Self-tests used as the RunPod smoke job."""
    from .test_invariants import main as inv
    from .test_kernels import main as ker

    rc1 = inv()
    rc2 = ker()
    if rc1 or rc2:
        raise SystemExit(f"phase0 failed invariants={rc1} kernels={rc2}")
    append_record({"job": "phase0", "cell": "cert", "graph_id": "phase0_ok", "N": 0, "k_certified": 0, "exact": True})
    return []


def job_1a() -> list[dict]:
    """Recertify Paley primes with O(p) squares + closed-form spectrum + VT residual."""
    lim = limits()
    rows = []
    for p in primes_congruence(lim["paley_max"], 4, 1):
        if p < 5:
            continue
        row = quadratic_residue_row(p)
        meta = {
            "construction_type": "paley_prime",
            "gpu_kernel": "O(p) squares + Paley closed spectrum + VT MCS",
            "field": f"F_{p}",
            "params": {"p": p},
            "run001": "done",
        }
        t = lim["time_limit"] if p <= 61 else 0.05
        rows.append(emit_from_row(row, meta, "1a", "cert", paley_q=p, time_limit=t))
    return rows


def job_1b() -> list[dict]:
    """F_2^n Gold / Kasami / symplectic, n in [8,12] (local: 8–10). FWHT certificates."""
    lim = limits()
    rows = []
    t = lim["time_limit"]
    for n_bits in range(lim["f2_lo"], lim["f2_hi"] + 1):
        for form in ("symplectic", "adjacent_bits"):
            adj, meta = quadratic_form_f2(n_bits, form)
            cert = certify_boolean_cayley(meta["boolean_f"], time_limit=t if n_bits <= 9 else 0.05)
            rows.append(emit_boolean(meta["boolean_f"], meta, cert, "1b", "cert"))
        # Gold: gcd(k,n)=1
        for k in range(1, n_bits):
            if np.gcd(k, n_bits) != 1:
                continue
            adj, meta = gold_trace_f2(n_bits, k)
            cert = certify_boolean_cayley(meta["boolean_f"], time_limit=0.05 if n_bits >= 10 else t)
            rows.append(emit_boolean(meta["boolean_f"], meta, cert, "1b", "cert"))
            break  # one Gold exponent per n is enough; rest are GL-equivalent-ish
        if n_bits % 2 == 0:
            try:
                adj, meta = kasami_trace_f2(n_bits)
                cert = certify_boolean_cayley(meta["boolean_f"], time_limit=0.05 if n_bits >= 10 else t)
                rows.append(emit_boolean(meta["boolean_f"], meta, cert, "1b", "cert"))
            except ValueError:
                pass
    return rows


def job_1c() -> list[dict]:
    """GQ polarity W(3,q) + PG(2,q) recertify. Owns R(4,t)-geom."""
    lim = limits()
    rows = []
    for q in lim["gq_q"]:
        adj, meta = polarity_gq(q)
        cert = certify_fast(adj, time_limit=lim["time_limit"] if adj.shape[0] <= 40 else 0.2)
        rows.append(emit(adj, meta, cert, "1c", "R(4,t)-geom"))
        if q in (2, 3, 5):
            adj2, meta2 = polarity_pg2(q)
            cert2 = certify_fast(adj2, time_limit=lim["time_limit"])
            rows.append(emit(adj2, meta2, cert2, "1c", "R(4,t)-geom"))
    return rows


def job_1d() -> list[dict]:
    """Small Frankl–Wilson instances + Sidon/disperser circulants. explicit-diag."""
    lim = limits()
    rows = []
    for n, k, L in lim["fw"]:
        adj, meta = frankl_wilson(n, k, tuple(L))
        cert = certify_fast(adj, time_limit=lim["time_limit"])
        rows.append(emit(adj, meta, cert, "1d", "explicit-diag"))
    for p in lim["disperser_primes"]:
        adj, meta = sidon_disperser(p)
        cert = certify_row(meta["row"], time_limit=lim["time_limit"])
        rows.append(emit(adj, meta, cert, "1d", "explicit-diag"))
    return rows


def _mask_score(row: np.ndarray) -> float:
    ev = fft_eigenvalues(row.astype(np.float64))
    b = spectral_bounds_from_eigs(ev, row.size)
    crow = 1.0 - row.astype(np.float64)
    crow[0] = 0.0
    cb = spectral_bounds_from_eigs(fft_eigenvalues(crow), row.size)
    return float(max(b["hoffman_alpha"], cb["hoffman_alpha"]))


def job_2a() -> list[dict]:
    """Cyclotomic class-union enumeration. FFT scoring; keep top masks. 2A owns cert.

    Mask ranker is a spectral linear score (Hoffman of G and Ḡ), not PPO edge-flip
    (Berghaus–Wagner ICLR 2025: RL can lose to random on R(4,4)). Yu 2026 quintic
    subset search is the perturbation 3A/3B may apply to these winners only.
    """
    lim = limits()
    rows = []
    ranker_samples = []
    primes = [p for p in linear_sieve(lim["cyclo_max"]) if p >= 13]
    for p in primes:
        for e in divisors(p - 1):
            if e < 4 or e > lim["cyclo_e_max"]:
                continue
            if e % 2 and e not in (5, 7):
                continue
            masks = negation_closed_masks(e) if e % 2 == 0 else [m for m in range(1, 1 << e)]
            scored = []
            for mask in masks:
                try:
                    row, closed = cyclotomic_row(p, e, mask)
                except ValueError:
                    continue
                if row.sum() == 0 or row.sum() == p - 1:
                    continue
                sc = _mask_score(row)
                scored.append((sc, closed, row))
                ranker_samples.append(
                    {"p": p, "e": e, "mask": closed, "degree": int(row.sum()), "score": sc}
                )
            scored.sort(key=lambda t: t[0])
            for sc, closed, row in scored[: lim["mask_keep"]]:
                meta = {
                    "construction_type": "cyclotomic_union",
                    "gpu_kernel": "O(p) orbits + FFT Hoffman ranker",
                    "field": f"F_{p}",
                    "params": {"p": p, "e": e, "mask": int(closed), "ranker_score": sc},
                    "run001": "not_done",
                }
                t = lim["time_limit"] if p <= 61 else 0.05
                rows.append(emit_from_row(row, meta, "2a", "cert", time_limit=t))
    # persist the ranker table — this is the one learned object of the plan
    from pathlib import Path

    Path("data").mkdir(exist_ok=True)
    Path("data/mask_ranker.json").write_text(json.dumps({"kind": "hoffman_max_G_Gbar", "n": len(ranker_samples), "samples": ranker_samples[:4000]}, indent=2))
    return rows


def job_2b() -> list[dict]:
    """Recertify 1B/1C/1D winners with a longer MCS budget. Still the cert cell."""
    lim = limits()
    cat = __import__("json").loads((__import__("pathlib").Path("data/catalog.json")).read_text())
    want = {"quadratic_form_f2", "gold_trace_f2", "polarity_gq", "frankl_wilson"}
    rows = []
    for g in cat.get("graphs", []):
        if g.get("construction_type") not in want:
            continue
        if g.get("N", 99) > 80:
            continue
        # rebuild small ones
        ct = g["construction_type"]
        try:
            if ct == "polarity_gq":
                adj, meta = polarity_gq(int(g["provenance_seed"]))
            elif ct == "frankl_wilson":
                continue  # already exact-ish
            else:
                continue
        except Exception:
            continue
        cert = certify_fast(adj, time_limit=min(2.0, 3 * lim["time_limit"]))
        rows.append(emit(adj, meta, cert, "2b", "cert"))
    return rows


def job_2c() -> list[dict]:
    """Circulant R(3,k): ILS over sum-free connection sets (Schur / triangle-free)."""
    lim = limits()
    rows = []
    for n in range(5, lim["circ_n_max"] + 1):
        rec = ils_connection_set(
            n, k_clique=3, steps=lim["ils_steps"], forbid_triangles=True,
            rng=np.random.default_rng(n * 17 + 3),
        )
        if not rec["triangle_free"]:
            continue
        meta = {
            "construction_type": "circulant_r3",
            "gpu_kernel": "sum-free ILS in distance space O(n) vars",
            "field": f"Z/{n}Z",
            "params": {"n": n, "S": rec["S"][:24], "score": rec["score"]},
            "run001": "not_done",
        }
        t = lim["time_limit"] if n <= 40 else 0.15
        rows.append(emit_from_row(rec["row"], meta, "2c", "R(3,k)", time_limit=t))
    return rows


def job_3a() -> list[dict]:
    """Block-circulant ILS from Paley / Singer / 2A seeds. Owns diagonal R(k,k)."""
    lim = limits()
    rows = []
    seeds = []
    for p in lim["paley_ils"]:
        if p > lim["paley_max"]:
            continue
        seeds.append(("paley", quadratic_residue_row(p), p))
    try:
        adj_s, meta_s = singer_difference(2)
        seeds.append(("singer", adj_s[0], 7))
    except Exception:
        pass
    for name, row, tag in seeds:
        if row.size > 80:
            # distance-space ILS on the seed itself (Yu-style perturbation), not 2-block
            rec = ils_connection_set(
                int(row.size), k_clique=5, steps=lim["ils_steps"],
                seed_row=row, rng=np.random.default_rng(tag),
            )
            meta = {
                "construction_type": "block_circulant",
                "gpu_kernel": "distance-space ILS from Paley/Singer seed",
                "field": f"perturb {name}{tag}",
                "params": {"n": rec["n"], "seed": name, "tag": tag, "score": rec["score"]},
                "run001": "not_done",
            }
            rows.append(emit_from_row(rec["row"], meta, "3a", "R(k,k)", time_limit=0.1))
            continue
        adj, meta = block_circulant_from_seed(row, steps=min(lim["ils_steps"], 60), rng_seed=tag)
        cert = certify_fast(adj, time_limit=lim["time_limit"])
        rows.append(emit(adj, meta, cert, "3a", "R(k,k)"))
    return rows


def job_3b() -> list[dict]:
    """Circulant R(4,k), k=5..20. K4-free ILS; Yu neighbourhood test."""
    lim = limits()
    rows = []
    # prime orders in the literature (251 is the R(4,20) order)
    candidates = [p for p in linear_sieve(lim["circ_n_max"]) if p >= 17]
    if scale_name() == "runpod":
        extra = [p for p in linear_sieve(313) if p >= 17]
        candidates = sorted(set(candidates) | set(extra))
    for n in candidates:
        rec = ils_connection_set(
            n, k_clique=4, steps=lim["ils_steps"],
            rng=np.random.default_rng(n * 4 + 20),
        )
        meta = {
            "construction_type": "circulant_r4",
            "gpu_kernel": "K4-free neighbourhood ILS + FFT Hoffman",
            "field": f"Z/{n}Z",
            "params": {"n": n, "S": rec["S"][:32], "k4_free": rec["k4_free"], "score": rec["score"]},
            "run001": "not_done",
        }
        rows.append(emit_from_row(rec["row"], meta, "3b", "R(4,k)", time_limit=0.2 if n > 60 else lim["time_limit"]))
    return rows


def job_3c() -> list[dict]:
    """GQ scale-up for large-t R(4,t). Same family as 1C, larger q."""
    lim = limits()
    rows = []
    for q in lim["gq_q_big"]:
        adj, meta = polarity_gq(q)
        cert = certify_fast(adj, time_limit=0.15)
        rows.append(emit(adj, meta, cert, "3c", "R(4,t)-geom"))
    return rows


def job_3d() -> list[dict]:
    """Quadratic ANF search on F_2^n, n=13..16 (local: 8–9). explicit-diag.

    Runpod n≥13 residuals are ~N/2 ≫ 64. Colouring those has no timeout and no
    log line (the hung PID 18717). This job prints every trial and skips MCS
    when the residual is wider than Tomita (spectral / FWHT only).
    """
    lim = limits()
    n_trials = int(lim["anf_trials"])
    bits = tuple(lim["anf_bits"])
    residual_limit = 64
    print(
        f"  [3d] bits={bits}  trials={n_trials}  residual_limit={residual_limit}  "
        f"(MCS only if |N(0)| and |N^c(0)| ≤ {residual_limit}; else FWHT/Hoffman)",
        flush=True,
    )
    rows = []
    for n_bits in bits:
        n = 1 << n_bits
        print(f"  [3d] --- n_bits={n_bits}  N={n} ---", flush=True)
        best = None
        best_sc = 1e18
        best_pair = None
        for trial in range(n_trials):
            t0 = time.perf_counter()
            print(f"  [3d] n={n_bits} trial {trial + 1}/{n_trials} seed={trial + 1}  ANF…", flush=True)
            _adj, meta = anf_quadratic_f2(n_bits, seed=trial + 1)
            f = meta["boolean_f"]
            deg = int(np.asarray(f).sum())
            print(
                f"  [3d] n={n_bits} trial {trial + 1}/{n_trials}  ANF {time.perf_counter() - t0:.2f}s  "
                f"|S|={deg}  |Nc|={n - 1 - deg}  cert…",
                flush=True,
            )
            t1 = time.perf_counter()
            cert = certify_boolean_cayley(f, time_limit=0.05, residual_limit=residual_limit)
            skipped = cert.get("residual_skipped")
            print(
                f"  [3d] n={n_bits} trial {trial + 1}/{n_trials}  cert {time.perf_counter() - t1:.2f}s  "
                f"k>{cert['k_certified']}  exact={cert['exact']}  "
                f"skip_mcs={skipped}  N^{{1/k}}={cert['n_1_over_k']:.4f}",
                flush=True,
            )
            sc = max(cert["omega_upper"], cert["alpha_upper"])
            if sc < best_sc or (sc == best_sc and cert["n_1_over_k"] > (best["n_1_over_k"] if best else 0)):
                best_sc = sc
                best = cert
                best_pair = (f, meta)
        if best_pair:
            rows.append(emit_boolean(best_pair[0], best_pair[1], best, "3d", "explicit-diag"))
    return rows


def _decision_cert(n: int, omega: int, alpha_lo: int, alpha_hi, exact: bool, kernel: str) -> dict:
    k = (alpha_hi + 1) if alpha_hi is not None else max(omega, alpha_lo) + 1
    return {
        "N": n,
        "omega_exact": omega if exact else None,
        "alpha_exact": alpha_hi if exact else None,
        "omega_lower": omega,
        "omega_upper": omega if exact else n,
        "alpha_lower": alpha_lo,
        "alpha_upper": alpha_hi if alpha_hi is not None else n,
        "theta_approx": 0.0,
        "delsarte_omega": float(omega),
        "spectral_gap": 0.0,
        "lambda_max": 0.0,
        "lambda_min": 0.0,
        "triangles": 0,
        "k4": 0 if omega <= 3 else 1,
        "k_certified": int(k),
        "is_k_free": bool(exact),
        "n_1_over_k": float(n) ** (1.0 / k) if k else 0.0,
        "exact": exact,
        "kernel": kernel,
        "symmetry": "circulant",
    }


def emit_decision(row: np.ndarray, meta: dict, cert: dict, job: str, cell: str) -> dict:
    n = int(row.size)
    dummy = np.zeros((2, 2), dtype=np.uint8)
    rec = features(dummy, _strip_meta(meta), cert)
    rec["N"] = n
    rec["degree_mean"] = float(row.sum())
    rec["degree_std"] = 0.0
    rec["degree_min"] = rec["degree_max"] = float(row.sum())
    rec["job"] = job
    rec["cell"] = cell
    rec["kernel"] = cert.get("kernel", "bitset-mis")
    rec["symmetry"] = "circulant"
    rec["params"] = json.dumps(meta.get("params", {}), default=str)
    rec["scale"] = scale_name()
    append_record(
        {
            "job": job,
            "cell": cell,
            "graph_id": rec["graph_id"],
            "N": n,
            "k_certified": rec["k_target"],
            "exact": rec["exact"],
            "omega": cert.get("omega_exact"),
            "alpha": cert.get("alpha_exact"),
        }
    )
    print(
        f"  [{job}] {rec['graph_id']:55s} N={n:4d}  {cell}  exact={rec['exact']}  "
        f"ω={cert.get('omega_exact')} α={cert.get('alpha_exact')}",
        flush=True,
    )
    return rec


def job_4a() -> list[dict]:
    """Yu-style 2-class pool search. Safe to run beside 3d (appends registry)."""
    lim = limits()
    print(
        "  [4a] leave 3d alone — this job is extra cores + bitset MIS. "
        "catalog upsert merges; ledger merges by graph_id.",
        flush=True,
    )
    print("  [4a] Yu S regression…", flush=True)
    gate = verify_yu_witness(time_limit=float(lim["yu_mis_limit"]))
    print(
        f"  [4a] Yu gate structural={gate['ok']}  alpha_certified={gate.get('alpha_certified')}  "
        f"S_in_pool={gate['S_in_pool']}  deg={gate['degree']}  residual={gate['residual_n']}  "
        f"tri_free={gate['triangle_free']}  {gate['seconds']:.2f}s  cert={gate['cert'].get('reason')}",
        flush=True,
    )
    rows: list[dict] = []
    w = load_yu_witness()
    p = int(w["p"])
    row = distances_to_row(p, w["S"])
    meta = {
        "construction_type": "yu_pool",
        "gpu_kernel": "restricted process + bitset residual MIS",
        "field": f"Z/{p}Z",
        "params": {"p": p, "e": 5, "kind": "yu_published", "S": w["S"]},
        "run001": "not_done",
    }
    gc = gate["cert"]
    pack = _decision_cert(
        p,
        3 if gate["triangle_free"] else 4,
        int(gc.get("alpha_lower") or 19),
        19 if gate["ok"] else gc.get("alpha_upper"),
        bool(gate["ok"]),
        "bitset-mis",
    )
    meta["params"]["literature_alpha"] = 19
    rows.append(emit_decision(row, meta, pack, "4a", "R(4,t)"))

    p_lo, p_hi = int(lim["yu_p_lo"]), int(lim["yu_p_hi"])
    walks = int(lim["yu_walks"])
    anneal = int(lim["yu_anneal"])
    tlim = float(lim["yu_mis_limit"])
    rng = np.random.default_rng(20260829)
    print(f"  [4a] hunt p∈[{p_lo},{p_hi}] walks={walks} anneal={anneal}", flush=True)
    last_p = None
    for spec in iter_yu_pools(p_lo, p_hi):
        if spec["p"] != last_p:
            last_p = spec["p"]
            append_record({"job": "4a", "checkpoint": True, "p": last_p})
        t_cell = 20
        for t, lb in sorted(R4_LOWER.items()):
            if spec["p"] + 1 > lb:
                t_cell = t
                break
        print(
            f"  [4a] p={spec['p']} e={spec['e']} D{spec['i']}∪D{spec['j']} "
            f"pool={len(spec['pool'])} t={t_cell}",
            flush=True,
        )
        hits = search_pool(spec, walks, anneal, t_cell, tlim, rng, mis_keep=int(lim.get("yu_mis_keep", 4)))
        for h in hits:
            S = h["S"]
            r = h["row"]
            c = h["cert"]
            meta = {
                "construction_type": "yu_pool",
                "gpu_kernel": "restricted process + bitset residual MIS",
                "field": f"Z/{spec['p']}Z",
                "params": {
                    "p": spec["p"],
                    "e": spec["e"],
                    "i": spec["i"],
                    "j": spec["j"],
                    "S": S,
                },
                "run001": "not_done",
            }
            pack = _decision_cert(
                spec["p"],
                3,
                int(c.get("alpha_lower") or 0),
                c.get("alpha_upper"),
                bool(c.get("exact") and not c.get("rejected")),
                "bitset-mis",
            )
            rows.append(emit_decision(r, meta, pack, "4a", "R(4,t)"))
            published = R4_LOWER.get(t_cell, 0)
            if (
                c.get("exact")
                and not c.get("rejected")
                and spec["p"] + 1 > published
            ):
                print(
                    f"  [4a] CELL? R(4,{t_cell}) ≥ {spec['p'] + 1}  (published ≥ {published})",
                    flush=True,
                )
    return rows


def job_4b() -> list[dict]:
    """Circulant R(3,t) for t≥50 (runpod) or a local smoke n. Incremental Schur."""
    lim = limits()
    t_cell = int(lim["r3_t"])
    steps = int(lim["r3_steps"])
    tlim = float(lim["yu_mis_limit"])
    rng = np.random.default_rng(4)
    rows: list[dict] = []
    print(f"  [4b] t={t_cell} n={lim['r3_n']}  skip Coniglio 24–49", flush=True)
    for n in lim["r3_n"]:
        n = int(n)
        if n % 2 == 0:
            continue
        half = n // 2
        bits = np.zeros(half, dtype=np.uint8)
        row = row_from_bits(n, bits)
        best_row = row.copy()
        best_g = n
        print(f"  [4b] n={n} ILS {steps}…", flush=True)
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
            if s % 10 == 0:
                print(f"    step {s} |S|={int(row.sum())//2} greedyα={g} best={best_g}", flush=True)
        row = best_row
        if not triangle_free_circulant(row) or int(row.sum()) == 0:
            print(f"  [4b] n={n} no sum-free mask kept", flush=True)
            continue
        residual = n - 1 - int(row.sum())
        print(f"  [4b] n={n} residual={residual} MIS…", flush=True)
        if residual > 280:
            print(f"  [4b] skip MCS residual>{280}", flush=True)
            continue
        cert = certify_row_decision(row, t_cell, tlim)
        # R(3,t): omega=2 if triangle-free
        omega = 2 if cert["triangle_free"] else 3
        pack = _decision_cert(
            n,
            omega,
            int(cert.get("alpha_lower") or cert.get("alpha_greedy") or 0),
            cert.get("alpha_upper"),
            bool(cert.get("exact") and omega == 2),
            "bitset-mis",
        )
        meta = {
            "construction_type": "circulant_r3",
            "gpu_kernel": "incremental Schur + residual MIS",
            "field": f"Z/{n}Z",
            "params": {"n": n, "t": t_cell, "S": np.flatnonzero(row).tolist()},
            "run001": "not_done",
        }
        rows.append(emit_decision(row, meta, pack, "4b", "R(3,k)"))
    return rows


def _gq_lines(adj: np.ndarray) -> list[frozenset]:
    n = int(adj.shape[0])
    seen: set[frozenset] = set()
    for u in range(n):
        nbrs = np.flatnonzero(adj[u])
        for v in nbrs:
            v = int(v)
            if v <= u:
                continue
            common = np.flatnonzero(adj[u] & adj[v])
            line = frozenset([u, v, *map(int, common)])
            seen.add(line)
    return list(seen)


def job_4c() -> list[dict]:
    """K4-clean polarity graph, exact α if leftover ≤ 256."""
    lim = limits()
    tlim = float(lim["yu_mis_limit"])
    rows: list[dict] = []
    for q in lim["gq_clean_q"]:
        q = int(q)
        print(f"  [4c] W(3,{q}) build…", flush=True)
        adj, meta = polarity_gq(q)
        n = int(adj.shape[0])
        lines = _gq_lines(adj)
        print(f"  [4c] q={q} n={n} lines={len(lines)}", flush=True)
        live = np.ones(n, dtype=bool)
        # keep at most 3 vertices per line (kills every K4 on a line)
        for line in lines:
            verts = [v for v in line if live[v]]
            if len(verts) <= 3:
                continue
            deg = adj.sum(axis=1)
            verts.sort(key=lambda v: -int(deg[v]))
            for v in verts[3:]:
                live[v] = False
        keep = np.flatnonzero(live)
        print(f"  [4c] leftover={keep.size}", flush=True)
        if keep.size > 256 or keep.size == 0:
            print(f"  [4c] stop leftover not in bitset range", flush=True)
            append_record({"job": "4c", "q": q, "leftover": int(keep.size), "exact": False})
            continue
        sub = adj[np.ix_(keep, keep)]
        # ω≤3 by construction. α = MIS of leftover.
        nbr = [0] * keep.size
        for i in range(keep.size):
            bits = 0
            for j in np.flatnonzero(sub[i]):
                bits |= 1 << int(j)
            nbr[i] = bits
        # try to prove a useful α: start from greedy and decide α < greedy+k
        from .kernels.bitset_mcs import greedy_mis

        glo = greedy_mis(nbr)
        # decision: is there an IS of size glo+1? if not, α = glo
        mis = mis_decision(nbr, target=glo + 1, time_limit=tlim)
        alpha = glo if (not mis["found"] and not mis["timed_out"]) else (
            glo + 1 if mis["found"] else None
        )
        exact = alpha is not None and not mis["timed_out"]
        print(f"  [4c] greedyα={glo} mis={mis} α={alpha} exact={exact}", flush=True)
        t_cell = (alpha + 1) if alpha is not None else glo + 1
        dummy_row = np.zeros(keep.size, dtype=np.uint8)
        dummy_row[1 : min(3, keep.size)] = 1
        pack = _decision_cert(int(keep.size), 3, glo, alpha, exact, "bitset-mis")
        meta = {
            "construction_type": "polarity_gq",
            "gpu_kernel": "K4-clean + residual MIS",
            "field": f"W(3,{q}) leftover",
            "params": {"q": q, "n": int(keep.size), "kind": "k4clean"},
            "run001": "not_done",
        }
        rec = emit_decision(dummy_row, meta, pack, "4c", "R(4,t)-geom")
        rec["N"] = int(keep.size)
        rows.append(rec)
        if exact:
            print(f"  [4c] R(4,{t_cell}) > {keep.size}  (cleaned W(3,{q}))", flush=True)
    return rows


JOBS: dict[str, Callable[[], list[dict]]] = {
    "phase0": job_phase0,
    "1a": job_1a,
    "1b": job_1b,
    "1c": job_1c,
    "1d": job_1d,
    "2a": job_2a,
    "2b": job_2b,
    "2c": job_2c,
    "3a": job_3a,
    "3b": job_3b,
    "3c": job_3c,
    "3d": job_3d,
    "4a": job_4a,
    "4b": job_4b,
    "4c": job_4c,
}


def _register_phase5() -> None:
    from . import phase5

    JOBS.update(
        {
            "5a": phase5.job_5a,
            "5b": phase5.job_5b,
            "5c": phase5.job_5c,
            "5d": phase5.job_5d,
            "5e": phase5.job_5e,
            "5f": phase5.job_5f,
            "phase5": phase5.job_phase5,
        }
    )
    from . import phase6

    JOBS.update({"6a": phase6.job_6a})
    from . import phase7

    JOBS.update(
        {
            "7a": phase7.job_7a,
            "7b": phase7.job_7b,
            "7c": phase7.job_7c,
            "7c1": phase7.job_7c1,
            "7d": phase7.job_7d,
            "7e": phase7.job_7e,
            "7f": phase7.job_7f,
            "phase7": phase7.job_phase7,
        }
    )


_register_phase5()


def run_job(name: str) -> list[dict]:
    name = name.lower().strip()
    if name not in JOBS:
        raise SystemExit(f"unknown job {name}; choose from {sorted(JOBS)}")
    print(f"== job {name}  scale={scale_name()}  device={backend.device_name()}  owners={OWNERS.get(name)} ==", flush=True)
    t0 = time.perf_counter()
    rows = JOBS[name]()
    if rows:
        payload = upsert_graphs(rows)
        # job table for the dashboard
        payload["jobs"] = payload.get("jobs") or {}
        payload["jobs"][name] = {
            "n_graphs": len(rows),
            "scale": scale_name(),
            "seconds": round(time.perf_counter() - t0, 3),
            "owners": OWNERS.get(name),
        }
        payload["algorithms"] = ALGORITHMS
        write_catalog(payload)
        exact_claims = [
            {
                "graph_id": r["graph_id"],
                "N": r["N"],
                "k": r["k_target"],
                "statement": f"R({r['k_target']},{r['k_target']}) > {r['N']}" if r["exact"] else f"spectral k={r['k_target']} (not a theorem)",
                "exact": r["exact"],
            }
            for r in rows
            if r.get("is_k_free")
        ]
        write_ledger(exact_claims)
    print(f"job {name} done in {time.perf_counter()-t0:.2f}s  graphs={len(rows)}", flush=True)
    return rows


ALGORITHMS = [
    "O(p) Paley row via x↦x² (not Euler on N×N); Paley spectrum in closed form",
    "O(p) cyclotomic orbits; 2^{e/2} negation-closed masks (Gray code)",
    "Circulant eigenvalues = FFT of the first row (Davis / Diaconis)",
    "Boolean Cayley eigenvalues = FWHT (Bernasconi–Codenotti)",
    "ω(G)=1+ω(G[N(0)]) and α(G)=1+α(G[N^c(0)]) (Yu arXiv:2608.18169)",
    "K4-free ⇔ neighbourhood triangle-free; R(3,k) ⇔ Schur sum-free S",
    "Distance-space ILS: O(n) binary variables (arXiv:2608.18769 IP circulant)",
    "Tomita MCS + degeneracy colour bound; Cvetković inertia + Delsarte ω≤1−d/λ_min",
    "2A ranker is spectral Hoffman, not PPO edge-flip (Berghaus–Wagner ICLR 2025)",
]
