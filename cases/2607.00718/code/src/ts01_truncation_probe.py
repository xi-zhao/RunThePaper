"""Finite-cutoff diagnostic probe for Supplemental Figure S1.

This module is intentionally diagnostic: it evaluates a few discriminating
detunings and Hilbert cutoffs before the full TS01 surface is authorized.
The production TS01 target remains in ``scripts/run_target.py``.

The default backend constructs the sparse Lindblad generator and applies its
matrix exponential with SciPy's Krylov implementation.  The earlier batched
Torch RK4 backend remains available as an explicitly selected GPU diagnostic.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import Any

import numpy as np

from finite_hilbert_dynamics import simulate_finite_hilbert_trajectory


@dataclass(frozen=True)
class ProbeGrid:
    cutoffs: tuple[int, ...] = (6, 8, 10)
    normalized_detunings: tuple[float, ...] = (0.0, 1.5, 4.25)
    substeps_per_output: int = 32


def _destroy(torch: Any, cutoff: int, *, device: Any, dtype: Any) -> Any:
    operator = torch.zeros((cutoff, cutoff), device=device, dtype=dtype)
    indices = torch.arange(1, cutoff, device=device, dtype=torch.float64)
    operator[indices.to(torch.long) - 1, indices.to(torch.long)] = torch.sqrt(
        indices
    ).to(dtype)
    return operator


def _operators(
    torch: Any,
    cutoff: int,
    *,
    device: Any,
    dtype: Any,
) -> dict[str, Any]:
    identity = torch.eye(cutoff, device=device, dtype=dtype)
    local_destroy = _destroy(torch, cutoff, device=device, dtype=dtype)
    a = torch.kron(local_destroy, identity)
    b = torch.kron(identity, local_destroy)
    return {
        "a": a,
        "a_dagger": a.mH,
        "b": b,
        "b_dagger": b.mH,
        "number_a": a.mH @ a,
        "number_b": b.mH @ b,
    }


def _liouvillian_components(
    torch: Any,
    *,
    cutoff: int,
    normalized_detunings: tuple[float, ...],
    coupling: float,
    kappa: float,
    drive: float,
    squeezing: float,
    charger_phase: float,
    reservoir_phase: float,
    device: Any,
    dtype: Any,
) -> tuple[Any, list[Any], Any]:
    operators = _operators(torch, cutoff, device=device, dtype=dtype)
    a = operators["a"]
    a_dagger = operators["a_dagger"]
    b = operators["b"]
    number_a = operators["number_a"]
    number_b = operators["number_b"]
    real_dtype = torch.float64 if dtype == torch.complex128 else torch.float32

    cosh_a = float(np.cosh(squeezing))
    sinh_a = float(np.sinh(squeezing))
    phase_a = torch.exp(
        torch.tensor(1.0j * charger_phase, device=device, dtype=dtype)
    )
    squeezed_creation_a = cosh_a * a_dagger - phase_a * sinh_a * a
    squeezed_annihilation_a = squeezed_creation_a.mH
    coherent_phase = torch.exp(
        torch.tensor(0.5j * np.pi, device=device, dtype=dtype)
    )
    forward = coherent_phase * squeezed_creation_a @ b
    coherent_hamiltonian = forward + forward.mH
    drive_ratio = drive / coupling
    drive_coefficient = drive_ratio * (
        cosh_a - complex(np.exp(1.0j * charger_phase)) * sinh_a
    )
    drive_hamiltonian = (
        drive_coefficient * a + np.conj(drive_coefficient) * a_dagger
    )
    base_hamiltonian = coherent_hamiltonian + drive_hamiltonian
    detunings = torch.tensor(
        normalized_detunings,
        device=device,
        dtype=real_dtype,
    )
    hamiltonians = (
        base_hamiltonian.unsqueeze(0)
        + detunings[:, None, None] * number_a.unsqueeze(0)
    )

    local_scale = float(np.sqrt(kappa / coupling))
    collapse_operators = [local_scale * a, local_scale * b]
    collective_annihilation = squeezed_annihilation_a + b
    phase_c = torch.exp(
        torch.tensor(1.0j * reservoir_phase, device=device, dtype=dtype)
    )
    squeezed_collective = np.sqrt(2.0) * (
        float(np.cosh(squeezing)) * collective_annihilation
        - phase_c * float(np.sinh(squeezing)) * collective_annihilation.mH
    )
    collapse_operators.append(squeezed_collective)
    return hamiltonians, collapse_operators, number_b


def _rhs(
    torch: Any,
    density: Any,
    hamiltonians: Any,
    collapse_operators: list[Any],
) -> Any:
    derivative = -1.0j * (
        torch.matmul(hamiltonians, density)
        - torch.matmul(density, hamiltonians)
    )
    for collapse in collapse_operators:
        collapse_dagger = collapse.mH
        rate = collapse_dagger @ collapse
        derivative = derivative + (
            torch.matmul(torch.matmul(collapse, density), collapse_dagger)
            - 0.5
            * (
                torch.matmul(rate, density)
                + torch.matmul(density, rate)
            )
        )
    return derivative


def _simulate_cutoff(
    torch: Any,
    *,
    cutoff: int,
    normalized_detunings: tuple[float, ...],
    coupling: float,
    kappa: float,
    drive: float,
    squeezing: float,
    charger_phase: float,
    reservoir_phase: float,
    scaled_time_max: float,
    time_points: int,
    substeps_per_output: int,
    device: Any,
    dtype: Any,
) -> dict[str, Any]:
    hamiltonians, collapse_operators, number_b = _liouvillian_components(
        torch,
        cutoff=cutoff,
        normalized_detunings=normalized_detunings,
        coupling=coupling,
        kappa=kappa,
        drive=drive,
        squeezing=squeezing,
        charger_phase=charger_phase,
        reservoir_phase=reservoir_phase,
        device=device,
        dtype=dtype,
    )
    batch_size, dimension, _ = hamiltonians.shape
    density = torch.zeros(
        (batch_size, dimension, dimension),
        device=device,
        dtype=dtype,
    )
    density[:, 0, 0] = 1.0
    maximum_energy = torch.zeros(batch_size, device=device, dtype=torch.float64)
    final_energy = maximum_energy.clone()
    time_step = (
        scaled_time_max / (time_points - 1) / substeps_per_output
    )

    with torch.no_grad():
        for _ in range(1, time_points):
            for _ in range(substeps_per_output):
                k1 = _rhs(torch, density, hamiltonians, collapse_operators)
                k2 = _rhs(
                    torch,
                    density + 0.5 * time_step * k1,
                    hamiltonians,
                    collapse_operators,
                )
                k3 = _rhs(
                    torch,
                    density + 0.5 * time_step * k2,
                    hamiltonians,
                    collapse_operators,
                )
                k4 = _rhs(
                    torch,
                    density + time_step * k3,
                    hamiltonians,
                    collapse_operators,
                )
                density = density + (time_step / 6.0) * (
                    k1 + 2.0 * k2 + 2.0 * k3 + k4
                )
            final_energy = torch.real(
                torch.einsum("bij,ji->b", density, number_b)
            ).to(torch.float64)
            maximum_energy = torch.maximum(maximum_energy, final_energy)

    numerically_finite = bool(
        (
            torch.isfinite(density).all()
            & torch.isfinite(maximum_energy).all()
            & torch.isfinite(final_energy).all()
        ).cpu()
    )
    common = {
        "cutoff": cutoff,
        "coupling": coupling,
        "normalized_detunings": list(normalized_detunings),
        "integration_time_step": time_step,
    }
    if not numerically_finite:
        return {
            **common,
            "numerical_status": "non_finite",
            "maximum_energy": [None] * batch_size,
            "final_energy": [None] * batch_size,
            "trace_max_abs_error": None,
            "hermiticity_max_fro_error": None,
            "minimum_final_density_eigenvalue": None,
            "peak_normalized_detuning": None,
        }

    trace = torch.real(
        torch.diagonal(density, dim1=-2, dim2=-1).sum(dim=-1)
    ).to(torch.float64)
    hermiticity_error = torch.linalg.matrix_norm(
        density - density.mH,
        ord="fro",
        dim=(-2, -1),
    ).to(torch.float64)
    hermitian_density = 0.5 * (density + density.mH)
    minimum_eigenvalue = float(
        torch.min(torch.linalg.eigvalsh(hermitian_density)).cpu()
    )
    trace_error = float(torch.max(torch.abs(trace - 1.0)).cpu())
    hermiticity_error = float(torch.max(hermiticity_error).cpu())
    physical_invariants_hold = bool(
        trace_error <= 1e-8
        and hermiticity_error <= 1e-8
        and minimum_eigenvalue >= -1e-7
        and float(torch.min(final_energy).cpu()) >= -1e-8
        and float(torch.max(maximum_energy).cpu()) <= cutoff - 1 + 1e-7
    )
    return {
        **common,
        "numerical_status": (
            "valid" if physical_invariants_hold else "invariant_violation"
        ),
        "maximum_energy": maximum_energy.cpu().tolist(),
        "final_energy": final_energy.cpu().tolist(),
        "trace_max_abs_error": trace_error,
        "hermiticity_max_fro_error": hermiticity_error,
        "minimum_final_density_eigenvalue": minimum_eigenvalue,
        "peak_normalized_detuning": float(
            normalized_detunings[
                int(torch.argmax(maximum_energy).cpu())
            ]
        ),
    }


def _simulate_cutoff_sparse(
    *,
    cutoff: int,
    normalized_detunings: tuple[float, ...],
    coupling: float,
    kappa: float,
    drive: float,
    squeezing: float,
    charger_phase: float,
    reservoir_phase: float,
    scaled_time_max: float,
    time_points: int,
) -> dict[str, Any]:
    maximum_energies: list[float | None] = []
    final_energies: list[float | None] = []
    detuning_diagnostics: list[dict[str, Any]] = []
    trace_errors: list[float] = []
    hermiticity_errors: list[float] = []
    minimum_eigenvalues: list[float] = []
    output_time_step = scaled_time_max / (time_points - 1)

    for normalized_detuning in normalized_detunings:
        diagnostic: dict[str, Any] = {
            "normalized_detuning": normalized_detuning,
        }
        try:
            trajectory = simulate_finite_hilbert_trajectory(
                case="c",
                cutoff=cutoff,
                normalized_detuning=normalized_detuning,
                coupling=coupling,
                kappa=kappa,
                drive=drive,
                squeezing=squeezing,
                charger_phase=charger_phase,
                reservoir_phase=reservoir_phase,
                scaled_time_min=0.0,
                scaled_time_max=scaled_time_max,
                time_points=time_points,
            )
        except Exception as error:
            maximum_energies.append(None)
            final_energies.append(None)
            diagnostic.update(
                {
                    "numerical_status": "solver_error",
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
            detuning_diagnostics.append(diagnostic)
            continue

        if trajectory.numerical_status == "non_finite":
            maximum_energies.append(None)
            final_energies.append(None)
            diagnostic["numerical_status"] = "non_finite"
            detuning_diagnostics.append(diagnostic)
            continue

        maximum_energy = float(np.max(trajectory.energy))
        final_energy = float(trajectory.energy[-1])
        maximum_energies.append(maximum_energy)
        final_energies.append(final_energy)
        trace_errors.append(trajectory.trace_max_abs_error)
        hermiticity_errors.append(
            trajectory.hermiticity_final_fro_error
        )
        minimum_eigenvalues.append(
            trajectory.minimum_final_density_eigenvalue
        )
        diagnostic.update(
            {
                "generator_nonzero_entries": (
                    trajectory.generator_nonzero_entries
                ),
                "numerical_status": trajectory.numerical_status,
                "trace_max_abs_error": trajectory.trace_max_abs_error,
                "hermiticity_final_fro_error": (
                    trajectory.hermiticity_final_fro_error
                ),
                "minimum_final_density_eigenvalue": (
                    trajectory.minimum_final_density_eigenvalue
                ),
                "maximum_energy": maximum_energy,
                "final_energy": final_energy,
            }
        )
        detuning_diagnostics.append(diagnostic)

    statuses = {
        diagnostic["numerical_status"]
        for diagnostic in detuning_diagnostics
    }
    if statuses == {"valid"}:
        numerical_status = "valid"
    elif "solver_error" in statuses:
        numerical_status = "solver_error"
    elif "non_finite" in statuses:
        numerical_status = "non_finite"
    else:
        numerical_status = "invariant_violation"
    peak_detuning = None
    if numerical_status == "valid":
        peak_detuning = float(
            normalized_detunings[
                int(np.argmax(np.asarray(maximum_energies, dtype=float)))
            ]
        )

    return {
        "cutoff": cutoff,
        "coupling": coupling,
        "normalized_detunings": list(normalized_detunings),
        "solver_backend": "scipy_sparse_expm",
        "integration_time_step": None,
        "output_time_step": output_time_step,
        "numerical_status": numerical_status,
        "maximum_energy": maximum_energies,
        "final_energy": final_energies,
        "trace_max_abs_error": (
            max(trace_errors) if trace_errors else None
        ),
        "hermiticity_max_fro_error": (
            max(hermiticity_errors) if hermiticity_errors else None
        ),
        "minimum_final_density_eigenvalue": (
            min(minimum_eigenvalues) if minimum_eigenvalues else None
        ),
        "peak_normalized_detuning": peak_detuning,
        "detuning_diagnostics": detuning_diagnostics,
    }


def _terminal_hypothesis(
    results: list[dict[str, Any]],
    *,
    largest_cutoff: int,
    weak_coupling: float,
    strong_coupling: float,
) -> dict[str, Any]:
    terminal_results = {
        result["coupling"]: result
        for result in results
        if result["cutoff"] == largest_cutoff
    }
    weak_result = terminal_results.get(weak_coupling)
    strong_result = terminal_results.get(strong_coupling)
    terminal_valid = bool(
        weak_result
        and strong_result
        and weak_result["numerical_status"] == "valid"
        and strong_result["numerical_status"] == "valid"
    )
    if not terminal_valid:
        return {
            "largest_cutoff": largest_cutoff,
            "weak_peak_normalized_detuning": None,
            "strong_peak_normalized_detuning": None,
            "finite_cutoff_restores_paper_feature_contract": None,
            "assessment": "inconclusive_numerical_validation",
        }

    weak_peak = float(weak_result["peak_normalized_detuning"])
    strong_peak = float(strong_result["peak_normalized_detuning"])
    restores_contract = abs(weak_peak) <= 0.5 and abs(strong_peak) >= 0.75
    return {
        "largest_cutoff": largest_cutoff,
        "weak_peak_normalized_detuning": weak_peak,
        "strong_peak_normalized_detuning": strong_peak,
        "finite_cutoff_restores_paper_feature_contract": restores_contract,
        "assessment": "supported" if restores_contract else "rejected",
    }


def run_truncation_probe(
    config: dict[str, Any],
    *,
    backend: str = "scipy_sparse_expm",
    device_name: str = "cpu",
    grid: ProbeGrid | None = None,
) -> dict[str, Any]:
    selected_grid = grid or ProbeGrid()
    if backend == "scipy_sparse_expm":
        import scipy

        if device_name != "cpu":
            raise RuntimeError(
                "scipy_sparse_expm is a CPU backend; use --device cpu"
            )
        runtime = {
            "backend": backend,
            "requested": device_name,
            "resolved": "cpu",
            "scipy_version": scipy.__version__,
            "python": platform.python_version(),
        }
    elif backend == "torch_rk4":
        import torch

        if device_name == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable")
        device = torch.device(device_name)
        dtype = torch.complex128
        runtime = {
            "backend": backend,
            "requested": device_name,
            "resolved": str(device),
            "torch_version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "gpu_name": (
                torch.cuda.get_device_name(0)
                if torch.cuda.is_available()
                else None
            ),
            "python": platform.python_version(),
        }
    else:
        raise ValueError(f"unsupported truncation probe backend: {backend}")

    results = []
    for cutoff in selected_grid.cutoffs:
        for coupling in (float(value) for value in config["coupling_values"]):
            common_arguments = {
                "cutoff": cutoff,
                "normalized_detunings": selected_grid.normalized_detunings,
                "coupling": coupling,
                "kappa": float(config["kappa"]),
                "drive": float(config["drive"]),
                "squeezing": float(config["squeezing"]),
                "charger_phase": float(config["charger_phase"]),
                "reservoir_phase": float(config["reservoir_phase"]),
                "scaled_time_max": float(config["scaled_time_max"]),
                "time_points": int(config["time_points"]),
            }
            if backend == "scipy_sparse_expm":
                result = _simulate_cutoff_sparse(**common_arguments)
            else:
                result = _simulate_cutoff(
                    torch,
                    **common_arguments,
                    substeps_per_output=selected_grid.substeps_per_output,
                    device=device,
                    dtype=dtype,
                )
                result["solver_backend"] = backend
            results.append(result)
            print(
                f"cutoff={cutoff} coupling={coupling:g} "
                f"status={result['numerical_status']} "
                f"peak={result['peak_normalized_detuning']}",
                flush=True,
            )

    weak_coupling, strong_coupling = (
        float(value) for value in config["coupling_values"]
    )
    largest_cutoff = max(selected_grid.cutoffs)
    numerically_valid = all(
        result["numerical_status"] == "valid" for result in results
    )
    return {
        "schema_version": 1,
        "status": "completed" if numerically_valid else "invalid",
        "probe_role": "cutoff_hypothesis_test",
        "paper_id": "2607.00718",
        "target_id": "TS01",
        "solver_backend": backend,
        "device": runtime,
        "grid": {
            "cutoffs": list(selected_grid.cutoffs),
            "normalized_detunings": list(selected_grid.normalized_detunings),
            "substeps_per_output": (
                selected_grid.substeps_per_output
                if backend == "torch_rk4"
                else None
            ),
            "time_points": int(config["time_points"]),
            "scaled_time_max": float(config["scaled_time_max"]),
        },
        "results": results,
        "terminal_hypothesis": _terminal_hypothesis(
            results,
            largest_cutoff=largest_cutoff,
            weak_coupling=weak_coupling,
            strong_coupling=strong_coupling,
        ),
    }
