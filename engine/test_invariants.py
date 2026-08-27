"""Sanity checks against known Ramsey graphs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.certify import certify, triangle_count
from engine.constructions import (
    generalized_paley,
    nagy_intersecting,
    paley_prime,
    paley_prime_power,
    polarity_pg2,
    quadratic_form_f2,
    singer_difference,
)


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_paley_5() -> None:
    adj, _ = paley_prime(5)
    _assert(adj.shape == (5, 5), "Paley(5) order")
    _assert(adj.sum() == 10, "C5 has 5 edges")  # 5*2
    c = certify(adj)
    _assert(c["omega_exact"] == 2, f"C5 is triangle-free, got {c}")
    _assert(c["alpha_exact"] == 2, "C5 independence")


def test_paley_17() -> None:
    adj, _ = paley_prime(17)
    c = certify(adj, exact_limit=17)
    _assert(c["omega_exact"] == 3, f"Paley(17) is K4-free, ω={c['omega_exact']}")
    _assert(c["alpha_exact"] == 3, f"Paley(17) α={c['alpha_exact']}")
    _assert(c["k_certified"] == 4, "R(4,4)>17")
    _assert(triangle_count(adj) > 0, "Paley(17) has triangles")


def test_paley_9() -> None:
    adj, meta = paley_prime_power(3, 2)
    _assert(adj.shape[0] == 9, "F_9 Paley")
    _assert(meta["run001"] == "not_done", "flagged as skipped in Run001")
    _assert((adj == adj.T).all() and adj.diagonal().sum() == 0, "simple undirected")


def test_gp_k3() -> None:
    # p=13, 13-1=12 divisible by 3, (p-1)/3=4 even. GP(13,3)
    adj, meta = generalized_paley(13, 3)
    _assert(adj.shape[0] == 13, "GP(13,3)")
    deg = int(adj[0].sum())
    _assert(deg == 4, f"degree (p-1)/k = 4, got {deg}")


def test_nagy() -> None:
    adj, _ = nagy_intersecting(6)
    _assert(adj.shape[0] == 15, "C(6,2)=15")
    c = certify(adj, exact_limit=15)
    # star at a vertex: 5 pairs, clique 5; matching independent set size 3
    _assert(c["omega_exact"] == 5, f"Nagy(6) ω={c['omega_exact']}")


def test_f2_symplectic() -> None:
    adj, _ = quadratic_form_f2(4, "symplectic")
    _assert(adj.shape[0] == 16, "2^4")
    _assert((adj == adj.T).all(), "undirected")


def test_polarity() -> None:
    adj, meta = polarity_pg2(3)
    _assert(adj.shape[0] == 13, "PG(2,3) has 13 points")
    _assert(meta["gpu_kernel"].startswith("point_enum"), "GEMM kernel")


def test_singer_fano() -> None:
    adj, meta = singer_difference(2)
    _assert(adj.shape[0] == 7, "Fano circulant")
    _assert(int(adj[0].sum()) in (2, 4, 6), f"degree {adj[0].sum()}")


def main() -> int:
    tests = [
        test_paley_5,
        test_paley_17,
        test_paley_9,
        test_gp_k3,
        test_nagy,
        test_f2_symplectic,
        test_polarity,
        test_singer_fano,
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
