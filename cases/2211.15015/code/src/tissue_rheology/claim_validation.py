"""Independent numerical checks for the paper's no-display validation claims."""

from __future__ import annotations

from typing import Any

import numpy as np

from .geometry import polygon_observables
from .model import VertexTissue


def area_force_factor_check(spec: dict[str, Any]) -> dict[str, float | bool]:
    """Compare the exact area derivative with finite differences and the prose form."""

    rng = np.random.default_rng(int(spec["seed"]))
    vertex_count = int(spec["vertex_count"])
    angles = np.sort(rng.uniform(0.0, 2.0 * np.pi, size=vertex_count))
    radii = rng.uniform(float(spec["radius_min"]), float(spec["radius_max"]), vertex_count)
    vertices = np.column_stack([radii * np.cos(angles), radii * np.sin(angles)])
    observable = polygon_observables(vertices)
    target_area = float(spec["target_area_fraction"]) * observable.area
    coefficient = float(spec["kappa_area"]) * (observable.area - target_area)
    exact_gradient = coefficient * observable.grad_area

    def area_energy(points: np.ndarray) -> float:
        area = polygon_observables(points).area
        return 0.5 * float(spec["kappa_area"]) * (area - target_area) ** 2

    step = float(spec["finite_difference_step"])
    finite_difference = np.zeros_like(vertices)
    for vertex in range(vertex_count):
        for coordinate in range(2):
            plus = vertices.copy()
            minus = vertices.copy()
            plus[vertex, coordinate] += step
            minus[vertex, coordinate] -= step
            finite_difference[vertex, coordinate] = (
                area_energy(plus) - area_energy(minus)
            ) / (2.0 * step)

    prose_without_half = 2.0 * exact_gradient
    denominator = max(float(np.linalg.norm(exact_gradient)), 1e-30)
    finite_difference_error = float(
        np.linalg.norm(exact_gradient - finite_difference) / denominator
    )
    prose_error = float(
        np.linalg.norm(prose_without_half - finite_difference) / denominator
    )
    return {
        "finite_difference_relative_error": finite_difference_error,
        "prose_without_half_relative_error": prose_error,
        "prose_to_exact_norm_ratio": float(
            np.linalg.norm(prose_without_half) / denominator
        ),
        "exact_derivative_supported": finite_difference_error
        <= float(spec["relative_tolerance"]),
        "factor_two_discrepancy_detected": abs(
            float(np.linalg.norm(prose_without_half) / denominator) - 2.0
        )
        <= float(spec["factor_tolerance"]),
    }


def gradient_sign_check(spec: dict[str, Any]) -> dict[str, float | bool]:
    """Discriminate the energy gradient from the physical negative-gradient force."""

    tissue = VertexTissue.initialize(
        nx=int(spec["nx"]),
        ny=int(spec["ny"]),
        p0=float(spec["p0"]),
        seed=int(spec["seed"]),
    )
    initial_energy = tissue.elastic_energy()
    force, _, _ = tissue.elastic_forces()
    inverse = np.linalg.inv(tissue.lattice)
    step = float(spec["descent_step"])

    along_force = tissue.copy()
    along_force.fractional = np.mod(
        along_force.fractional + (inverse @ (step * force).T).T,
        1.0,
    )
    against_force = tissue.copy()
    against_force.fractional = np.mod(
        against_force.fractional - (inverse @ (step * force).T).T,
        1.0,
    )
    force_energy = along_force.elastic_energy()
    gradient_energy = against_force.elastic_energy()
    return {
        "initial_energy": initial_energy,
        "negative_gradient_step_energy": force_energy,
        "positive_gradient_step_energy": gradient_energy,
        "negative_gradient_descends": force_energy < initial_energy,
        "positive_gradient_ascends": gradient_energy > initial_energy,
    }


def time_step_scan(spec: dict[str, Any]) -> list[dict[str, float | int]]:
    """Run a matched deterministic refinement scan around the printed dt."""

    rows: list[dict[str, float | int]] = []
    seeds = [int(value) for value in spec.get("seeds", [spec["seed"]])]
    dt_values = [float(value) for value in spec["dt_values"]]
    for seed in seeds:
        seed_rows: list[dict[str, float | int]] = []
        for dt in dt_values:
            tissue = VertexTissue.initialize(
                nx=int(spec["nx"]),
                ny=int(spec["ny"]),
                p0=float(spec["p0"]),
                seed=seed,
                rotational_diffusion=0.0,
            )
            steps = int(round(float(spec["physical_time"]) / dt))
            result = tissue.run(
                steps=steps,
                activity=float(spec["activity"]),
                shear_rate=float(spec["shear_rate"]),
                dt=dt,
                sample_every=max(1, steps),
                enable_t1=bool(spec["enable_t1"]),
                max_nonaffine_displacement=float(spec["max_nonaffine_displacement"]),
            )
            seed_rows.append(
                {
                    "seed": seed,
                    "dt": dt,
                    "steps": steps,
                    "final_energy": float(result["energy"][-1]),
                    "final_shear_stress": float(result["stress"][-1]),
                    "final_strain": float(result["strain"][-1]),
                }
            )
        finest = min(seed_rows, key=lambda row: float(row["dt"]))
        for row in seed_rows:
            row["energy_relative_to_finest"] = abs(
                float(row["final_energy"]) - float(finest["final_energy"])
            ) / max(abs(float(finest["final_energy"])), 1e-30)
            row["stress_relative_to_finest"] = abs(
                float(row["final_shear_stress"])
                - float(finest["final_shear_stress"])
            ) / max(abs(float(finest["final_shear_stress"])), 1e-30)
        rows.extend(seed_rows)
    return rows


