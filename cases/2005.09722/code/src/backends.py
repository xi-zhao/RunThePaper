"""Numerical backends for the paper-scale QSD campaign.

The backend seam is intentionally narrow: it evolves one independently seeded
QSD/QSDc trajectory and returns an ordinary NumPy orbital matrix.  Scientific
observables remain in :mod:`monitored_fermion`, so selecting an accelerator
cannot change their definitions.  Noise is generated on the CPU from the
case-owned seed and supplied to every adapter; this makes CPU/GPU parity a
meaningful test instead of a comparison between different random streams.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np


class BackendUnavailable(RuntimeError):
    """Raised when a requested numerical backend is not installed or usable."""


@dataclass(frozen=True)
class Backend:
    name: str
    xp: Any

    def asarray(self, value: Any) -> Any:
        return self.xp.asarray(value)

    def to_numpy(self, value: Any) -> np.ndarray:
        if self.name == "numpy":
            return np.asarray(value)
        return np.asarray(self.xp.asnumpy(value))


def load_backend(name: str) -> Backend:
    """Load the named backend without making CuPy a local dependency."""

    normalized = name.strip().lower()
    if normalized == "numpy":
        return Backend("numpy", np)
    if normalized != "cupy":
        raise ValueError(f"unsupported backend: {name}")
    try:
        import cupy as cp  # type: ignore[import-not-found]
    except ImportError as exc:
        raise BackendUnavailable(
            "CuPy is not installed; use requirements-a100.txt on the A100 host"
        ) from exc
    try:
        device_count = int(cp.cuda.runtime.getDeviceCount())
    except Exception as exc:  # pragma: no cover - depends on CUDA runtime
        raise BackendUnavailable(f"CuPy cannot access CUDA: {exc}") from exc
    if device_count < 1:
        raise BackendUnavailable("CuPy reports no CUDA device")
    return Backend("cupy", cp)


def evolve_qsd_backend(
    *,
    length: int,
    gamma: float,
    dt: float,
    t_final: float,
    protocol: str,
    seed: int,
    backend_name: str,
) -> np.ndarray:
    """Evolve one trajectory with the printed QSD/QSDc Trotter update.

    At most one full trajectory state is resident in host memory.  A CuPy
    adapter may hold the corresponding state on the device, but the returned
    value is always NumPy so all downstream observables share one code path.
    """

    if length < 4 or length % 2:
        raise ValueError("length must be an even integer >= 4")
    if gamma < 0.0 or dt <= 0.0 or t_final < 0.0:
        raise ValueError("gamma/timing parameters are invalid")
    if protocol not in {"qsd", "qsdc"}:
        raise ValueError("protocol must be qsd or qsdc")

    backend = load_backend(backend_name)
    xp = backend.xp
    orbitals = xp.zeros((length, length // 2), dtype=xp.complex128)
    occupied = xp.arange(1, length, 2)
    columns = xp.arange(length // 2)
    orbitals[occupied, columns] = 1.0
    momenta = 2.0 * np.pi * np.arange(length, dtype=np.float64) / length
    phases = backend.asarray(np.exp(-2.0j * np.cos(momenta) * dt))
    generator = np.random.default_rng(seed)
    sigma = 1.0 if protocol == "qsd" else 0.0
    steps = int(np.ceil(t_final / dt - 1e-12))
    noise_schedule = (
        backend.asarray(np.sqrt(gamma * dt) * generator.normal(size=(steps, length)))
        if gamma > 0.0
        else None
    )

    for step in range(steps):
        densities = xp.sum(xp.abs(orbitals) ** 2, axis=1).real
        transformed = xp.fft.fft(orbitals, axis=0)
        evolved = xp.fft.ifft(phases[:, None] * transformed, axis=0)
        if gamma > 0.0:
            # CPU-owned noise makes the same seed mean the same stochastic
            # trajectory for both adapters.  One batched transfer avoids a
            # host/device synchronization at every time step.
            assert noise_schedule is not None
            noise = noise_schedule[step]
            exponent = noise + gamma * sigma * (2.0 * densities - 1.0) * dt
            evolved = xp.exp(exponent)[:, None] * evolved
        orthonormal, triangular = xp.linalg.qr(evolved, mode="reduced")
        diagonal = xp.diag(triangular)
        magnitude = xp.abs(diagonal)
        safe = xp.where(magnitude > 1e-15, magnitude, 1.0)
        orbital_phases = xp.where(magnitude > 1e-15, diagonal / safe, 1.0)
        orbitals = orthonormal * orbital_phases[None, :]

    return np.asarray(backend.to_numpy(orbitals), dtype=np.complex128)


def benchmark_backend(
    *,
    backend_name: str,
    length: int,
    gamma: float,
    dt: float,
    steps: int,
    seed: int,
    tolerance: float,
) -> dict[str, Any]:
    """Compare one adapter with the established NumPy reference path."""

    from monitored_fermion import (
        QSDConfig,
        correlation_matrix,
        evolve_qsd,
        orthonormality_residual,
        subsystem_entropy,
    )

    t_final = dt * steps
    reference_started = perf_counter()
    reference = evolve_qsd(
        QSDConfig(
            length=length,
            gamma=gamma,
            dt=dt,
            t_final=t_final,
            protocol="qsd",
        ),
        seed=seed,
    )
    reference_seconds = perf_counter() - reference_started

    candidate_started = perf_counter()
    candidate = evolve_qsd_backend(
        length=length,
        gamma=gamma,
        dt=dt,
        t_final=t_final,
        protocol="qsd",
        seed=seed,
        backend_name=backend_name,
    )
    candidate_seconds = perf_counter() - candidate_started

    correlation_difference = float(
        np.max(np.abs(correlation_matrix(candidate) - correlation_matrix(reference)))
    )
    reference_entropy = subsystem_entropy(reference, range(length // 2))
    candidate_entropy = subsystem_entropy(candidate, range(length // 2))
    entropy_difference = abs(candidate_entropy - reference_entropy)
    residual = orthonormality_residual(candidate)
    passed = bool(
        correlation_difference <= tolerance
        and entropy_difference <= tolerance
        and residual <= max(tolerance, 1e-12)
    )
    return {
        "backend": backend_name,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "length": length,
        "gamma": gamma,
        "dt": dt,
        "steps": steps,
        "seed": seed,
        "tolerance": tolerance,
        "max_correlation_matrix_abs_difference": correlation_difference,
        "half_entropy_abs_difference": entropy_difference,
        "orthonormality_residual": residual,
        "reference_seconds": reference_seconds,
        "candidate_seconds": candidate_seconds,
        "candidate_steps_per_second": steps / max(candidate_seconds, 1e-12),
    }


def run_backend_benchmark(
    benchmark_config: dict[str, Any], *, smoke: bool = False
) -> dict[str, Any]:
    """Run declared CPU/accelerator probes and select a parity-safe backend."""

    lengths = [int(value) for value in benchmark_config["lengths"]]
    steps = int(benchmark_config["steps"])
    if smoke:
        lengths = [int(benchmark_config.get("smoke_length", 12))]
        steps = int(benchmark_config.get("smoke_steps", 2))
    candidates = [str(value) for value in benchmark_config["candidates"]]
    rows: list[dict[str, Any]] = []
    for backend_name in candidates:
        for length in lengths:
            try:
                rows.append(
                    benchmark_backend(
                        backend_name=backend_name,
                        length=length,
                        gamma=float(benchmark_config["gamma"]),
                        dt=float(benchmark_config["dt"]),
                        steps=steps,
                        seed=int(benchmark_config["seed"]),
                        tolerance=float(benchmark_config["parity_tolerance"]),
                    )
                )
            except BackendUnavailable as exc:
                rows.append(
                    {
                        "backend": backend_name,
                        "length": length,
                        "status": "unavailable",
                        "passed": False,
                        "reason": str(exc),
                    }
                )

    numpy_rows = [row for row in rows if row["backend"] == "numpy"]
    numpy_passed = bool(numpy_rows and all(row.get("passed") for row in numpy_rows))
    eligible = [row for row in rows if row.get("passed")]
    throughput: dict[str, float] = {}
    for row in eligible:
        backend_name = str(row["backend"])
        throughput[backend_name] = throughput.get(backend_name, 0.0) + float(
            row["candidate_steps_per_second"]
        )
    selected = max(throughput, key=throughput.get) if throughput else None
    return {
        "schema_version": 1,
        "status": "passed" if numpy_passed else "failed",
        "execution_mode": "smoke" if smoke else "paper_scale_benchmark",
        "benchmark_config_sha256": hashlib.sha256(
            json.dumps(
                benchmark_config,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest(),
        "selected_backend": selected,
        "accelerator_available": any(
            row["backend"] == "cupy" and row.get("passed") for row in rows
        ),
        "results": rows,
    }
