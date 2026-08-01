"""Finite-Hilbert Lindblad propagation for Figure S1.

The paper states that its numerical simulations use a finite-dimensional
Hilbert-space truncation but does not report the cutoff.  This module keeps that
method parameter explicit for bounded sensitivity diagnostics.  The formal
TS01 target uses the cutoff-free Gaussian propagator because a single
undisclosed cutoff cannot be justified across all four source panels.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray


BatteryCase = Literal["a", "c"]
ComplexArray = NDArray[np.complex128]
FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class FiniteHilbertTrajectory:
    energy: FloatArray
    numerical_status: str
    trace_max_abs_error: float
    hermiticity_final_fro_error: float
    minimum_final_density_eigenvalue: float
    generator_nonzero_entries: int


@dataclass(frozen=True)
class FiniteHilbertGrid:
    panels: dict[str, FloatArray]
    panel_diagnostics: dict[str, dict[str, Any]]
    numerical_status: str
    cutoff: int
    worker_count: int


@dataclass(frozen=True)
class _TrajectoryTask:
    panel_key: str
    detuning_index: int
    case: BatteryCase
    cutoff: int
    normalized_detuning: float
    coupling: float
    kappa: float
    drive: float
    squeezing: float
    charger_phase: float
    reservoir_phase: float
    scaled_time_min: float
    scaled_time_max: float
    time_points: int


def _destroy(cutoff: int) -> Any:
    from scipy import sparse

    return sparse.diags(
        np.sqrt(np.arange(1, cutoff, dtype=float)),
        offsets=1,
        shape=(cutoff, cutoff),
        dtype=np.complex128,
        format="csr",
    )


def _operators(cutoff: int) -> dict[str, Any]:
    from scipy import sparse

    identity = sparse.identity(cutoff, dtype=np.complex128, format="csr")
    local_destroy = _destroy(cutoff)
    a = sparse.kron(local_destroy, identity, format="csr")
    b = sparse.kron(identity, local_destroy, format="csr")
    a_dagger = a.getH().tocsr()
    b_dagger = b.getH().tocsr()
    return {
        "a": a,
        "a_dagger": a_dagger,
        "b": b,
        "number_a": (a_dagger @ a).tocsr(),
        "number_b": (b_dagger @ b).tocsr(),
    }


def _squeezing_by_case(
    case: BatteryCase,
    squeezing: float,
) -> tuple[float, float]:
    if case == "a":
        return squeezing, 0.0
    if case == "c":
        return squeezing, squeezing
    raise ValueError(f"finite-Hilbert TS01 supports only cases a and c: {case}")


def _liouvillian_components(
    *,
    case: BatteryCase,
    cutoff: int,
    normalized_detuning: float,
    coupling: float,
    kappa: float,
    drive: float,
    squeezing: float,
    charger_phase: float,
    reservoir_phase: float,
) -> tuple[Any, list[Any], Any]:
    operators = _operators(cutoff)
    a = operators["a"]
    a_dagger = operators["a_dagger"]
    b = operators["b"]
    number_a = operators["number_a"]
    number_b = operators["number_b"]
    charger_squeezing, reservoir_squeezing = _squeezing_by_case(
        case,
        squeezing,
    )

    cosh_a = float(np.cosh(charger_squeezing))
    sinh_a = float(np.sinh(charger_squeezing))
    phase_a = complex(np.exp(1.0j * charger_phase))
    squeezed_creation_a = cosh_a * a_dagger - phase_a * sinh_a * a
    squeezed_annihilation_a = squeezed_creation_a.getH().tocsr()
    forward = 1.0j * (squeezed_creation_a @ b)
    coherent_hamiltonian = forward + forward.getH()
    drive_coefficient = (drive / coupling) * (
        cosh_a - phase_a * sinh_a
    )
    drive_hamiltonian = (
        drive_coefficient * a + np.conj(drive_coefficient) * a_dagger
    )
    hamiltonian = (
        coherent_hamiltonian
        + drive_hamiltonian
        + normalized_detuning * number_a
    ).tocsr()

    local_scale = float(np.sqrt(kappa / coupling))
    collapse_operators = [local_scale * a, local_scale * b]
    collective_annihilation = squeezed_annihilation_a + b
    phase_c = complex(np.exp(1.0j * reservoir_phase))
    squeezed_collective = np.sqrt(2.0) * (
        float(np.cosh(reservoir_squeezing)) * collective_annihilation
        - phase_c
        * float(np.sinh(reservoir_squeezing))
        * collective_annihilation.getH()
    )
    collapse_operators.append(squeezed_collective.tocsr())
    return hamiltonian, collapse_operators, number_b


def _liouvillian(
    hamiltonian: Any,
    collapse_operators: list[Any],
) -> Any:
    """Return the Lindblad generator for column-major vectorized density."""

    from scipy import sparse

    dimension = hamiltonian.shape[0]
    identity = sparse.identity(
        dimension,
        dtype=np.complex128,
        format="csr",
    )
    generator = -1.0j * (
        sparse.kron(identity, hamiltonian, format="csr")
        - sparse.kron(hamiltonian.transpose(), identity, format="csr")
    )
    for collapse in collapse_operators:
        rate = (collapse.getH() @ collapse).tocsr()
        generator = generator + (
            sparse.kron(collapse.conjugate(), collapse, format="csr")
            - 0.5
            * (
                sparse.kron(identity, rate, format="csr")
                + sparse.kron(rate.transpose(), identity, format="csr")
            )
        )
    generator.sum_duplicates()
    generator.eliminate_zeros()
    return generator.tocsr()


def simulate_finite_hilbert_trajectory(
    *,
    case: BatteryCase,
    cutoff: int,
    normalized_detuning: float,
    coupling: float,
    kappa: float,
    drive: float,
    squeezing: float,
    charger_phase: float,
    reservoir_phase: float,
    scaled_time_min: float,
    scaled_time_max: float,
    time_points: int,
) -> FiniteHilbertTrajectory:
    """Propagate one paper-parameter trajectory and validate invariants."""

    from scipy.sparse.linalg import expm_multiply

    if cutoff < 2:
        raise ValueError("cutoff must be at least 2")
    if time_points < 2:
        raise ValueError("time_points must be at least 2")
    if scaled_time_min < 0.0 or scaled_time_max <= scaled_time_min:
        raise ValueError("scaled time must define a nonnegative interval")

    hamiltonian, collapse_operators, number_b = _liouvillian_components(
        case=case,
        cutoff=cutoff,
        normalized_detuning=normalized_detuning,
        coupling=coupling,
        kappa=kappa,
        drive=drive,
        squeezing=squeezing,
        charger_phase=charger_phase,
        reservoir_phase=reservoir_phase,
    )
    generator = _liouvillian(hamiltonian, collapse_operators)
    dimension = cutoff**2
    vector_dimension = dimension**2
    initial_density = np.zeros(vector_dimension, dtype=np.complex128)
    initial_density[0] = 1.0
    trajectory = expm_multiply(
        generator,
        initial_density,
        start=scaled_time_min,
        stop=scaled_time_max,
        num=time_points,
        endpoint=True,
        traceA=complex(generator.diagonal().sum()),
    )
    trajectory = np.asarray(trajectory, dtype=np.complex128)
    if not np.isfinite(trajectory).all():
        return FiniteHilbertTrajectory(
            energy=np.full(time_points, np.nan, dtype=float),
            numerical_status="non_finite",
            trace_max_abs_error=float("inf"),
            hermiticity_final_fro_error=float("inf"),
            minimum_final_density_eigenvalue=float("-inf"),
            generator_nonzero_entries=int(generator.nnz),
        )

    diagonal_indices = np.arange(dimension) * (dimension + 1)
    density_diagonals = trajectory[:, diagonal_indices]
    traces = density_diagonals.sum(axis=1)
    number_weights = np.asarray(number_b.diagonal()).reshape(-1)
    energy = np.asarray(
        np.real(density_diagonals @ number_weights),
        dtype=float,
    )
    final_density = trajectory[-1].reshape(
        (dimension, dimension),
        order="F",
    )
    trace_error = float(np.max(np.abs(traces - 1.0)))
    hermiticity_error = float(
        np.linalg.norm(final_density - final_density.conj().T, ord="fro")
    )
    hermitian_density = 0.5 * (final_density + final_density.conj().T)
    minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(hermitian_density)))
    invariants_hold = bool(
        trace_error <= 1e-8
        and hermiticity_error <= 1e-8
        and minimum_eigenvalue >= -1e-7
        and float(np.min(energy)) >= -1e-8
        and float(np.max(energy)) <= cutoff - 1 + 1e-7
    )
    energy[np.abs(energy) < 1e-13] = 0.0
    return FiniteHilbertTrajectory(
        energy=energy,
        numerical_status=(
            "valid" if invariants_hold else "invariant_violation"
        ),
        trace_max_abs_error=trace_error,
        hermiticity_final_fro_error=hermiticity_error,
        minimum_final_density_eigenvalue=minimum_eigenvalue,
        generator_nonzero_entries=int(generator.nnz),
    )


def _run_trajectory_task(task: _TrajectoryTask) -> dict[str, Any]:
    try:
        result = simulate_finite_hilbert_trajectory(
            case=task.case,
            cutoff=task.cutoff,
            normalized_detuning=task.normalized_detuning,
            coupling=task.coupling,
            kappa=task.kappa,
            drive=task.drive,
            squeezing=task.squeezing,
            charger_phase=task.charger_phase,
            reservoir_phase=task.reservoir_phase,
            scaled_time_min=task.scaled_time_min,
            scaled_time_max=task.scaled_time_max,
            time_points=task.time_points,
        )
        return {
            "panel_key": task.panel_key,
            "detuning_index": task.detuning_index,
            "normalized_detuning": task.normalized_detuning,
            "energy": result.energy,
            "numerical_status": result.numerical_status,
            "trace_max_abs_error": result.trace_max_abs_error,
            "hermiticity_final_fro_error": (
                result.hermiticity_final_fro_error
            ),
            "minimum_final_density_eigenvalue": (
                result.minimum_final_density_eigenvalue
            ),
            "generator_nonzero_entries": (
                result.generator_nonzero_entries
            ),
        }
    except Exception as error:
        return {
            "panel_key": task.panel_key,
            "detuning_index": task.detuning_index,
            "normalized_detuning": task.normalized_detuning,
            "energy": None,
            "numerical_status": "solver_error",
            "error_type": type(error).__name__,
            "error": str(error),
        }


def simulate_finite_hilbert_grid(
    *,
    panel_cases_and_couplings: dict[str, tuple[BatteryCase, float]],
    normalized_detunings: FloatArray,
    cutoff: int,
    kappa: float,
    drive: float,
    squeezing: float,
    charger_phase: float,
    reservoir_phase: float,
    scaled_time_min: float,
    scaled_time_max: float,
    time_points: int,
    max_workers: int = 1,
) -> FiniteHilbertGrid:
    """Propagate a group of TS01 panels with bounded local parallelism."""

    detunings = np.asarray(normalized_detunings, dtype=float).reshape(-1)
    if detunings.size == 0:
        raise ValueError("normalized_detunings must not be empty")
    tasks = [
        _TrajectoryTask(
            panel_key=panel_key,
            detuning_index=detuning_index,
            case=case,
            cutoff=cutoff,
            normalized_detuning=float(normalized_detuning),
            coupling=float(coupling),
            kappa=kappa,
            drive=drive,
            squeezing=squeezing,
            charger_phase=charger_phase,
            reservoir_phase=reservoir_phase,
            scaled_time_min=scaled_time_min,
            scaled_time_max=scaled_time_max,
            time_points=time_points,
        )
        for panel_key, (case, coupling) in panel_cases_and_couplings.items()
        for detuning_index, normalized_detuning in enumerate(detunings)
    ]
    worker_count = max(1, min(int(max_workers), len(tasks)))
    if worker_count == 1:
        task_results = [_run_trajectory_task(task) for task in tasks]
    else:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            task_results = list(
                executor.map(_run_trajectory_task, tasks, chunksize=1)
            )

    panels = {
        panel_key: np.full(
            (detunings.size, time_points),
            np.nan,
            dtype=float,
        )
        for panel_key in panel_cases_and_couplings
    }
    diagnostics_by_panel: dict[str, list[dict[str, Any]]] = {
        panel_key: [] for panel_key in panel_cases_and_couplings
    }
    for task_result in task_results:
        panel_key = str(task_result["panel_key"])
        detuning_index = int(task_result["detuning_index"])
        energy = task_result.get("energy")
        if isinstance(energy, np.ndarray):
            panels[panel_key][detuning_index] = energy
        diagnostics_by_panel[panel_key].append(task_result)

    panel_diagnostics = {
        panel_key: _summarize_panel_diagnostics(
            diagnostics,
            panels[panel_key],
        )
        for panel_key, diagnostics in diagnostics_by_panel.items()
    }
    numerically_valid = all(
        diagnostic["numerical_status"] == "valid"
        for diagnostic in panel_diagnostics.values()
    )
    return FiniteHilbertGrid(
        panels=panels,
        panel_diagnostics=panel_diagnostics,
        numerical_status="valid" if numerically_valid else "invalid",
        cutoff=cutoff,
        worker_count=worker_count,
    )


def _summarize_panel_diagnostics(
    diagnostics: list[dict[str, Any]],
    energy: FloatArray,
) -> dict[str, Any]:
    valid = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic["numerical_status"] == "valid"
    ]
    failures = [
        {
            key: value
            for key, value in diagnostic.items()
            if key not in {"energy", "panel_key"}
        }
        for diagnostic in diagnostics
        if diagnostic["numerical_status"] != "valid"
    ]
    return {
        "numerical_status": (
            "valid" if len(valid) == len(diagnostics) else "invalid"
        ),
        "trajectory_count": len(diagnostics),
        "valid_trajectory_count": len(valid),
        "trace_max_abs_error": (
            max(
                float(diagnostic["trace_max_abs_error"])
                for diagnostic in valid
            )
            if valid
            else None
        ),
        "hermiticity_max_fro_error": (
            max(
                float(diagnostic["hermiticity_final_fro_error"])
                for diagnostic in valid
            )
            if valid
            else None
        ),
        "minimum_final_density_eigenvalue": (
            min(
                float(diagnostic["minimum_final_density_eigenvalue"])
                for diagnostic in valid
            )
            if valid
            else None
        ),
        "generator_nonzero_entries": (
            sorted(
                {
                    int(diagnostic["generator_nonzero_entries"])
                    for diagnostic in valid
                }
            )
            if valid
            else []
        ),
        "energy_minimum": (
            float(np.nanmin(energy)) if np.isfinite(energy).any() else None
        ),
        "energy_maximum": (
            float(np.nanmax(energy)) if np.isfinite(energy).any() else None
        ),
        "failures": failures[:5],
    }
