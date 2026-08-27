"""Linear sieve, O(n) quadratic residues, O(p) cyclotomic first rows.

CP / Project Euler staples: linear (Euler) sieve is O(n); Paley connection
sets are the image of x ↦ x², not Euler-criterion exponentiations.
"""

from __future__ import annotations

import numpy as np


def linear_sieve(limit: int) -> list[int]:
    """Primes in [2, limit] in O(n) after the harmonic factor is absorbed."""
    if limit < 2:
        return []
    spf = list(range(limit + 1))
    primes: list[int] = []
    for i in range(2, limit + 1):
        if spf[i] == i:
            primes.append(i)
        for p in primes:
            v = i * p
            if v > limit:
                break
            spf[v] = p
            if i % p == 0:
                break
    return primes


def primes_congruence(limit: int, mod: int, residue: int) -> list[int]:
    return [p for p in linear_sieve(limit) if p % mod == residue]


def divisors(n: int) -> list[int]:
    out = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            out.append(i)
            if i * i != n:
                out.append(n // i)
        i += 1
    return sorted(out)


def quadratic_residue_row(p: int) -> np.ndarray:
    """First row of Paley(p): 1 at quadratic residues. O(p) squares, not O(p log p) Euler."""
    row = np.zeros(p, dtype=np.uint8)
    i = np.arange(1, p, dtype=np.int64)
    row[np.mod(i * i, p)] = 1
    row[0] = 0
    return row


def primitive_root(p: int) -> int:
    phi = p - 1
    factors: list[int] = []
    n = phi
    d = 2
    while d * d <= n:
        if n % d == 0:
            factors.append(d)
            while n % d == 0:
                n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append(n)
    for g in range(2, p):
        if all(pow(g, phi // f, p) != 1 for f in factors):
            return g
    raise ValueError(f"no primitive root for {p}")


def cyclotomic_row(p: int, e: int, class_mask: int) -> tuple[np.ndarray, int]:
    """Connection row of a negation-closed union of index-e cyclotomic classes. O(p).

    Free bits after S = −S: e/2 when e is even. Mask is expanded to the pair
    (i, i+e/2) as in Yu 2026 / classical cyclotomy.
    """
    if (p - 1) % e != 0:
        raise ValueError("e must divide p-1")
    if e % 2 == 0:
        half = e // 2
        closed = 0
        for i in range(e):
            if class_mask & (1 << i):
                closed |= 1 << i
                closed |= 1 << ((i + half) % e)
        class_mask = closed
    g = primitive_root(p)
    row = np.zeros(p, dtype=np.uint8)
    ge = pow(g, e, p)
    width = (p - 1) // e
    for cls in range(e):
        if not (class_mask & (1 << cls)):
            continue
        x = pow(g, cls, p)
        for _ in range(width):
            row[x] = 1
            x = (x * ge) % p
    row[0] = 0
    return row, int(class_mask)


def negation_closed_masks(e: int) -> list[int]:
    """Gray-code list of nonempty S=−S class masks. 2^{e/2}−1 of them when e even."""
    if e % 2:
        return [m for m in range(1, 1 << e)]
    half = e // 2
    out = []
    for free in range(1, 1 << half):
        mask = 0
        for i in range(half):
            if free & (1 << i):
                mask |= 1 << i
                mask |= 1 << (i + half)
        out.append(mask)
    return out
