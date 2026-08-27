"""GF(2^n) arithmetic for Gold / Kasami / ANF Cayley graphs.

Carry-less multiply + reduction by a primitive polynomial. The Boolean
function is evaluated once (O(N n²)), then the Cayley graph is the XOR
table f[i⊕j] — never rebuilt.
"""

from __future__ import annotations

import numpy as np

# Primitive polynomials including the x^n term, bits = coefficients.
IRR = {
    3: 0b1011,
    4: 0b10011,
    5: 0b100101,
    6: 0b1000011,
    7: 0b10000011,
    8: 0b100011101,
    9: 0b1000010001,
    10: 0b10000001001,
    11: 0b100000000101,
    12: 0b1000001010011,
    13: 0b10000000011011,
    14: 0b100010001000011,
    15: 0b1000000000000011,
    16: 0b10001000000001011,
}


def gf_mul(a: int, b: int, n_bits: int) -> int:
    irr = IRR[n_bits]
    mask = (1 << n_bits) - 1
    p = 0
    aa, bb = a, b
    while bb:
        if bb & 1:
            p ^= aa
        bb >>= 1
        aa <<= 1
    for i in range(p.bit_length() - 1, n_bits - 1, -1):
        if p & (1 << i):
            p ^= irr << (i - n_bits)
    return p & mask


def gf_pow(a: int, e: int, n_bits: int) -> int:
    r = 1
    while e:
        if e & 1:
            r = gf_mul(r, a, n_bits)
        a = gf_mul(a, a, n_bits)
        e >>= 1
    return r


def gf_trace(a: int, n_bits: int) -> int:
    s = a
    x = a
    for _ in range(n_bits - 1):
        x = gf_mul(x, x, n_bits)
        s ^= x
    return s & 1


def trace_of_power(n_bits: int, exp: int) -> np.ndarray:
    n = 1 << n_bits
    return np.array([gf_trace(gf_pow(i, exp, n_bits), n_bits) for i in range(n)], dtype=np.uint8)


def cayley_from_boolean(f: np.ndarray) -> np.ndarray:
    n = int(f.size)
    xor = np.arange(n)[:, None] ^ np.arange(n)[None, :]
    adj = f[xor].astype(np.uint8)
    np.fill_diagonal(adj, 0)
    return adj
