"""Distance-space circulant search: O(n) decision variables, O(n log n) scores.

Flipping a residue d ∈ S updates the triangle count by a cyclic convolution
slice (CP FFT trick). K_r-freeness of a vertex-transitive graph reduces to the
neighbourhood of 0 (MathOverflow / Yu 2026 R(4,20) circulant certificate).
Integer-programming circulant models (arXiv:2608.18769) use the same projection.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

from .spectrum import convolution_bool, fft_eigenvalues, spectral_bounds_from_eigs, triangle_count_circulant


def closed_S(n: int, S: Iterable[int]) -> np.ndarray:
    """Undirected Cayley: S = −S, 0 ∉ S. Stored as a 0/1 row of length n."""
    row = np.zeros(n, dtype=np.uint8)
    for d in S:
        d = int(d) % n
        if d == 0:
            continue
        row[d] = 1
        row[(n - d) % n] = 1
    row[0] = 0
    return row


def adj_from_row(row: np.ndarray) -> np.ndarray:
    n = row.size
    return np.stack([np.roll(row, i) for i in range(n)]).astype(np.uint8)


def bits_from_row(row: np.ndarray) -> np.ndarray:
    """Pack unique distances 1..⌊n/2⌋ into a 0/1 vector of length ⌊n/2⌋."""
    n = int(row.size)
    half = n // 2
    bits = np.zeros(half, dtype=np.uint8)
    for d in range(1, half):
        bits[d] = 1 if row[d] else 0
    if n % 2 == 0 and half < n:
        bits[0] = 1 if row[half] else 0  # slot 0 stores the diameter n/2
    return bits


def row_from_bits(n: int, bits: np.ndarray) -> np.ndarray:
    half = n // 2
    S = []
    for i in range(1, half):
        if bits[i]:
            S.append(i)
    if n % 2 == 0 and bits[0]:
        S.append(half)
    return closed_S(n, S)


def k4_free_via_neighbourhood(row: np.ndarray) -> bool:
    """Circulant is K4-free iff N(0) is triangle-free. O(d^2) with d=|S|."""
    S = np.flatnonzero(row)
    if S.size < 3:
        return True
    n = row.size
    d = S.size
    for a in range(d):
        for b in range(a + 1, d):
            if row[(int(S[b]) - int(S[a])) % n] == 0:
                continue
            for c in range(b + 1, d):
                if row[(int(S[c]) - int(S[a])) % n] and row[(int(S[c]) - int(S[b])) % n]:
                    return False
    return True


def triangle_free_circulant(row: np.ndarray) -> bool:
    """S+S misses S: no 3-term Schur triple. O(n log n) convolution."""
    conv = convolution_bool(row, row)
    # ignore the 2·S diagonal contribution at 2s when 2s happens to land in S
    # for undirected Cayley a triangle is x,y,x+y all in S (x,y,x+y ≠ 0)
    return not np.any((conv > 0.5) & (row > 0.5))


def schur_sum_free(row: np.ndarray) -> bool:
    """Same as triangle-free for undirected Cayley on Z/nZ."""
    return triangle_free_circulant(row)


def incremental_triangle_delta(row: np.ndarray, d: int) -> float:
    """Change in common-neighbour count at 0 if residue d is flipped. O(n)."""
    n = row.size
    d %= n
    if d == 0:
        return 0.0
    rolled = np.roll(row, d)
    common = float(np.dot(row.astype(np.float64), rolled.astype(np.float64)))
    adding = row[d] == 0
    return common if adding else -common


def _score_row(row: np.ndarray, k_clique: int, forbid_triangles: bool) -> float:
    if forbid_triangles and not triangle_free_circulant(row):
        return 1e9
    if k_clique >= 4 and not k4_free_via_neighbourhood(row):
        return 1e9
    eigs = fft_eigenvalues(row.astype(np.float64))
    b = spectral_bounds_from_eigs(eigs, row.size)
    crow = 1.0 - row.astype(np.float64)
    crow[0] = 0.0
    cb = spectral_bounds_from_eigs(fft_eigenvalues(crow), row.size)
    # smaller max(Hoffman α of G, Hoffman α of Ḡ) is a better Ramsey seed
    return float(max(b["hoffman_alpha"], cb["hoffman_alpha"]))


def ils_connection_set(
    n: int,
    k_clique: int,
    steps: int = 200,
    rng: np.random.Generator | None = None,
    forbid_triangles: bool = False,
    seed_row: np.ndarray | None = None,
    mask: np.ndarray | None = None,
) -> dict:
    """Iterated local search in distance space (Exoo / 2026 IP circulant).

    State is ⌊n/2⌋ unique distances. Optional `mask` freezes residues outside
    a cyclotomic union (Yu 2026: search inside D0 ∪ D2). Cooling is DSC-3 style.
    """
    rng = rng or np.random.default_rng(0)
    half = n // 2
    if seed_row is not None:
        bits = bits_from_row(np.asarray(seed_row, dtype=np.uint8))
    else:
        bits = rng.integers(0, 2, size=half, dtype=np.uint8)
        bits[0] = 0 if n % 2 else bits[0]
    free = np.ones(half, dtype=bool)
    if mask is not None:
        allowed = bits_from_row(np.asarray(mask, dtype=np.uint8))
        free = allowed.astype(bool)
        bits = bits & allowed
        if not free.any():
            free[:] = True

    row = row_from_bits(n, bits)
    best_bits = bits.copy()
    best_row = row
    best = _score_row(row, k_clique, forbid_triangles)
    cur = best
    idxs = np.flatnonzero(free)
    if idxs.size == 0:
        idxs = np.arange(half)
    for t in range(steps):
        i = int(rng.choice(idxs))
        bits[i] ^= 1
        row = row_from_bits(n, bits)
        sc = _score_row(row, k_clique, forbid_triangles)
        T = 0.4 * (1.0 - t / max(steps, 1)) + 0.02
        if sc <= cur or rng.random() < np.exp(-(sc - cur) / max(T, 1e-6)):
            cur = sc
            if sc < best:
                best, best_bits, best_row = sc, bits.copy(), row
        else:
            bits[i] ^= 1
    return {
        "n": n,
        "score": best,
        "row": best_row,
        "S": np.flatnonzero(best_row).tolist(),
        "triangles": triangle_count_circulant(best_row.astype(np.float64)),
        "k4_free": k4_free_via_neighbourhood(best_row),
        "triangle_free": triangle_free_circulant(best_row),
    }


def two_block_adj(s0: np.ndarray, s1: np.ndarray) -> np.ndarray:
    """Undirected 2-block circulant on 2m vertices. O(m) parameters.

    Blocks: circ(s0) on each copy, circ(s1) between copies. s0, s1 length m,
    closed under inversion.
    """
    m = int(s0.size)
    n = 2 * m
    A = np.zeros((n, n), dtype=np.uint8)
    r0 = closed_S(m, np.flatnonzero(s0))
    r1 = closed_S(m, np.flatnonzero(s1))
    for i in range(m):
        A[i, :m] = np.roll(r0, i)
        A[i, m:] = np.roll(r1, i)
        A[i + m, m:] = np.roll(r0, i)
        A[i + m, :m] = np.roll(r1, i)
    np.fill_diagonal(A, 0)
    return A


def ils_two_block(
    m: int,
    steps: int = 200,
    rng: np.random.Generator | None = None,
    seed_s0: np.ndarray | None = None,
    seed_s1: np.ndarray | None = None,
    k_clique: int = 5,
) -> dict:
    rng = rng or np.random.default_rng(1)
    if seed_s0 is None:
        s0 = rng.integers(0, 2, size=m, dtype=np.uint8)
    else:
        s0 = np.asarray(seed_s0, dtype=np.uint8).copy()
    if seed_s1 is None:
        s1 = rng.integers(0, 2, size=m, dtype=np.uint8)
    else:
        s1 = np.asarray(seed_s1, dtype=np.uint8).copy()
    s0[0] = 0
    s1[0] = 0

    def score() -> float:
        A = two_block_adj(s0, s1)
        from ..certify import greedy_clique_lower, triangle_count, complement

        om = greedy_clique_lower(A)
        al = greedy_clique_lower(complement(A))
        if om >= k_clique or al >= k_clique:
            return 1e9
        # cheaper than eigendecomposition inside the ILS loop (CP: evaluate, then certify)
        deg = float(A[0].sum())
        tri = triangle_count(A) if A.shape[0] <= 80 else 0
        return float(max(om, al) * 1000 + deg + tri / 100.0)

    best = score()
    best_s0, best_s1 = s0.copy(), s1.copy()
    cur = best
    for t in range(steps):
        which = int(rng.integers(0, 2))
        i = int(rng.integers(1, m))
        vec = s0 if which == 0 else s1
        vec[i] ^= 1
        vec[(m - i) % m] = vec[i]
        sc = score()
        T = 0.5 * (1.0 - t / max(steps, 1)) + 0.02
        if sc <= cur or rng.random() < np.exp(-(sc - cur) / max(T, 1e-6)):
            cur = sc
            if sc < best:
                best, best_s0, best_s1 = sc, s0.copy(), s1.copy()
        else:
            vec[i] ^= 1
            vec[(m - i) % m] = vec[i]
    A = two_block_adj(best_s0, best_s1)
    return {"n": 2 * m, "score": best, "adj": A, "s0": best_s0, "s1": best_s1}
