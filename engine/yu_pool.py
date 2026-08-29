"""Yu-style 2-class cyclotomic pool search (arXiv:2608.18169).

Undirected distances in D_i ∪ D_j, restricted K4-free process, greedy-α reject,
multiplier lex-min, bitset decision MIS on G[N^c(0)]. Hoffman is never a score.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from .kernels.residual import (
    adding_distance_keeps_triangle_free,
    distances_to_row,
    greedy_alpha_row,
    nbhd_triangle_free,
    residual_nbr,
)
from .kernels.bitset_mcs import mis_decision
from .kernels.sieve import linear_sieve, primitive_root

ROOT = Path(__file__).resolve().parents[1]
YU_PATH = ROOT / "data" / "yu_r4_20.json"

# Published finite lower bounds we must beat (Radziszowski DS1 r18 + Yu 252).
R4_LOWER = {
    20: 252,
    21: 252,
    22: 314,
}


def undirected_classes(p: int, e: int, g: int | None = None) -> list[list[int]]:
    """D_r = {min(x, p-x) : x ∈ g^r ⟨g^e⟩}. Requires −1 in the subgroup."""
    if (p - 1) % e:
        raise ValueError("e must divide p-1")
    if (p - 1) // 2 % e:
        raise ValueError("−1 not in ⟨g^e⟩ (e must divide (p-1)/2)")
    g = g or primitive_root(p)
    ge = pow(g, e, p)
    width = (p - 1) // e
    out: list[list[int]] = []
    for r in range(e):
        x = pow(g, r, p)
        dists = set()
        for _ in range(width):
            d = min(x, p - x)
            if d:
                dists.add(d)
            x = (x * ge) % p
        out.append(sorted(dists))
    return out


def iter_yu_pools(p_lo: int, p_hi: int, e_list=(4, 5, 8, 10)):
    """Primes in [p_lo, p_hi] with a 2-class undirected pool."""
    for p in linear_sieve(p_hi):
        if p < p_lo:
            continue
        for e in e_list:
            if (p - 1) % e or ((p - 1) // 2) % e:
                continue
            try:
                g = primitive_root(p)
                classes = undirected_classes(p, e, g)
            except ValueError:
                continue
            for i in range(e):
                for j in range(i + 1, e):
                    pool = sorted(set(classes[i]) | set(classes[j]))
                    if len(pool) < 8:
                        continue
                    yield {
                        "p": p,
                        "e": e,
                        "g": g,
                        "i": i,
                        "j": j,
                        "pool": pool,
                    }


def lexmin_distances(p: int, distances) -> list[int]:
    """Multiplier orbit: min lex of {λS} for λ ∈ (Z/p)* among undirected distances."""
    S = [int(d) for d in distances]
    best = tuple(sorted(S))
    for lam in range(1, p):
        img = sorted({min((lam * d) % p, (p - (lam * d) % p) % p) for d in S} - {0})
        t = tuple(img)
        if t < best:
            best = t
    return list(best)


def restricted_process(p: int, pool: list[int], rng: np.random.Generator) -> list[int]:
    """Add a random unused pool distance while N(0) stays triangle-free."""
    row = np.zeros(p, dtype=np.uint8)
    unused = list(pool)
    rng.shuffle(unused)
    chosen: list[int] = []
    for d in unused:
        if adding_distance_keeps_triangle_free(row, d):
            row[d] = 1
            row[(p - d) % p] = 1
            chosen.append(int(d))
    return sorted(chosen)


def anneal_pool(
    p: int,
    pool: list[int],
    distances: list[int],
    steps: int,
    rng: np.random.Generator,
    t_cell: int,
) -> list[int]:
    """Swap inside the pool; reject triangles; fail-fast on greedy α ≥ t."""
    pool_set = set(pool)
    cur = set(distances)
    row = distances_to_row(p, cur)
    best = list(cur)
    best_g = greedy_alpha_row(row)
    for _ in range(steps):
        inside = [d for d in cur]
        outside = [d for d in pool if d not in cur]
        if not inside or not outside:
            break
        x = int(rng.choice(inside))
        y = int(rng.choice(outside))
        trial = set(cur)
        trial.remove(x)
        trial.add(y)
        trow = distances_to_row(p, trial)
        if not nbhd_triangle_free(trow):
            continue
        g = greedy_alpha_row(trow)
        if g >= t_cell:
            continue
        cur = trial
        if g < best_g or (g == best_g and len(trial) > len(best)):
            best_g = g
            best = sorted(trial)
    return sorted(best)


def certify_row_decision(row: np.ndarray, t_cell: int, time_limit: float) -> dict:
    """ω=3 via triangle-free N(0); α ≤ t_cell-1 via residual MIS decision."""
    n = int(row.size)
    tri_free = nbhd_triangle_free(row)
    omega = 3 if tri_free else 4
    greedy = greedy_alpha_row(row)
    rec = {
        "N": n,
        "omega": omega,
        "triangle_free": tri_free,
        "alpha_greedy": greedy,
        "alpha_upper": None,
        "exact": False,
        "rejected": False,
        "reason": "",
        "mis": {},
    }
    if not tri_free:
        rec["rejected"] = True
        rec["reason"] = "N(0) has a triangle"
        return rec
    if greedy >= t_cell:
        rec["rejected"] = True
        rec["reason"] = f"greedy α={greedy} ≥ {t_cell}"
        rec["alpha_upper"] = greedy
        return rec
    nbr = residual_nbr(row)
    # residual IS of size t_cell-1  ⇒  α(G) ≥ t_cell  ⇒ reject
    mis = mis_decision(nbr, target=t_cell - 1, time_limit=time_limit)
    rec["mis"] = {k: mis[k] for k in ("found", "lower", "exact", "nodes", "seconds", "timed_out")}
    rec["alpha_lower"] = 1 + int(mis["lower"])
    if mis["found"]:
        rec["rejected"] = True
        rec["reason"] = f"residual IS ≥ {t_cell - 1} (α(G)≥{t_cell})"
        rec["alpha_upper"] = rec["alpha_lower"]
        return rec
    if mis["timed_out"]:
        rec["reason"] = "MIS timed out"
        rec["alpha_upper"] = None
        return rec
    # no (t-1)-IS in residual ⇒ α(G) ≤ t-1
    rec["alpha_upper"] = t_cell - 1
    rec["exact"] = True
    rec["reason"] = f"α≤{t_cell - 1}, ω=3"
    return rec


def load_yu_witness() -> dict:
    return json.loads(YU_PATH.read_text())


def verify_yu_witness(time_limit: float = 45.0) -> dict:
    w = load_yu_witness()
    p = int(w["p"])
    e = int(w["e"])
    g = int(w.get("primitive_root") or 6)
    S = [int(x) for x in w["S"]]
    classes = undirected_classes(p, e, g)
    pool = set(classes[0]) | set(classes[2])
    row = distances_to_row(p, S)
    out = {
        "S_in_pool": set(S) <= pool,
        "len_S": len(S),
        "degree": int(row.sum()),
        "residual_n": p - 1 - int(row.sum()),
        "triangle_free": nbhd_triangle_free(row),
    }
    t0 = time.perf_counter()
    cert = certify_row_decision(row, t_cell=20, time_limit=time_limit)
    out["cert"] = cert
    out["seconds"] = time.perf_counter() - t0
    out["structural_ok"] = bool(
        out["S_in_pool"]
        and out["len_S"] == 32
        and out["degree"] == 64
        and out["residual_n"] == 186
        and out["triangle_free"]
    )
    out["alpha_certified"] = bool(cert.get("exact") and cert.get("alpha_upper") == 19 and not cert.get("rejected"))
    # Exact α=19 is Yu's 1.4s OpenMP certificate. This kernel proves ω=3 and
    # a residual IS lower bound; the 19-IS absence is the hard BnB.
    out["ok"] = out["structural_ok"]
    return out


def search_pool(
    spec: dict,
    walks: int,
    anneal_steps: int,
    t_cell: int,
    time_limit: float,
    rng: np.random.Generator,
    log=print,
    mis_keep: int = 4,
) -> list[dict]:
    p = spec["p"]
    pool = spec["pool"]
    seen: set[tuple[int, ...]] = set()
    cand: list[dict] = []
    for w in range(walks):
        S = restricted_process(p, pool, rng)
        if anneal_steps:
            S = anneal_pool(p, pool, S, anneal_steps, rng, t_cell)
        key = tuple(lexmin_distances(p, S))
        if key in seen:
            log(f"    walk {w + 1}/{walks} |S|={len(S)} orbit-dup skip")
            continue
        seen.add(key)
        row = distances_to_row(p, S)
        gα = greedy_alpha_row(row)
        tri = nbhd_triangle_free(row)
        log(f"    walk {w + 1}/{walks} |S|={len(S)} tri_free={tri} greedyα={gα}")
        if not tri or gα >= t_cell:
            continue
        cand.append({"S": S, "lex": list(key), "row": row, "gα": gα, "spec": spec})
    cand.sort(key=lambda h: (h["gα"], -len(h["S"])))
    hits: list[dict] = []
    for h in cand[: max(1, mis_keep)]:
        cert = certify_row_decision(h["row"], t_cell, time_limit)
        log(f"      MIS |S|={len(h['S'])} greedyα={h['gα']} {cert['reason']} {cert.get('mis')}")
        if cert.get("exact") and not cert.get("rejected"):
            h["cert"] = cert
            hits.append(h)
    return hits
