"""Certify a Cayley graph from its connection row — O(n) memory, O(n log n) spectrum.

Vertex-transitive identities (Yu arXiv:2608.18169, 2026; standard Cayley):
    ω(G) = 1 + ω(G[N(0)])
    α(G) = 1 + α(G[N^c(0)]) = 1 + ω(Ḡ[N_Ḡ(0)])
K4-free ⇔ N(0) is triangle-free. Circulant triangles are a cyclic convolution.
Boolean Cayley spectra are a Walsh–Hadamard transform (Bernasconi–Codenotti).
Paley graphs of order q have a closed-form spectrum: no eigendecomposition.
"""

from __future__ import annotations

import numpy as np

from .cayley import adj_from_row, k4_free_via_neighbourhood, triangle_free_circulant
from .mcs import max_clique
from .spectrum import (
    boolean_cayley_eigenvalues,
    fft_eigenvalues,
    spectral_bounds_from_eigs,
    triangle_count_circulant,
)


def paley_closed_eigs(q: int) -> np.ndarray:
    """Spectrum of the Paley graph of order q ≡ 1 (mod 4): one d=(q-1)/2 and
    (q-1)/2 copies of each of (−1±√q)/2.
    """
    d = (q - 1) / 2.0
    a = (-1.0 + np.sqrt(q)) / 2.0
    b = (-1.0 - np.sqrt(q)) / 2.0
    return np.concatenate(([d], np.full((q - 1) // 2, a), np.full((q - 1) // 2, b)))


def _induced_from_differences(host_row: np.ndarray, verts: np.ndarray) -> np.ndarray:
    """Induced subgraph of an abelian Cayley graph on a vertex list.

    Circulant: adj[u,v] = row[(verts[v]-verts[u]) mod n].
    """
    n = host_row.size
    d = verts.size
    if d == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    diff = (verts[None, :] - verts[:, None]) % n
    return host_row[diff].astype(np.uint8)


def _induced_f2(f: np.ndarray, verts: np.ndarray) -> np.ndarray:
    if verts.size == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    xor = verts[:, None] ^ verts[None, :]
    sub = f[xor].astype(np.uint8)
    np.fill_diagonal(sub, 0)
    return sub


def _pack_cert(
    n: int,
    om: dict,
    al: dict,
    spec: dict,
    cspec: dict,
    triangles: int,
    symmetry: str,
    kernel: str,
    extra: dict | None = None,
) -> dict:
    omega_lower = int(om["lower"])
    omega_upper = int(
        om["upper"]
        if om["exact"]
        else min(
            om["upper"],
            int(np.floor(spec["delsarte_omega"] + 1e-9)),
            int(np.floor(spec["ratio_omega"] + 1e-9)),
        )
    )
    omega_upper = max(omega_upper, omega_lower)
    alpha_lower = int(al["lower"])
    alpha_upper = int(
        al["upper"]
        if al["exact"]
        else min(
            al["upper"],
            int(np.floor(spec["hoffman_alpha"] + 1e-9)),
            int(spec["inertia_alpha"]),
            int(np.floor(cspec["ratio_omega"] + 1e-9)),
        )
    )
    alpha_upper = max(alpha_upper, alpha_lower)
    exact = bool(om["exact"] and al["exact"])
    if exact:
        omega_upper = omega_lower
        alpha_upper = alpha_lower
    k = max(omega_upper, alpha_upper) + 1
    rec = {
        "N": n,
        "omega_exact": omega_lower if exact else None,
        "alpha_exact": alpha_lower if exact else None,
        "omega_lower": omega_lower,
        "omega_upper": omega_upper,
        "alpha_lower": alpha_lower,
        "alpha_upper": alpha_upper,
        "theta_approx": float(spec["hoffman_alpha"]),
        "delsarte_omega": float(spec["delsarte_omega"]),
        "spectral_gap": float(spec["spectral_gap"]),
        "lambda_max": float(spec["lambda_max"]),
        "lambda_min": float(spec["lambda_min"]),
        "triangles": int(triangles),
        "triangles_complement": -1,
        "k4": -1,
        "k4_complement": -1,
        "k_certified": int(k),
        "is_k_free": True,
        "n_1_over_k": float(n) ** (1.0 / k) if k else 0.0,
        "exact": exact,
        "symmetry": symmetry,
        "kernel": kernel,
        "reduced_n": om.get("reduced_n"),
    }
    if extra:
        rec.update(extra)
    return rec


def certify_circulant_row(row: np.ndarray, time_limit: float = 1.0, paley_q: int | None = None) -> dict:
    row = np.asarray(row, dtype=np.uint8).copy()
    row[0] = 0
    n = int(row.size)
    if paley_q:
        evals = paley_closed_eigs(paley_q)
    else:
        evals = fft_eigenvalues(row.astype(np.float64))
    crow = (1 - row).astype(np.uint8)
    crow[0] = 0
    if paley_q:
        # Paley is self-complementary
        cevals = evals
    else:
        cevals = fft_eigenvalues(crow.astype(np.float64))
    spec = spectral_bounds_from_eigs(evals, n)
    cspec = spectral_bounds_from_eigs(cevals, n)
    S = np.flatnonzero(row)
    Nc = np.array([i for i in range(1, n) if row[i] == 0], dtype=np.int64)
    sub = _induced_from_differences(row, S)
    csub = _induced_from_differences(crow, Nc)
    # residual of Ḡ at 0 is Nc with complement edges = original non-edges among Nc
    om_inner = max_clique(sub, time_limit=time_limit) if sub.shape[0] else {"lower": 0, "upper": 0, "exact": True}
    al_inner = max_clique(csub, time_limit=time_limit * 0.5) if csub.shape[0] else {"lower": 0, "upper": 0, "exact": True}
    om = {
        "lower": om_inner["lower"] + 1,
        "upper": om_inner["upper"] + 1,
        "exact": om_inner["exact"],
        "reduced_n": int(S.size),
    }
    al = {
        "lower": al_inner["lower"] + 1,
        "upper": al_inner["upper"] + 1,
        "exact": al_inner["exact"],
        "reduced_n": int(Nc.size),
    }
    triangles = triangle_count_circulant(row.astype(np.float64))
    extra = {
        "k4_free_nbhd": bool(k4_free_via_neighbourhood(row)),
        "triangle_free": bool(triangle_free_circulant(row)),
        "degree": int(S.size),
    }
    return _pack_cert(n, om, al, spec, cspec, triangles, "circulant", "fft", extra)


def certify_boolean_cayley(f: np.ndarray, time_limit: float = 1.0) -> dict:
    f = np.asarray(f, dtype=np.uint8).copy()
    f[0] = 0
    n = int(f.size)
    evals = boolean_cayley_eigenvalues(f.astype(np.float64))
    cf = (1 - f).astype(np.uint8)
    cf[0] = 0
    cevals = boolean_cayley_eigenvalues(cf.astype(np.float64))
    spec = spectral_bounds_from_eigs(evals, n)
    cspec = spectral_bounds_from_eigs(cevals, n)
    S = np.flatnonzero(f)
    Nc = np.array([i for i in range(1, n) if f[i] == 0], dtype=np.int64)
    sub = _induced_f2(f, S)
    csub = _induced_f2(cf, Nc)
    om_inner = max_clique(sub, time_limit=time_limit) if sub.shape[0] else {"lower": 0, "upper": 0, "exact": True}
    al_inner = max_clique(csub, time_limit=time_limit * 0.5) if csub.shape[0] else {"lower": 0, "upper": 0, "exact": True}
    om = {
        "lower": om_inner["lower"] + 1,
        "upper": om_inner["upper"] + 1,
        "exact": om_inner["exact"],
        "reduced_n": int(S.size),
    }
    al = {
        "lower": al_inner["lower"] + 1,
        "upper": al_inner["upper"] + 1,
        "exact": al_inner["exact"],
        "reduced_n": int(Nc.size),
    }
    return _pack_cert(n, om, al, spec, cspec, -1, "f2_cayley", "fwht", {"degree": int(S.size)})


def materialize_if_small(row: np.ndarray, limit: int = 256) -> np.ndarray | None:
    if row.size <= limit:
        return adj_from_row(row)
    return None
