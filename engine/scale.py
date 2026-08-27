"""Local vs RunPod resource knobs. CUDA ⇒ runpod defaults; override with RAMSEY_SCALE."""

from __future__ import annotations

import os

from . import backend


def scale_name() -> str:
    env = os.environ.get("RAMSEY_SCALE", "").strip().lower()
    if env in ("local", "runpod", "full"):
        return "runpod" if env == "full" else env
    return "runpod" if backend.CUDA_AVAILABLE else "local"


LIMITS = {
    "local": {
        "paley_max": 101,
        "cyclo_max": 181,
        "cyclo_e_max": 8,
        "f2_lo": 8,
        "f2_hi": 10,
        "gq_q": (2, 3, 5),
        "gq_q_big": (7,),
        "ils_steps": 80,
        "circ_n_max": 47,
        "fw": ((7, 3, (0, 1)), (8, 3, (0, 1))),
        "paley_ils": (17, 37),
        "anf_bits": (8, 9),
        "anf_trials": 8,
        "time_limit": 0.4,
        "mask_keep": 2,
        "disperser_primes": (13, 17, 19, 37),
    },
    "runpod": {
        "paley_max": 997,
        "cyclo_max": 10_000,
        "cyclo_e_max": 12,
        "f2_lo": 8,
        "f2_hi": 12,
        "gq_q": (2, 3, 5, 7),
        "gq_q_big": (11, 13),
        "ils_steps": 2000,
        "circ_n_max": 251,
        "fw": ((8, 3, (0, 1)), (9, 3, (0, 1)), (11, 5, (0, 1))),
        "paley_ils": (17, 37, 41, 61, 73, 101, 109, 157, 181, 229, 241, 251),
        "anf_bits": (13, 14, 15, 16),
        "anf_trials": 32,
        "time_limit": 2.0,
        "mask_keep": 4,
        "disperser_primes": (13, 17, 37, 41, 61, 73, 109),
    },
}


def limits() -> dict:
    return dict(LIMITS[scale_name()])
