"""Small NumPy/CuPy boundary shared by the independent numerical solvers."""

from __future__ import annotations

from typing import Any

import numpy as np


def array_module(backend: str):
    """Return NumPy or an optional CuPy backend without making GPU mandatory."""

    if backend == "numpy":
        return np
    if backend == "cupy":
        try:
            import cupy  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on A100 environment
            raise RuntimeError(
                "backend='cupy' requires CuPy in the execution environment; "
                "install a CUDA-compatible cupy package on the A100 host"
            ) from exc
        return cupy
    raise ValueError(f"unsupported backend: {backend!r}")


def to_numpy(value: Any) -> np.ndarray:
    """Copy an array from NumPy/CuPy to host NumPy."""

    module = type(value).__module__.split(".", 1)[0]
    if module == "cupy":  # pragma: no cover - depends on A100 environment
        import cupy  # type: ignore

        return cupy.asnumpy(value)
    return np.asarray(value)