def finite_size_scan(spec: dict[str, Any]) -> list[dict[str, float | int]]:
    """Run the declared N=64/100/144 finite-size protocol from clean initial states."""

    rows: list[dict[str, float | int]] = []
    dt = float(spec["dt"])
    steps = int(round(float(spec["physical_time"]) / dt))
    seeds = [int(value) for value in spec.get("seeds", [spec["seed"]])]
    for seed in seeds:
        for nx, ny in spec["grid_sizes"]:
            tissue = VertexTissue.initialize(
                nx=int(nx),
                ny=int(ny),
                p0=float(spec["p0"]),
                seed=seed,
                rotational_diffusion=0.0,
            )
            result = tissue.run(
                steps=steps,
                activity=float(spec["activity"]),
                shear_rate=float(spec["shear_rate"]),
                dt=dt,
                sample_every=max(1, steps),
                enable_t1=bool(spec["enable_t1"]),
                max_nonaffine_displacement=float(spec["max_nonaffine_displacement"]),
            )
            tensors, _, _ = tissue.cell_stress_tensors()
            cell_stress = np.abs(tensors[:, 0, 1])
            rows.append(
                {
                    "seed": seed,
                    "nx": int(nx),
                    "ny": int(ny),
                    "cell_count": int(tissue.cell_count),
                    "steps": steps,
                    "final_energy_per_cell": tissue.elastic_energy()
                    / tissue.cell_count,
                    "final_shear_stress": float(result["stress"][-1]),
                    "cell_stress_std": float(np.std(cell_stress)),
                    "cell_stress_sem": float(
                        np.std(cell_stress) / np.sqrt(tissue.cell_count)
                    ),
                }
            )
    return rows


def time_step_convergence_summary(
    rows: list[dict[str, float | int]], spec: dict[str, Any]
) -> dict[str, float | int | bool]:
    """Adjudicate the printed dt against a finer-grid, multi-seed reference."""

    paper_dt = float(spec["paper_dt"])
    paper_rows = [row for row in rows if np.isclose(float(row["dt"]), paper_dt)]
    if not paper_rows:
        raise ValueError("time-step scan does not contain paper_dt")
    energy_error = max(float(row["energy_relative_to_finest"]) for row in paper_rows)
    stress_error = max(float(row["stress_relative_to_finest"]) for row in paper_rows)
    energy_tolerance = float(spec["energy_relative_tolerance"])
    stress_tolerance = float(spec["stress_relative_tolerance"])
    return {
        "seeds_total": len({int(row["seed"]) for row in rows}),
        "paper_dt": paper_dt,
        "finest_dt": min(float(row["dt"]) for row in rows),
        "max_energy_relative_to_finest": energy_error,
        "max_stress_relative_to_finest": stress_error,
        "energy_relative_tolerance": energy_tolerance,
        "stress_relative_tolerance": stress_tolerance,
        "passed": energy_error <= energy_tolerance
        and stress_error <= stress_tolerance,
    }


def finite_size_convergence_summary(
    rows: list[dict[str, float | int]], spec: dict[str, Any]
) -> dict[str, float | int | bool]:
    """Test N=100 against the larger N=144 branch and fluctuation scaling."""

    counts = sorted({int(row["cell_count"]) for row in rows})
    paper_count = int(spec["paper_cell_count"])
    larger = [value for value in counts if value > paper_count]
    if paper_count not in counts or not larger:
        raise ValueError("finite-size scan must contain paper N and a larger N")
    comparison_count = min(larger)

    def mean_for(count: int, key: str) -> float:
        values = [float(row[key]) for row in rows if int(row["cell_count"]) == count]
        return float(np.mean(values))

    paper_energy = mean_for(paper_count, "final_energy_per_cell")
    larger_energy = mean_for(comparison_count, "final_energy_per_cell")
    paper_stress = mean_for(paper_count, "final_shear_stress")
    larger_stress = mean_for(comparison_count, "final_shear_stress")
    energy_error = abs(paper_energy - larger_energy) / max(abs(larger_energy), 1e-30)
    stress_error = abs(paper_stress - larger_stress) / max(abs(larger_stress), 1e-30)
    sem_values = [mean_for(count, "cell_stress_sem") for count in counts]
    sem_monotonic = all(
        later < earlier for earlier, later in zip(sem_values, sem_values[1:])
    )
    energy_tolerance = float(spec["energy_relative_tolerance"])
    stress_tolerance = float(spec["stress_relative_tolerance"])
    return {
        "seeds_total": len({int(row["seed"]) for row in rows}),
        "paper_cell_count": paper_count,
        "comparison_cell_count": comparison_count,
        "paper_energy_per_cell_mean": paper_energy,
        "comparison_energy_per_cell_mean": larger_energy,
        "paper_stress_mean": paper_stress,
        "comparison_stress_mean": larger_stress,
        "energy_relative_difference": energy_error,
        "stress_relative_difference": stress_error,
        "energy_relative_tolerance": energy_tolerance,
        "stress_relative_tolerance": stress_tolerance,
        "cell_stress_sem_monotonic_decrease": sem_monotonic,
        "passed": energy_error <= energy_tolerance
        and stress_error <= stress_tolerance
        and sem_monotonic,
    }
