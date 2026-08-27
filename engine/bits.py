"""Numpy 1.x / 2.x popcount. np.bitwise_count is 2.0+; RunPod images may ship 1.26."""

from __future__ import annotations

import numpy as np


def bitwise_count(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a)
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(a)
    raw = np.ascontiguousarray(a)
    return np.unpackbits(raw.view(np.uint8)).reshape(*raw.shape, -1).sum(axis=-1)
