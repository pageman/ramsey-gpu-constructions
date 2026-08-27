"""Word-RAM maximum clique: degeneracy order, Tomita pivot, greedy colour bound.

n ≤ 64 uses Python ints; n ≤ 512 uses uint64 limbs (CP-style bitset, BBMC/Prosser).
Vertex-transitive graphs reduce ω(G) = 1 + ω(G[N(0)]) (standard Cayley trick;
used for R(4,20)≥252 on a 64-vertex neighbourhood).
"""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from ..bits import bitwise_count


def _limbs(n: int) -> int:
    return (n + 63) // 64


def pack_neighbours(adj: np.ndarray) -> np.ndarray:
    """nbr[i, w] = 64-bit word w of N(i). Shape (n, L)."""
    n = int(adj.shape[0])
    L = _limbs(n)
    nbr = np.zeros((n, L), dtype=np.uint64)
    a = np.asarray(adj, dtype=np.uint8)
    for i in range(n):
        js = np.flatnonzero(a[i])
        for j in js:
            if i == j:
                continue
            nbr[i, j >> 6] |= np.uint64(1) << np.uint64(j & 63)
    return nbr


def popcnt_words(w: np.ndarray) -> int:
    return int(bitwise_count(w).sum())


def degeneracy_order(adj: np.ndarray) -> np.ndarray:
    """Core decomposition / Batagelj–Zaversnik O(n+m). Smallest-last order."""
    n = int(adj.shape[0])
    if n == 0:
        return np.zeros(0, dtype=np.int32)
    deg = adj.sum(axis=1).astype(np.int32)
    remaining = np.ones(n, dtype=bool)
    order = np.empty(n, dtype=np.int32)
    for k in range(n):
        live = np.flatnonzero(remaining)
        v = int(live[int(np.argmin(deg[live]))])
        order[n - 1 - k] = v  # smallest-last: low-core vertices last
        remaining[v] = False
        nbrs = np.flatnonzero(adj[v])
        deg[nbrs] -= 1
        deg[v] = n + 1
    return order


def greedy_colour_bound(adj: np.ndarray, verts: np.ndarray) -> int:
    """Number of colours used on induced subgraph — upper bound on ω."""
    if verts.size == 0:
        return 0
    sub = adj[np.ix_(verts, verts)]
    order = np.argsort(-sub.sum(axis=1))
    colour = np.full(verts.size, -1, dtype=np.int32)
    used = 0
    for u in order:
        neigh_cols = colour[np.flatnonzero(sub[u]) ]
        blocked = set(int(c) for c in neigh_cols if c >= 0)
        c = 0
        while c in blocked:
            c += 1
        colour[u] = c
        used = max(used, c + 1)
    return int(used)


def _mcs_small(adj: np.ndarray, time_limit: float) -> tuple[int, bool]:
    n = int(adj.shape[0])
    nbr = [0] * n
    a = np.asarray(adj, dtype=np.uint8)
    for i in range(n):
        bits = 0
        for j in range(n):
            if i != j and a[i, j]:
                bits |= 1 << j
        nbr[i] = bits
    best = 0
    t0 = time.perf_counter()
    timed_out = False

    def rec(r_size: int, p: int, x: int) -> None:
        nonlocal best, timed_out
        if timed_out:
            return
        if time.perf_counter() - t0 > time_limit:
            timed_out = True
            return
        if p == 0:
            if x == 0 and r_size > best:
                best = r_size
            return
        if r_size + p.bit_count() <= best:
            return
        ux = p | x
        # Tomita pivot: vertex in P∪X of max |P ∩ N(u)|
        u, best_deg = 0, -1
        tmp = ux
        while tmp:
            b = tmp & -tmp
            v = b.bit_length() - 1
            d = (p & nbr[v]).bit_count()
            if d > best_deg:
                best_deg, u = d, v
            tmp ^= b
        candidates = p & ~nbr[u]
        while candidates:
            b = candidates & -candidates
            v = b.bit_length() - 1
            rec(r_size + 1, p & nbr[v], x & nbr[v])
            p &= ~b
            x |= b
            candidates &= ~b

    rec(0, (1 << n) - 1 if n else 0, 0)
    return best, not timed_out


def max_clique(adj: np.ndarray, time_limit: float = 1.5) -> dict:
    """Return {lower, upper, exact}. upper from greedy colouring if MCS times out."""
    adj = np.asarray(adj, dtype=np.uint8)
    np.fill_diagonal(adj, 0)
    n = int(adj.shape[0])
    if n == 0:
        return {"lower": 0, "upper": 0, "exact": True}
    colour_ub = greedy_colour_bound(adj, np.arange(n))
    if n <= 64:
        low, exact = _mcs_small(adj, time_limit)
        return {"lower": low, "upper": low if exact else max(low, colour_ub), "exact": exact}
    # degeneracy greedy lower bound
    order = degeneracy_order(adj)
    # try MCS on the core: vertices of highest remaining degree
    deg = adj.sum(axis=1)
    core_idx = np.argsort(-deg)[: min(n, 64)]
    sub = adj[np.ix_(core_idx, core_idx)]
    low_core, exact_core = _mcs_small(sub, time_limit * 0.5)
    # greedy
    remaining = np.ones(n, dtype=bool)
    v0 = int(np.argmax(deg))
    clique = [v0]
    cand = adj[v0].astype(bool)
    while cand.any():
        idx = np.flatnonzero(cand)
        scores = adj[np.ix_(idx, idx)].sum(axis=1)
        v = int(idx[int(np.argmax(scores))])
        clique.append(v)
        cand &= adj[v].astype(bool)
        cand[v] = False
    low = max(low_core, len(clique))
    return {
        "lower": int(low),
        "upper": int(colour_ub),
        "exact": bool(exact_core and colour_ub == low and n <= 64),
    }


def omega_vertex_transitive(adj: np.ndarray, time_limit: float = 1.5) -> dict:
    """ω(G) = 1 + ω(G[N(0)]) for vertex-transitive G. Cuts n to degree d."""
    adj = np.asarray(adj, dtype=np.uint8)
    np.fill_diagonal(adj, 0)
    nbrs = np.flatnonzero(adj[0])
    if nbrs.size == 0:
        return {"lower": 1, "upper": 1, "exact": True, "reduced_n": 0}
    sub = adj[np.ix_(nbrs, nbrs)]
    inner = max_clique(sub, time_limit=time_limit)
    return {
        "lower": inner["lower"] + 1,
        "upper": inner["upper"] + 1,
        "exact": inner["exact"],
        "reduced_n": int(nbrs.size),
    }


def is_circulant(adj: np.ndarray) -> bool:
    n = adj.shape[0]
    row0 = adj[0]
    for i in range(1, min(n, 8)):  # sample; full check if samples pass
        if not np.array_equal(adj[i], np.roll(row0, i)):
            return False
    if n > 8:
        i = n // 2
        if not np.array_equal(adj[i], np.roll(row0, i)):
            return False
    return True


def is_f2_cayley(adj: np.ndarray) -> bool:
    n = adj.shape[0]
    if n == 0 or n & (n - 1):
        return False
    # adj[i,j] == adj[0, i xor j]
    row0 = adj[0]
    idx = np.arange(n)
    for i in (1, n // 3 if n > 3 else 1, n - 1):
        if not np.array_equal(adj[i], row0[i ^ idx]):
            return False
    return True
