"""7c.1: SAT on a Yu pool with lazy leftover-IS cuts (CEGIS).

Per round, pack |S| (search bias; empty S never reaches the referee).
When N(0) has a triangle, cut that triangle's supporting distances.
When c-decide finds a leftover independent set I, cut so S must hit I.
Timeout ≠ cut ≠ accept. Do not encode “no 16-IS” up front.
"""

from __future__ import annotations

import time

import numpy as np

from .kernels.bitset_mcs import greedy_mis_set


def undirected_dist(p: int, x: int) -> int:
    """Circular distance in 1..⌊p/2⌋, or 0."""
    x %= p
    if x == 0:
        return 0
    return min(x, p - x)


def residual_vertices(row) -> list[int]:
    """Z/p vertices of G[N^c(0)] in the same order as residual_nbr."""
    n = int(row.size)
    return [i for i in range(1, n) if int(row[i]) == 0]


def extract_is_local(nbr: list[int], target: int, seconds: float = 2.0) -> list[int] | None:
    """Residual-local indices of an IS of size ≥ target, or None.

    Prefer greedy (if it already hits the target). Else CP-SAT. The native
    decision kernel does not return a witness; we must reconstruct one before
    cutting. If this returns None after found=True, do not invent a cut.
    """
    if target <= 0:
        return []
    greedy = greedy_mis_set(nbr)
    if len(greedy) >= target:
        return greedy
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return None
    n = len(nbr)
    if n == 0:
        return None
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"v{i}") for i in range(n)]
    for u in range(n):
        nu = int(nbr[u])
        for v in range(u + 1, n):
            if (nu >> v) & 1:
                model.Add(xs[u] + xs[v] <= 1)
    model.Add(sum(xs) >= int(target))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = 4
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return [i for i, x in enumerate(xs) if solver.Value(x)]


def local_is_to_zp(row, local: list[int]) -> list[int]:
    verts = residual_vertices(row)
    out = []
    for k in local:
        if 0 <= int(k) < len(verts):
            out.append(int(verts[int(k)]))
    return sorted(set(out))


def is_cut_pool_lits(p: int, pool_idx: dict[int, int], I: list[int]) -> list[int]:
    """Pool-variable indices that hit residual IS I ⊂ Z/p.

    Hitting means: put a vertex of I into N(0), or put a pairwise difference
    into S. Both are undirected distances, so only pool members become lits.
    An empty list means this pool cannot kill I — the model should become
    unsat (the pool is dead for this t).
    """
    lits: set[int] = set()
    for i in I:
        d = undirected_dist(p, int(i))
        if d in pool_idx:
            lits.add(pool_idx[d])
    for a in range(len(I)):
        ua = int(I[a])
        for b in range(a + 1, len(I)):
            d = undirected_dist(p, int(I[b]) - ua)
            if d in pool_idx:
                lits.add(pool_idx[d])
    return sorted(lits)


def assignment_nogood(xs: list, pool: list[int], idx: dict[int, int], S: list[int]):
    """Constraint: not this exact 0/1 vector on the pool."""
    chosen = set(int(d) for d in S)
    terms = []
    for d in pool:
        var = xs[idx[d]]
        if d in chosen:
            terms.append(1 - var)
        else:
            terms.append(var)
    return sum(terms) >= 1


def build_triangle_free_model(spec: dict):
    """Same N(0) triangle-free clauses as 7c. No max-|S| objective."""
    from itertools import combinations

    from ortools.sat.python import cp_model

    from .kernels.residual import distances_to_row, nbhd_triangle_free

    pool = list(spec["pool"])
    p = int(spec["p"])
    idx = {d: i for i, d in enumerate(pool)}
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"d{d}") for d in pool]
    for k in (1, 2, 3):
        for subset in combinations(pool, k):
            row = distances_to_row(p, subset)
            if not nbhd_triangle_free(row):
                model.Add(sum(xs[idx[d]] for d in subset) <= k - 1)
    # Residual width: p-1-2|S| ≤ 256  ⇒  |S| ≥ ceil((p-1-256)/2)
    need = (p - 1 - 256 + 1) // 2
    if need > 0:
        model.Add(sum(xs) >= need)
    # Packing is a *search bias*, not the night's objective. Empty S is
    # triangle-free and would never reach the leftover referee (greedy α = p).
    # 7c stopped after one Maximize. 7c1 Maximize's again after each IS-cut.
    model.Maximize(sum(xs))
    return model, xs, idx, pool


def solve_pool_model(model, xs, pool, seconds: float, seed: int = 0) -> tuple[str, list[int] | None, float]:
    from ortools.sat.python import cp_model

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = int(__import__("os").environ.get("RAMSEY_SAT_WORKERS", "8"))
    solver.parameters.random_seed = int(seed) & 0x7FFFFFFF
    t0 = time.perf_counter()
    status = solver.Solve(model)
    dt = time.perf_counter() - t0
    names = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    label = names.get(status, str(status))
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return label, None, dt
    S = sorted(int(d) for d, x in zip(pool, xs) if solver.Value(x))
    return label, S, dt


def first_triangle_support_dists(row) -> list[int] | None:
    """Undirected distances that witness one triangle in N(0), or None.

    7c’s 1-/2-/3-subset forbids are necessary but not sufficient for a large
    S: a 37-set can contain a triangle even when no 3-subset does as a
    standalone connection set. CEGIS adds this as a cut, not a ‘bug’.
    """
    n = int(row.size)
    verts = [int(x) for x in np.flatnonzero(row)]
    for i, a in enumerate(verts):
        for j in range(i + 1, len(verts)):
            b = verts[j]
            if int(row[(b - a) % n]) == 0:
                continue
            for k in range(j + 1, len(verts)):
                c = verts[k]
                if int(row[(c - a) % n]) and int(row[(c - b) % n]):
                    dists = {
                        undirected_dist(n, a),
                        undirected_dist(n, b),
                        undirected_dist(n, c),
                        undirected_dist(n, b - a),
                        undirected_dist(n, c - a),
                        undirected_dist(n, c - b),
                    }
                    return sorted(d for d in dists if d)
    return None


def verify_is_independent(row, I: list[int]) -> bool:
    """True iff I ⊆ N^c(0) and no S-edge between members."""
    n = int(row.size)
    for v in I:
        if not (1 <= int(v) < n) or int(row[int(v)]) != 0:
            return False
    for a in range(len(I)):
        for b in range(a + 1, len(I)):
            if int(row[(int(I[b]) - int(I[a])) % n]):
                return False
    return True


def cut_kills_this_s(pool: list[int], S: list[int], lits: list[int], idx: dict[int, int]) -> bool:
    """Every cut literal is false under S (so the clause excludes this S)."""
    chosen = set(int(d) for d in S)
    inv = {i: d for d, i in idx.items()}
    return all(inv[i] not in chosen for i in lits)
