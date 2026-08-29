"""Kernel invariants: FFT Paley 17, VT ω, FWHT, O(p) QR vs Euler."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.certify import certify
from engine.constructions import paley_prime, polarity_gq, frankl_wilson
from engine.kernels.cayley import k4_free_via_neighbourhood, triangle_free_circulant
from engine.kernels.mcs import omega_vertex_transitive
from engine.kernels.rowcert import certify_boolean_cayley, certify_circulant_row, paley_closed_eigs
from engine.kernels.sieve import quadratic_residue_row
from engine.kernels.spectrum import fft_eigenvalues, fwht, spectral_bounds_from_eigs


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_paley17_fft_matches_hermitian() -> None:
    adj, _ = paley_prime(17)
    row = adj[0].astype(np.float64)
    fft = np.sort(fft_eigenvalues(row))
    her = np.sort(np.linalg.eigvalsh(adj.astype(np.float64)))
    _assert(np.allclose(fft, her, atol=1e-8), f"FFT vs eigvalsh {fft[-1]} {her[-1]}")
    _assert(abs(fft[-1] - 8) < 1e-8, f"λ_max Paley17 = 8, got {fft[-1]}")
    closed = np.sort(paley_closed_eigs(17))
    _assert(np.allclose(fft, closed, atol=1e-8), "closed-form Paley spectrum")
    a = (-1 + np.sqrt(17)) / 2
    _assert(any(abs(x - a) < 1e-8 for x in fft), "λ = (√17-1)/2")


def test_paley17_vt_omega() -> None:
    adj, _ = paley_prime(17)
    om = omega_vertex_transitive(adj, time_limit=1.0)
    _assert(om["exact"] and om["lower"] == 3, f"VT ω Paley17 = 3, got {om}")
    rec = certify_circulant_row(adj[0], time_limit=1.0, paley_q=17)
    _assert(rec["exact"] and rec["omega_exact"] == 3 and rec["alpha_exact"] == 3, rec)
    _assert(rec["k_certified"] == 4, "R(4,4)>17")
    _assert(k4_free_via_neighbourhood(adj[0]), "N(0) triangle-free ⇒ K4-free")


def test_qr_row_matches_euler() -> None:
    p = 17
    row = quadratic_residue_row(p)
    euler = np.array([1 if d and pow(int(d), (p - 1) // 2, p) == 1 else 0 for d in range(p)], dtype=np.uint8)
    _assert(np.array_equal(row, euler), "O(p) squares vs Euler criterion")


def test_fwht_hadamard() -> None:
    n = 8
    e0 = np.zeros(n)
    e0[0] = 1
    h = fwht(e0)
    _assert(np.allclose(h, np.ones(n)), f"FWHT of e0 is all-ones, got {h}")
    x = np.arange(n, dtype=np.float64)
    _assert(np.allclose(fwht(fwht(x)) / n, x), "FWHT involution")


def test_c5_triangle_free() -> None:
    row = quadratic_residue_row(5)
    _assert(triangle_free_circulant(row), "Paley5 = C5 is triangle-free")
    rec = certify_circulant_row(row, time_limit=0.5, paley_q=5)
    _assert(rec["omega_exact"] == 2 and rec["alpha_exact"] == 2, rec)


def test_gq2_order() -> None:
    adj, meta = polarity_gq(2)
    _assert(adj.shape[0] == 15, f"W(3,2) has 15 points, got {adj.shape[0]}")
    _assert((adj == adj.T).all() and adj.diagonal().sum() == 0, "simple undirected")
    deg = int(adj[0].sum())
    _assert(deg == 6, f"GQ(2,2) collinearity degree 6, got {deg}")


def test_boolean_residual_limit_skips_mcs() -> None:
    """n=13 ANF residual is ~4k vertices; residual_limit=64 must not colour it."""
    from engine.constructions import anf_quadratic_f2

    _adj, meta = anf_quadratic_f2(13, seed=1)
    rec = certify_boolean_cayley(meta["boolean_f"], time_limit=0.05, residual_limit=64)
    _assert(rec.get("residual_skipped") is True, rec)
    _assert(rec["exact"] is False, rec)
    _assert(rec["N"] == 8192, rec)
    _assert(rec["kernel"] == "fwht", rec)


def test_fw_small() -> None:
    adj, meta = frankl_wilson(6, 2, (1,))
    _assert(adj.shape[0] == 15, "C(6,2)")
    # |A∩B|=1 is the Nagy graph
    c = certify(adj, exact_limit=15)
    _assert(c["omega_exact"] == 5, c)


def main() -> int:
    tests = [
        test_paley17_fft_matches_hermitian,
        test_paley17_vt_omega,
        test_qr_row_matches_euler,
        test_fwht_hadamard,
        test_c5_triangle_free,
        test_gq2_order,
        test_boolean_residual_limit_skips_mcs,
        test_fw_small,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"ok  {t.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {t.__name__}: {exc}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
