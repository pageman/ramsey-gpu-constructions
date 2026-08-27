"""Fast certificate using FFT / FWHT / neighbourhood reduction when the symmetry fits."""

from __future__ import annotations

import numpy as np

from .kernels.mcs import is_circulant, is_f2_cayley, max_clique, omega_vertex_transitive
from .kernels.rowcert import certify_boolean_cayley, certify_circulant_row
from .kernels.spectrum import (
    boolean_cayley_eigenvalues,
    fft_eigenvalues,
    spectral_bounds_from_eigs,
    triangle_count_circulant,
)


def certify_fast(adj: np.ndarray, time_limit: float = 1.0, paley_q: int | None = None) -> dict:
    adj = np.asarray(adj, dtype=np.uint8)
    np.fill_diagonal(adj, 0)
    n = int(adj.shape[0])

    if is_circulant(adj):
        rec = certify_circulant_row(adj[0], time_limit=time_limit, paley_q=paley_q)
        rec["k4"] = rec.get("k4", -1)
        rec["k4_complement"] = rec.get("k4_complement", -1)
        rec["triangles_complement"] = rec.get("triangles_complement", -1)
        return rec
    if is_f2_cayley(adj) and n >= 4:
        rec = certify_boolean_cayley(adj[0], time_limit=time_limit)
        rec["k4"] = -1
        rec["k4_complement"] = -1
        rec["triangles_complement"] = -1
        return rec

    from . import certify as base

    rec = base.certify(adj, exact_limit=21 if n <= 21 else 0)
    rec["symmetry"] = "none"
    rec["kernel"] = "generic"
    rec.setdefault("delsarte_omega", rec.get("omega_upper", n))
    return rec


def certify_row(row: np.ndarray, time_limit: float = 1.0, paley_q: int | None = None) -> dict:
    """O(n) memory path for circulants — never materializes A."""
    return certify_circulant_row(row, time_limit=time_limit, paley_q=paley_q)
