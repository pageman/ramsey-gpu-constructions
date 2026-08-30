"""Referee: decide α(G) < target (no independent set of that size).

Contract (plan v3 / job 5b):
- n > MAXN → skip; never call the 256-word entry.
- Timeout ≠ accept. exact=True only if the tree finished.
- Residual-only accepts are not CELL? until mixed-set is proved.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from .bitset_mcs import greedy_mis, mis_decision, _load_decide_native, _pack_nbr
from .residual import distances_to_row, nbhd_triangle_free, residual_nbr

ROOT = Path(__file__).resolve().parents[2]
MAXN = 256
CERT_PATH = ROOT / "data" / "yu_r4_20.cert.json"


def shash_distances(distances) -> str:
    payload = ",".join(str(int(d)) for d in sorted({int(x) for x in distances}))
    return hashlib.blake2b(payload.encode(), digest_size=8).hexdigest()


def decide_alpha_le(
    nbr: list[int],
    target: int,
    time_limit: float | None = None,
) -> dict[str, Any]:
    """Decide whether α(G) ≥ target. found=True means α ≥ target (reject).

    exact=True only if the search finished. n>MAXN is timed_out skip, never accept.
    """
    n = len(nbr)
    lim = float(time_limit if time_limit is not None else os.environ.get("RAMSEY_MIS_LIMIT", "25"))
    t0 = time.perf_counter()
    if target <= 0:
        return {
            "found": True,
            "lower": 0,
            "exact": True,
            "nodes": 0,
            "seconds": 0.0,
            "timed_out": False,
            "backend": "trivial",
            "n": n,
        }
    if n == 0:
        return {
            "found": False,
            "lower": 0,
            "exact": True,
            "nodes": 0,
            "seconds": 0.0,
            "timed_out": False,
            "backend": "trivial",
            "n": n,
        }
    lower = greedy_mis(nbr)
    if lower >= target:
        return {
            "found": True,
            "lower": lower,
            "exact": False,
            "nodes": 0,
            "seconds": time.perf_counter() - t0,
            "timed_out": False,
            "backend": "greedy",
            "n": n,
        }
    if n > MAXN:
        return {
            "found": False,
            "lower": lower,
            "exact": False,
            "nodes": 0,
            "seconds": time.perf_counter() - t0,
            "timed_out": True,
            "backend": "skip_n>256",
            "n": n,
        }
    native = _load_decide_native()
    if native is not None:
        import ctypes

        flat = _pack_nbr(nbr)
        arr = (ctypes.c_uint64 * len(flat))(*flat)
        nodes = ctypes.c_long(0)
        lo = ctypes.c_int(0)
        timed = ctypes.c_int(0)
        found = native.mis_decide_aim(
            n, arr, target, float(lim), int(lower), ctypes.byref(nodes), ctypes.byref(lo), ctypes.byref(timed)
        )
        return {
            "found": bool(found),
            "lower": max(int(lo.value), lower),
            "exact": not bool(timed.value),
            "nodes": int(nodes.value),
            "seconds": time.perf_counter() - t0,
            "timed_out": bool(timed.value),
            "backend": native._ramsey_backend,  # type: ignore[attr-defined]
            "n": n,
        }
    rec = mis_decision(nbr, target, time_limit=lim)
    rec["n"] = n
    return rec


def neighbourhood_nbr(row) -> list[int]:
    """Bitsets of G[N(0)]."""
    import numpy as np

    n = int(row.size)
    verts = [int(i) for i in range(1, n) if int(row[i]) == 1]
    idx = {v: k for k, v in enumerate(verts)}
    nbr = [0] * len(verts)
    for k, u in enumerate(verts):
        bits = 0
        for v in verts:
            if v == u:
                continue
            if int(row[(v - u) % n]):
                bits |= 1 << idx[v]
        nbr[k] = bits
    return nbr


def mixed_set_check(row, t_cell: int, time_limit: float) -> dict[str, Any]:
    """Before CELL?: residual accept is not enough.

    Rejects stay valid. Accepts need α(N(0)) ≤ t-2 and no mixed (t-1)-IS.
    k=1 only under a shared budget; higher k → residual_only.
    """
    t0 = time.perf_counter()
    out: dict[str, Any] = {
        "mixed_ok": False,
        "residual_only": True,
        "reason": "",
        "nbhd_alpha_lt": None,
    }
    nb = neighbourhood_nbr(row)
    if not nb:
        out["mixed_ok"] = True
        out["residual_only"] = False
        out["reason"] = "empty N(0)"
        return out
    budget = max(0.5, time_limit)
    dec = decide_alpha_le(nb, target=t_cell - 1, time_limit=min(5.0, budget))
    out["nbhd_mis"] = {k: dec[k] for k in ("found", "lower", "timed_out", "backend", "n") if k in dec}
    if dec["found"]:
        out["reason"] = f"α(N(0))≥{t_cell - 1}"
        return out
    if dec["timed_out"]:
        out["reason"] = "α(N(0)) timed out"
        return out
    # no (t-1)-IS in N(0). Need α(N(0)) ≤ t-2 for mixed of size t-1 to require residual.
    dec2 = decide_alpha_le(nb, target=t_cell - 1, time_limit=0.0)  # already know not found
    out["nbhd_alpha_lt"] = t_cell - 1
    # k=1 mixed: v in N(0) plus (t-2)-IS in residual minus N(v)
    resid_verts = [i for i in range(1, int(row.size)) if int(row[i]) == 0]
    n0 = [i for i in range(1, int(row.size)) if int(row[i]) == 1]
    idx_r = {v: k for k, v in enumerate(resid_verts)}
    left = budget - (time.perf_counter() - t0)
    if left < 0.4 or len(n0) > 96:
        out["reason"] = "mixed k≥1 not budgeted"
        return out
    per = min(2.0, left / max(len(n0), 1))
    residual_full = residual_nbr(row)
    for v in n0:
        if time.perf_counter() - t0 > budget:
            out["reason"] = "mixed k=1 budget"
            return out
        blocked = set()
        n = int(row.size)
        for u in resid_verts:
            if int(row[(u - v) % n]):
                blocked.add(u)
        # induced residual after deleting N(v)
        keep = [u for u in resid_verts if u not in blocked]
        if not keep:
            continue
        inv = {u: j for j, u in enumerate(keep)}
        sub = [0] * len(keep)
        for j, u in enumerate(keep):
            bits = 0
            old = residual_full[idx_r[u]]
            for w in keep:
                if w == u:
                    continue
                if (old >> idx_r[w]) & 1:
                    bits |= 1 << inv[w]
            sub[j] = bits
        d = decide_alpha_le(sub, target=t_cell - 2, time_limit=per)
        if d["found"]:
            out["reason"] = f"mixed IS via N(0) vertex {v}"
            return out
        if d["timed_out"]:
            out["reason"] = "mixed k=1 timed out"
            return out
    # α(N(0)) may still be ≥2, so k≥2 mixed sets are a hole.
    a_nb = decide_alpha_le(nb, target=2, time_limit=min(2.0, budget))
    if a_nb["found"]:
        out["reason"] = "α(N(0))≥2; k≥2 mixed not enumerated"
        return out
    if a_nb["timed_out"]:
        out["reason"] = "α(N(0))≥2 check timed out"
        return out
    out["mixed_ok"] = True
    out["residual_only"] = False
    out["reason"] = "α(N(0))≤1 and no k=1 mixed (t-1)-IS"
    return out


def write_yu_cert(payload: dict, path: Path = CERT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path


def load_yu_cert(path: Path = CERT_PATH) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
