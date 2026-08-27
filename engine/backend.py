"""Array backend: NumPy today, CUDA tensors when a GPU is present.

Every construction kernel is written as batched array ops (outer differences,
XOR tables, GEMMs) so the same code path maps onto cuBLAS / CUDA bitwise
kernels without rewriting the math.
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np

try:
    import torch

    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = bool(torch.cuda.is_available())
except Exception:  # pragma: no cover - torch is optional
    torch = None  # type: ignore
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False

USE_TORCH = CUDA_AVAILABLE and os.environ.get("RAMSEY_FORCE_NUMPY") != "1"


def device_name() -> str:
    if USE_TORCH:
        return f"cuda:{torch.cuda.get_device_name(0)}"
    if TORCH_AVAILABLE:
        return "torch-cpu"
    return "numpy-openblas"


def as_float(x: Any):
    if USE_TORCH:
        t = torch.as_tensor(x, device="cuda", dtype=torch.float64)
        return t
    return np.asarray(x, dtype=np.float64)


def as_int(x: Any):
    if USE_TORCH:
        return torch.as_tensor(x, device="cuda", dtype=torch.int64)
    return np.asarray(x, dtype=np.int64)


def to_numpy(x: Any) -> np.ndarray:
    if USE_TORCH and torch is not None and isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x)


def matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """GEMM — the primitive behind triangle counts, polarity dots, and spectra."""
    if USE_TORCH:
        ta = torch.as_tensor(a, device="cuda", dtype=torch.float64)
        tb = torch.as_tensor(b, device="cuda", dtype=torch.float64)
        return (ta @ tb).cpu().numpy()
    return np.asarray(a, dtype=np.float64) @ np.asarray(b, dtype=np.float64)


def eigvalsh(adj: np.ndarray) -> np.ndarray:
    if USE_TORCH and adj.shape[0] >= 64:
        t = torch.as_tensor(adj, device="cuda", dtype=torch.float64)
        # torch.linalg.eigvalsh is GPU-resident for symmetric matrices
        return torch.linalg.eigvalsh(t).cpu().numpy()
    return np.linalg.eigvalsh(np.asarray(adj, dtype=np.float64))
