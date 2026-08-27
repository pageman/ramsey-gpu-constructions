"""Run the GPU-native construction sweep and emit dashboard JSON/CSV."""

from __future__ import annotations

import csv
import json
import math
import sys
import time
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import backend
from engine.certify import certify
from engine.constructions import (
    cyclotomic_union,
    features,
    generalized_paley,
    gold_trace_f2,
    nagy_intersecting,
    paley_prime,
    paley_prime_power,
    polarity_pg2,
    primes_between,
    quadratic_form_f2,
    singer_difference,
    tensor_strong_product,
)
from engine.gap import DONE_IN_RUN001, GAP

DATA = ROOT / "data"
PUBLIC = ROOT / "public" / "data"
SRC_DATA = ROOT / "src" / "data"


def _emit(adj, meta, exact_limit=21, save_adj=False):
    t0 = time.perf_counter()
    cert = certify(adj, exact_limit=exact_limit)
    row = features(adj, meta, cert)
    row["runtime_sec"] = round(time.perf_counter() - t0, 4)
    row["params"] = json.dumps(meta.get("params", {}), default=str)
    if save_adj and adj.shape[0] <= 64:
        path = ROOT / row["adj_matrix_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, adj)
    print(
        f"  {row['graph_id']:55s} N={row['N']:4d}  k>{row['k_target']:<3d}  "
        f"N^{{1/k}}={row['n_1_over_k']:.4f}  exact={row['exact']}",
        flush=True,
    )
    return row


def sweep() -> list[dict]:
    rows: list[dict] = []
    print(f"device: {backend.device_name()}", flush=True)

    print("\n== Paley primes (Run001 baseline) ==", flush=True)
    for p in primes_between(5, 101):
        if p % 4 != 1:
            continue
        adj, meta = paley_prime(p)
        rows.append(_emit(adj, meta, exact_limit=21 if p <= 21 else 0, save_adj=p <= 17))

    print("\n== Paley prime powers F_p^2 (NOT in Run001) ==", flush=True)
    for p in (3, 5, 7, 11, 13):
        try:
            adj, meta = paley_prime_power(p, 2)
        except ValueError as exc:
            print(f"  skip p={p}: {exc}")
            continue
        n = adj.shape[0]
        rows.append(_emit(adj, meta, exact_limit=21 if n <= 21 else 0, save_adj=n <= 25))

    print("\n== Generalized Paley k>2 (NOT in Run001) ==", flush=True)
    for k in (3, 4, 6):
        for p in primes_between(13, 181):
            if (p - 1) % k != 0:
                continue
            if ((p - 1) // k) % 2 != 0:
                continue
            if p > 120 and k == 3:
                pass
            try:
                adj, meta = generalized_paley(p, k)
            except ValueError:
                continue
            rows.append(_emit(adj, meta, exact_limit=21 if p <= 21 else 0))

    print("\n== Cyclotomic class unions (NOT in Run001) ==", flush=True)
    # e=4: pair classes (0,2) and (1,3). Paley is e=2. Try 0∪1 and 0 only after closure.
    for p in primes_between(13, 73):
        if (p - 1) % 4 != 0:
            continue
        for mask in (0b0011, 0b0101, 0b1001):
            adj, meta = cyclotomic_union(p, 4, mask)
            # skip empty / complete
            deg = int(adj[0].sum())
            if deg <= 1 or deg >= p - 2:
                continue
            rows.append(_emit(adj, meta, exact_limit=21 if p <= 21 else 0))

    print("\n== Quadratic-form Cayley on F_2^n (NOT in Run001) ==", flush=True)
    for n_bits in range(4, 9):
        for form in ("symplectic", "adjacent_bits"):
            adj, meta = quadratic_form_f2(n_bits, form)
            n = adj.shape[0]
            rows.append(_emit(adj, meta, exact_limit=21 if n <= 21 else 0, save_adj=n <= 32))

    print("\n== Gold trace Cayley on F_2^n (NOT in Run001) ==", flush=True)
    for n_bits, k in ((5, 1), (5, 2), (7, 1), (7, 3)):
        adj, meta = gold_trace_f2(n_bits, k)
        n = adj.shape[0]
        rows.append(_emit(adj, meta, exact_limit=21 if n <= 21 else 0, save_adj=n <= 32))

    print("\n== Polarity graphs of PG(2,q) (NOT in Run001) ==", flush=True)
    for q in (3, 5, 7, 11, 13):
        adj, meta = polarity_pg2(q)
        n = adj.shape[0]
        rows.append(_emit(adj, meta, exact_limit=21 if n <= 21 else 0, save_adj=n <= 31))

    print("\n== Nagy intersecting families (NOT in Run001) ==", flush=True)
    for t in range(6, 16):
        adj, meta = nagy_intersecting(t)
        n = adj.shape[0]
        rows.append(_emit(adj, meta, exact_limit=21 if n <= 21 else 0, save_adj=n <= 21))

    print("\n== Strong-product lifts (NOT in Run001) ==", flush=True)
    for p in (5, 13, 17):
        seed, seed_meta = paley_prime(p)
        adj, meta = tensor_strong_product(seed, seed_meta["construction_type"] + f"_{p}")
        n = adj.shape[0]
        rows.append(_emit(adj, meta, exact_limit=0, save_adj=False))

    print("\n== Singer difference circulants (NOT in Run001) ==", flush=True)
    for q in (2, 3, 4, 5):
        try:
            adj, meta = singer_difference(q)
        except Exception as exc:
            print(f"  skip singer q={q}: {exc}")
            continue
        n = adj.shape[0]
        rows.append(_emit(adj, meta, exact_limit=21 if n <= 21 else 0, save_adj=n <= 21))

    return rows


def fit_exponential(rows: list[dict], construction: str | None = None) -> dict:
    pts = []
    for r in rows:
        if construction and r["construction_type"] != construction:
            continue
        if not r["is_k_free"]:
            continue
        k = int(r["k_target"])
        n = int(r["N"])
        if k >= 3 and n >= 2:
            pts.append((k, math.log(n)))
    if len(pts) < 2:
        return {"C": None, "slope": None, "points": len(pts), "construction": construction}
    ks = np.array([p[0] for p in pts], dtype=float)
    logs = np.array([p[1] for p in pts], dtype=float)
    slope, intercept = np.polyfit(ks, logs, 1)
    return {
        "C": float(math.exp(slope)),
        "slope": float(slope),
        "intercept": float(intercept),
        "points": len(pts),
        "construction": construction or "all",
        "mean_n_1_over_k": float(np.mean([r["n_1_over_k"] for r in rows if (not construction or r["construction_type"] == construction)])),
    }


def oeis_reference() -> list[dict]:
    """OEIS A000791 diagonal Ramsey numbers R(k,k) where known, else lower/upper."""
    return [
        {"k": 3, "R": 6, "status": "exact", "oeis": "A000791"},
        {"k": 4, "R": 18, "status": "exact", "oeis": "A000791"},
        {"k": 5, "R_lower": 43, "R_upper": 48, "status": "open", "oeis": "A000791"},
        {"k": 6, "R_lower": 102, "R_upper": 161, "status": "open", "oeis": "A000791"},
        {"k": 7, "R_lower": 205, "R_upper": 540, "status": "open", "oeis": "A000791"},
        {"k": 8, "R_lower": 282, "R_upper": 1870, "status": "open", "oeis": "A000791"},
        {"k": 9, "R_lower": 565, "R_upper": 6588, "status": "open", "oeis": "A000791"},
        {"k": 10, "R_lower": 798, "R_upper": 23529, "status": "open", "oeis": "A000791"},
    ]


def erdos_bound(k: int) -> float:
    """Erdős 1947 probabilistic lower bound R(k,k) > (1+o(1)) √2 ^ k * k / e."""
    return (math.sqrt(2) ** k) * k / math.e


def frankl_wilson_n(k: int) -> float:
    """Rough FW vertex count inverted: k ~ exp(c sqrt(log N log log N)).
    Report N such that the FW homogeneous-set size equals k — polynomial-ish
    superpoly: N ≈ exp( (log k)^2 / c^2 / log log ...). Use the standard
    inversion N > k^{c log k / log log k} wait that's R(k,k) > that.
    FW: R(k,k) > k^{c log k / log log k}. That's the lower bound on R, i.e. N.
    """
    if k < 4:
        return float(k)
    ll = math.log(k)
    lll = max(math.log(ll), 0.5)
    return float(k ** (0.5 * ll / lll))


def write_outputs(rows: list[dict]) -> None:
    for d in (DATA, PUBLIC, SRC_DATA):
        d.mkdir(parents=True, exist_ok=True)

    # CSV
    fieldnames = list(rows[0].keys()) if rows else []
    csv_path = DATA / "ramsey_constructions.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    (PUBLIC / "ramsey_constructions.csv").write_text(csv_path.read_text())

    types = sorted({r["construction_type"] for r in rows})
    fits = [fit_exponential(rows, t) for t in types]
    fits.append(fit_exponential(rows, None))

    heatmaps = {}
    for key, builder in (
        ("paley_17", lambda: paley_prime(17)[0]),
        ("paley_f9", lambda: paley_prime_power(3, 2)[0]),
        ("f2_symplectic_16", lambda: quadratic_form_f2(4, "symplectic")[0]),
        ("polarity_pg2_3", lambda: polarity_pg2(3)[0]),
        ("nagy_6", lambda: nagy_intersecting(6)[0]),
    ):
        heatmaps[key] = builder().astype(int).tolist()

    payload = {
        "device": backend.device_name(),
        "n_graphs": len(rows),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run001_done": DONE_IN_RUN001,
        "gap": GAP,
        "fits": fits,
        "oeis_a000791": oeis_reference(),
        "reference_curves": [
            {
                "name": "Erdős probabilistic",
                "points": [{"k": k, "N": erdos_bound(k)} for k in range(3, 16)],
            },
            {
                "name": "Frankl–Wilson (explicit, inverted)",
                "points": [{"k": k, "N": frankl_wilson_n(k)} for k in range(3, 16)],
            },
            {
                "name": "Target C=1.01 exponential",
                "points": [{"k": k, "N": 1.01 ** k} for k in range(3, 16)],
            },
        ],
        "graphs": rows,
        "best_by_type": [],
        "heatmaps": heatmaps,
    }
    # best N^{1/k} per type among certified k-free
    for t in types:
        cand = [r for r in rows if r["construction_type"] == t and r["is_k_free"]]
        if not cand:
            continue
        best = max(cand, key=lambda r: r["n_1_over_k"])
        payload["best_by_type"].append(
            {
                "construction_type": t,
                "graph_id": best["graph_id"],
                "N": best["N"],
                "k_target": best["k_target"],
                "n_1_over_k": best["n_1_over_k"],
                "run001": best["run001"],
                "gpu_kernel": best["gpu_kernel"],
            }
        )

    for dest in (DATA / "catalog.json", PUBLIC / "catalog.json", SRC_DATA / "catalog.json"):
        dest.write_text(json.dumps(payload, indent=2, default=str, allow_nan=False))
    print(f"\nwrote {len(rows)} graphs → {csv_path} and catalog.json")


def main() -> int:
    try:
        rows = sweep()
        if not rows:
            print("no graphs generated", file=sys.stderr)
            return 1
        write_outputs(rows)
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
