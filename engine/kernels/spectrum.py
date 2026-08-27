"""O(n log n) spectra for the two Cayley families that dominate this project.

Circulant on Z/nZ: eigenvalues are the DFT of the first row (Davis 1979 / Diaconis).
Boolean Cayley on F_2^n: eigenvalues are the Walsh–Hadamard transform of f
(Bernasconi–Codenotti; Stănică). Both beat O(n^3) Hermitian eigendecomposition.

Delsarte bound for strongly regular graphs: ω ≤ 1 − d/λ_min.
Hoffman / ratio / Cvetković inertia are free once the spectrum is known.
"""

from __future__ import annotations

import numpy as np


def circulant_row_from_S(n: int, S) -> np.ndarray:
    row = np.zeros(n, dtype=np.float64)
    for d in S:
        dd = int(d) % n
        if dd:
            row[dd] = 1.0
    return row


def fft_eigenvalues(row: np.ndarray) -> np.ndarray:
    """Real eigenvalues of a symmetric circulant. O(n log n)."""
    row = np.asarray(row, dtype=np.float64)
    # undirected circulant ⇒ row[k] == row[n-k]; FFT is real up to 1e-12
    return np.real(np.fft.fft(row))


def fwht(a: np.ndarray) -> np.ndarray:
    """In-place-style fast Walsh–Hadamard transform. N must be a power of 2.
    Competitive-programming FWHT (hadamard OR/XOR convolution) with +/−.
    """
    x = np.asarray(a, dtype=np.float64).copy()
    n = x.size
    if n == 0 or n & (n - 1):
        raise ValueError("FWHT length must be a power of 2")
    h = 1
    while h < n:
        x = x.reshape(-1, 2 * h)
        u, v = x[:, :h], x[:, h:]
        x = np.concatenate((u + v, u - v), axis=1)
        h *= 2
    return x.reshape(n)


def boolean_cayley_eigenvalues(f: np.ndarray) -> np.ndarray:
    """Eigenvalues of Cay(F_2^n, {x : f(x)=1}). f[0] should be 0 (loopless)."""
    return fwht(np.asarray(f, dtype=np.float64))


def convolution_bool(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cyclic convolution via FFT. Triangle indicators on Z/nZ are convolutions."""
    n = a.size
    fa = np.fft.rfft(a.astype(np.float64), n=n)
    fb = np.fft.rfft(b.astype(np.float64), n=n)
    return np.fft.irfft(fa * fb, n=n)


def triangle_count_circulant(row: np.ndarray) -> int:
    """Number of triangles in an undirected circulant. O(n log n).

    A 3-cycle through 0 is a pair x,y in S with y-x in S. Vertex-transitivity
    multiplies by n/3 (each triangle counted 3 times at a vertex, 2 directions
    already folded by undirectedness). Equivalently (1/6) n * <row, row*row>
    in cyclic convolution.
    """
    n = row.size
    conv = convolution_bool(row, row)
    # conv[k] = |{x : x in S, k-x in S}|
    local = float(np.dot(row, conv))  # closed wedges at 0, each triangle 2 times
    # n vertices, each triangle seen 3 times as a vertex, 2 as a wedge order
    return int(round(n * local / 6.0))


def spectral_bounds_from_eigs(evals: np.ndarray, n: int | None = None) -> dict:
    evals = np.sort(np.real(np.asarray(evals, dtype=np.float64)))
    n = int(n if n is not None else evals.size)
    lam_min = float(evals[0])
    lam_max = float(evals[-1])
    lam2 = float(evals[-2]) if n > 1 else lam_max
    if lam_min >= -1e-9:
        hoffman = float(n)
        delsarte = float(n)
        ratio = float(n)
    else:
        hoffman = float(n) / (1.0 + lam_max / abs(lam_min))
        delsarte = 1.0 - lam_max / lam_min  # 1 - d/s for regular graphs
        ratio = 1.0 + lam_max / abs(lam_min)
    pos = int(np.sum(evals > 1e-8))
    neg = int(np.sum(evals < -1e-8))
    zero = n - pos - neg
    # Cvetković inertia bound on α
    inertia_alpha = zero + min(pos, neg)
    return {
        "lambda_max": lam_max,
        "lambda_min": lam_min,
        "spectral_gap": lam_max - lam2,
        "hoffman_alpha": hoffman,
        "delsarte_omega": max(1.0, delsarte),
        "ratio_omega": ratio,
        "inertia_alpha": int(inertia_alpha),
        "n_pos": pos,
        "n_neg": neg,
        "n_zero": zero,
    }


def nikiforov_clique_lower(lam_max: float, n: int, m: int) -> float:
    """Nikiforov-type Motzkin–Straus lower bound: ω ≥ 1 + λ^2 / (2m − λ) roughly.
    Uses 1 − 1/ω ≥ λ_max / n for the all-ones Rayleigh when regular of degree λ_max.
    For a d-regular graph, 1 − 1/ω ≥ d/n is false in general; the MS quadratic
    optimum is at least d/n only if a regular simplex sits in a clique.
    We report the Wilf lower bound ω ≥ n/(n − λ_max) which is valid for the
    chromatic number side as a *weak* clique lower bound only when the graph
    is a disjoint union of cliques. Kept as a diagnostic, not a certificate.
    """
    if n <= lam_max + 1e-9:
        return float(n)
    return float(n / (n - lam_max))
