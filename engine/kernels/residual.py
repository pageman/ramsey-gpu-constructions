"""Circulant residual from the first row: O(n) memory, no dense (p/2)×(p/2)."""

from __future__ import annotations

import numpy as np


def distances_to_row(p: int, distances) -> np.ndarray:
    """Undirected circulant row: edge iff circular distance is in `distances`."""
    row = np.zeros(p, dtype=np.uint8)
    for d in distances:
        d = int(d) % p
        if d == 0:
            continue
        row[d] = 1
        row[(p - d) % p] = 1
    row[0] = 0
    return row


def nbhd_triangle_free(row: np.ndarray) -> bool:
    """G[N(0)] triangle-free ⇔ circulant is K4-free. O(|S|³) bit tests."""
    S = [int(x) for x in np.flatnonzero(row)]
    n = int(row.size)
    if len(S) < 3:
        return True
    for i, a in enumerate(S):
        for j in range(i + 1, len(S)):
            b = S[j]
            if row[(b - a) % n] == 0:
                continue
            for k in range(j + 1, len(S)):
                c = S[k]
                if row[(c - a) % n] and row[(c - b) % n]:
                    return False
    return True


def adding_distance_keeps_triangle_free(row: np.ndarray, d: int) -> bool:
    """Would G[N(0)] stay triangle-free after adding ±d?"""
    n = int(row.size)
    d = int(d) % n
    if d == 0 or row[d]:
        return True
    trial = row.copy()
    trial[d] = 1
    trial[(n - d) % n] = 1
    return nbhd_triangle_free(trial)


def residual_nbr(row: np.ndarray) -> list[int]:
    """Neighbour bitsets of G[N^c(0)]. Vertex list = nonzero non-neighbours of 0."""
    n = int(row.size)
    verts = [i for i in range(1, n) if row[i] == 0]
    idx = {v: k for k, v in enumerate(verts)}
    m = len(verts)
    nbr = [0] * m
    for k, u in enumerate(verts):
        bits = 0
        for v in verts:
            if v == u:
                continue
            if row[(v - u) % n]:
                bits |= 1 << idx[v]
        nbr[k] = bits
    return nbr


def greedy_alpha_row(row: np.ndarray) -> int:
    """1 + greedy α(G[N^c(0)]). A witness ≥ t rejects R(4,t) / R(3,t)."""
    from .bitset_mcs import greedy_mis

    nbr = residual_nbr(row)
    return 1 + greedy_mis(nbr)
