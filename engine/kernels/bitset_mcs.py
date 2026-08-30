"""Bitset independent-set search for residuals n ≤ 256.

Decision-first: stop when a set of size `target` is found (reject), or when
every branch is pruned (accept). Circulant residuals are sparse; MIS on
G[N^c(0)] is the primitive. A tiny C kernel (native_mis.c) is preferred;
Python ints are the fallback.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import time
from pathlib import Path
from typing import Any

_LIB = None
_LIB_TRIED = False


def _load_native():
    global _LIB, _LIB_TRIED
    if _LIB_TRIED:
        return _LIB
    _LIB_TRIED = True
    here = Path(__file__).resolve().parent
    src = here / "native_mis.c"
    so = here / "native_mis.so"
    if not so.exists() or (src.exists() and src.stat().st_mtime > so.stat().st_mtime):
        try:
            subprocess.check_call(
                ["gcc", "-O3", "-shared", "-fPIC", "-o", str(so), str(src)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
    try:
        lib = ctypes.CDLL(str(so))
        lib.mis_decide.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.c_int,
            ctypes.c_double,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_long),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]
        lib.mis_decide.restype = ctypes.c_int
        _LIB = lib
        return _LIB
    except OSError:
        return None


def _pack_nbr(nbr: list[int]) -> list[int]:
    """Flatten n×4 uint64 words (little-endian bits 0..255)."""
    words: list[int] = []
    for mask in nbr:
        m = int(mask)
        for _ in range(4):
            words.append(m & ((1 << 64) - 1))
            m >>= 64
    return words


def _mis_native(nbr: list[int], target: int, time_limit: float, greedy_lower: int) -> dict[str, Any] | None:
    n = len(nbr)
    if n > 256:
        return None
    lib = _load_native()
    if lib is None:
        return None
    flat = _pack_nbr(nbr)
    arr = (ctypes.c_uint64 * len(flat))(*flat)
    nodes = ctypes.c_long(0)
    lower = ctypes.c_int(0)
    timed = ctypes.c_int(0)
    t0 = time.perf_counter()
    found = lib.mis_decide(n, arr, target, float(time_limit), int(greedy_lower), ctypes.byref(nodes), ctypes.byref(lower), ctypes.byref(timed))
    return {
        "found": bool(found),
        "lower": int(lower.value),
        "exact": not bool(timed.value),
        "nodes": int(nodes.value),
        "seconds": time.perf_counter() - t0,
        "timed_out": bool(timed.value),
        "backend": "c",
    }


def _closed(nbr: list[int]) -> list[int]:
    return [nbr[v] | (1 << v) for v in range(len(nbr))]


def greedy_mis(nbr: list[int], order: list[int] | None = None) -> int:
    n = len(nbr)
    if n == 0:
        return 0
    if order is None:
        order = [v for _, v in sorted((nbr[v].bit_count(), v) for v in range(n))]
    blocked = 0
    size = 0
    for v in order:
        if (blocked >> v) & 1:
            continue
        size += 1
        blocked |= nbr[v] | (1 << v)
    return size


def _complement_colour_ub(nbr: list[int], p: int) -> int:
    """χ(Ḡ[p]) ≥ α(G[p]). Greedy colours on the complement."""
    if p == 0:
        return 0
    verts: list[int] = []
    tmp = p
    while tmp:
        v = (tmp & -tmp).bit_length() - 1
        verts.append(v)
        tmp &= tmp - 1
    # high complement-degree first
    verts.sort(key=lambda v: -((p & ~nbr[v]).bit_count()))
    colour: dict[int, int] = {}
    used = 0
    closed_mask_extra = 0  # unused; keep loop tight
    for v in verts:
        blocked = 0
        # complement neighbours in p: p & ~nbr[v] & ~(1<<v)
        cn = p & ~nbr[v] & ~(1 << v)
        t = cn
        while t:
            u = (t & -t).bit_length() - 1
            if u in colour:
                blocked |= 1 << colour[u]
            t &= t - 1
        c = 0
        while (blocked >> c) & 1:
            c += 1
        colour[v] = c
        if c + 1 > used:
            used = c + 1
    return used


def mis_decision(
    nbr: list[int],
    target: int,
    time_limit: float = 30.0,
) -> dict[str, Any]:
    """Decide whether α(G) ≥ target.

    Finding an independent set of size `target` sets found=True (Yu reject:
    residual 19-set ⇒ α(G)≥20). Exhausting the tree without one proves
    α < target when timed_out is False.
    """
    n = len(nbr)
    t0 = time.perf_counter()
    if target <= 0:
        return {"found": True, "lower": 0, "exact": True, "nodes": 0, "seconds": 0.0, "backend": "trivial"}
    if n == 0:
        return {"found": False, "lower": 0, "exact": True, "nodes": 0, "seconds": 0.0, "backend": "trivial"}

    closed = _closed(nbr)
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
        }
    if n > 256:
        return {
            "found": False,
            "lower": lower,
            "exact": False,
            "nodes": 0,
            "seconds": time.perf_counter() - t0,
            "timed_out": True,
            "backend": "skip_n>256",
        }
    native = _mis_native(nbr, target, time_limit, lower)
    if native is not None:
        return native

    nodes = 0
    found = False
    timed_out = False
    full = (1 << n) - 1

    def rec(p: int, size: int) -> None:
        nonlocal nodes, found, timed_out, lower
        if found or timed_out:
            return
        nodes += 1
        if (nodes & 16383) == 0 and time.perf_counter() - t0 > time_limit:
            timed_out = True
            return
        if size >= target:
            found = True
            lower = size
            return
        rem = p.bit_count()
        if size + rem < target:
            if size > lower:
                lower = size
            return
        if p == 0:
            if size > lower:
                lower = size
            return
        if rem <= 48:
            ub = _complement_colour_ub(nbr, p)
            if size + ub < target:
                if size > lower:
                    lower = size
                return
        # min-degree vertex in G[p]
        tmp = p
        best_v, best_d = 0, n + 1
        while tmp:
            v = (tmp & -tmp).bit_length() - 1
            d = (nbr[v] & p).bit_count()
            if d < best_d:
                best_d = d
                best_v = v
            tmp &= tmp - 1
        v = best_v
        rec(p & ~closed[v], size + 1)
        if found or timed_out:
            return
        rec(p & ~(1 << v), size)

    rec(full, 0)
    return {
        "found": found,
        "lower": lower,
        "exact": (not timed_out) and (found or not found),
        "nodes": nodes,
        "seconds": time.perf_counter() - t0,
        "timed_out": timed_out,
    }


def mcs_decision_from_adj(adj, target: int, time_limit: float = 30.0) -> dict[str, Any]:
    """Clique decision: MIS on the complement."""
    import numpy as np

    a = np.asarray(adj, dtype=np.uint8)
    n = int(a.shape[0])
    nbr = [0] * n
    all_but = (1 << n) - 1
    for i in range(n):
        bits = 0
        row = a[i]
        for j in range(n):
            if i != j and int(row[j]):
                bits |= 1 << j
        nbr[i] = (all_but ^ (1 << i)) ^ bits
    return mis_decision(nbr, target, time_limit=time_limit)
