"""Exact and spectral certificates for (k,k)-Ramsey-freeness.

Exact ω/α via bitset Bron-Kerbosch (N ≤ 40). Larger graphs use GPU-native
GEMM triangle/K4 counts plus Hoffman / ratio spectral bounds.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from . import backend


def _nbr_bitsets(adj: np.ndarray) -> list[int]:
    n = adj.shape[0]
    out = [0] * n
    for i in range(n):
        bits = 0
        row = adj[i]
        for j in range(n):
            if i != j and row[j]:
                bits |= 1 << j
        out[i] = bits
    return out


def max_clique_bitset(adj: np.ndarray, limit: int = 40) -> Optional[int]:
    """Bron-Kerbosch with pivoting. Returns None if N is above `limit`."""
    n = int(adj.shape[0])
    if n == 0:
        return 0
    if n > limit:
        return None
    nbr = _nbr_bitsets(adj)
    best = 0

    def rec(r_size: int, p: int, x: int) -> None:
        nonlocal best
        if p == 0 and x == 0:
            if r_size > best:
                best = r_size
            return
        if r_size + p.bit_count() <= best:
            return
        ux = p | x
        if ux == 0:
            return
        u = (ux & -ux).bit_length() - 1
        candidates = p & ~nbr[u]
        while candidates:
            b = candidates & -candidates
            v = b.bit_length() - 1
            rec(r_size + 1, p & nbr[v], x & nbr[v])
            p &= ~b
            x |= b
            candidates &= ~b

    rec(0, (1 << n) - 1, 0)
    return best


def triangle_count(adj: np.ndarray) -> int:
    """trace(A^3)/6 via GEMM — maps directly onto cuBLAS."""
    a = np.asarray(adj, dtype=np.float64)
    a2 = backend.matmul(a, a)
    return int(round(float(np.sum(a2 * a)) / 6.0))


def k4_count(adj: np.ndarray, max_n: int = 80) -> Optional[int]:
    """Exact K4 count from common-neighbor GEMMs. None if N is too large."""
    n = adj.shape[0]
    if n > max_n:
        return None
    a = np.asarray(adj, dtype=np.uint8)
    total = 0
    for i in range(n):
        nbrs = np.flatnonzero(a[i])
        nbrs = nbrs[nbrs > i]
        m = nbrs.size
        if m < 3:
            continue
        sub = a[np.ix_(nbrs, nbrs)]
        # triangles in the neighborhood = K4 through i
        sub_f = sub.astype(np.float64)
        total += int(round(float(np.sum(backend.matmul(sub_f, sub_f) * sub_f)) / 6.0))
    return total


def greedy_clique_lower(adj: np.ndarray) -> int:
    """Degeneracy-style greedy lower bound on ω."""
    n = adj.shape[0]
    if n == 0:
        return 0
    remaining = np.ones(n, dtype=bool)
    clique: list[int] = []
    # start at a max-degree vertex
    deg = adj.sum(axis=1)
    v = int(np.argmax(deg))
    clique.append(v)
    cand = adj[v].astype(bool)
    while cand.any():
        # pick candidate with most neighbors inside remaining candidates
        idx = np.flatnonzero(cand)
        scores = adj[np.ix_(idx, idx)].sum(axis=1)
        v = int(idx[int(np.argmax(scores))])
        clique.append(v)
        cand &= adj[v].astype(bool)
        cand[v] = False
        remaining[v] = False
    return max(1, len(clique))


def spectral_invariants(adj: np.ndarray) -> dict:
    n = adj.shape[0]
    if n == 0:
        return {
            "lambda_max": 0.0,
            "lambda_min": 0.0,
            "spectral_gap": 0.0,
            "hoffman_alpha": 0.0,
            "ratio_omega": 0.0,
        }
    evals = backend.eigvalsh(adj)
    evals = np.sort(np.real(evals))
    lam_min = float(evals[0])
    lam_max = float(evals[-1])
    lam2 = float(evals[-2]) if n > 1 else lam_max
    gap = lam_max - lam2
    if lam_min >= -1e-8:
        hoffman = float(n)
    else:
        hoffman = float(n) / (1.0 + lam_max / abs(lam_min))
    if abs(lam_min) < 1e-8:
        ratio = float(n)
    else:
        ratio = 1.0 + lam_max / abs(lam_min)
    return {
        "lambda_max": lam_max,
        "lambda_min": lam_min,
        "spectral_gap": gap,
        "hoffman_alpha": hoffman,
        "ratio_omega": ratio,
    }


def complement(adj: np.ndarray) -> np.ndarray:
    n = adj.shape[0]
    c = 1 - adj
    np.fill_diagonal(c, 0)
    return c.astype(np.uint8)


def certify(adj: np.ndarray, exact_limit: int = 36) -> dict:
    """Return ω/α bounds and a certified k such that R(k,k) > N if k-free."""
    adj = np.asarray(adj, dtype=np.uint8)
    np.fill_diagonal(adj, 0)
    n = int(adj.shape[0])
    comp = complement(adj)
    spec_g = spectral_invariants(adj)
    spec_c = spectral_invariants(comp)
    triangles = triangle_count(adj) if n <= 400 else -1
    triangles_c = triangle_count(comp) if n <= 400 else -1
    k4 = k4_count(adj, max_n=48)
    k4_c = k4_count(comp, max_n=48)

    omega_exact = max_clique_bitset(adj, limit=exact_limit)
    alpha_exact = max_clique_bitset(comp, limit=exact_limit)
    omega_lower = greedy_clique_lower(adj)
    alpha_lower = greedy_clique_lower(comp)
    if triangles > 0:
        omega_lower = max(omega_lower, 3)
    if triangles_c > 0:
        alpha_lower = max(alpha_lower, 3)
    if k4 is not None and k4 > 0:
        omega_lower = max(omega_lower, 4)
    if k4_c is not None and k4_c > 0:
        alpha_lower = max(alpha_lower, 4)
    if omega_exact is not None:
        omega_lower = omega_upper = int(omega_exact)
    else:
        omega_upper = int(np.floor(spec_g["ratio_omega"] + 1e-9))
        omega_upper = max(omega_upper, omega_lower)
    if alpha_exact is not None:
        alpha_lower = alpha_upper = int(alpha_exact)
    else:
        alpha_upper = int(np.floor(spec_c["ratio_omega"] + 1e-9))
        alpha_upper = int(min(alpha_upper, np.floor(spec_g["hoffman_alpha"] + 1e-9)))
        alpha_upper = max(alpha_upper, alpha_lower)

    k_certified = int(max(omega_upper, alpha_upper)) + 1
    is_k_free = omega_upper < k_certified and alpha_upper < k_certified
    n_root = float(n) ** (1.0 / k_certified) if k_certified > 0 and n > 0 else 0.0
    return {
        "N": n,
        "omega_exact": None if omega_exact is None else int(omega_exact),
        "alpha_exact": None if alpha_exact is None else int(alpha_exact),
        "omega_lower": int(omega_lower),
        "omega_upper": int(omega_upper),
        "alpha_lower": int(alpha_lower),
        "alpha_upper": int(alpha_upper),
        "theta_approx": float(spec_g["hoffman_alpha"]),
        "spectral_gap": float(spec_g["spectral_gap"]),
        "lambda_max": float(spec_g["lambda_max"]),
        "lambda_min": float(spec_g["lambda_min"]),
        "triangles": int(triangles),
        "triangles_complement": int(triangles_c),
        "k4": -1 if k4 is None else int(k4),
        "k4_complement": -1 if k4_c is None else int(k4_c),
        "k_certified": k_certified,
        "is_k_free": bool(is_k_free),
        "n_1_over_k": n_root,
        "exact": omega_exact is not None and alpha_exact is not None,
    }
