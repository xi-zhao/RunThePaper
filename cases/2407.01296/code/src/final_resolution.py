"""Independent scientific closure for the unresolved 2407.01296 items.

The runner in this module is deliberately clean-room.  It accepts only a
paper-transcribed JSON configuration and implements the printed Hamiltonians
and formulas through the case-local scientific modules.  It never reads the
paper PDF, source images, author release, author arrays, or legacy outputs.

The functions are split by atomic scientific object so an omitted publication
detail in one panel cannot block a different, fully specified panel.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

import numpy as np
from scipy import optimize

from src.gbz import solve_gbz_for_energy
from src.geometry_adaptive import (
    aggregate_right_density,
    amoeba_potential,
    build_obc_hamiltonian,
    cylindrical_root_potential,
    density_metrics,
    diamond_sites,
    eigensystem_residuals,
    full_right_eigensystem,
    full_spectrum,
    geometry_adaptive_potential,
    minimize_cylindrical_potential,
    model_eq11,
    model_eq15,
    reflection_symmetrized_density,
    rhombus_localization_metrics,
    spectral_density_from_potential,
    spectral_potential_grid,
    square_sites,
    symmetric_cloud_distance,
)
from src.supplemental_campaign import (
    biorthogonal_first_order_disorder,
    directional_winding_rows,
    s24_hamiltonian,
    s24_state_profiles,
)


HoppingModel = dict[tuple[int, int], complex]


def _json_default(value: Any) -> Any:
    """Convert NumPy scalar/array results at the output boundary."""

    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
            default=_json_default,
        )
        + "\n",
        encoding="utf-8",
    )


def _complex_pairs(values: np.ndarray) -> list[list[float]]:
    flat = np.asarray(values, dtype=np.complex128).reshape(-1)
    return [[float(value.real), float(value.imag)] for value in flat]


def _farthest_point_sample(values: np.ndarray, count: int) -> np.ndarray:
    """Deterministically cover a complex cloud without a source-figure input."""

    values = np.asarray(values, dtype=np.complex128).reshape(-1)
    if len(values) <= count:
        return values.copy()
    points = np.column_stack((values.real, values.imag))
    scale = np.ptp(points, axis=0)
    scale[scale == 0.0] = 1.0
    normalized = (points - points.mean(axis=0)) / scale
    selected = [int(np.argmax(np.linalg.norm(normalized, axis=1)))]
    minimum_distance = np.full(len(values), np.inf)
    for _ in range(1, count):
        latest = normalized[selected[-1]]
        minimum_distance = np.minimum(
            minimum_distance,
            np.sum((normalized - latest) ** 2, axis=1),
        )
        minimum_distance[selected] = -1.0
        selected.append(int(np.argmax(minimum_distance)))
    return values[np.asarray(selected)]


def _geometry_eigensystem(
    sites: tuple[tuple[int, int], ...], hoppings: HoppingModel
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    matrix = build_obc_hamiltonian(sites, hoppings)
    started = time.perf_counter()
    eigensystem = full_right_eigensystem(matrix)
    density = aggregate_right_density(eigensystem.right_eigenvectors)
    residuals = eigensystem_residuals(matrix, eigensystem, batch_size=128)
    return eigensystem.eigenvalues, density, residuals, time.perf_counter() - started


def _geometry_potential_grid(
    hoppings: HoppingModel,
    basis: str,
    real_axis: np.ndarray,
    imaginary_axis: np.ndarray,
    *,
    momentum_samples: int,
    tolerance: float,
) -> tuple[np.ndarray, np.ndarray, int, float]:
    potential = np.empty((len(imaginary_axis), len(real_axis)), dtype=np.float64)
    evaluations = 0
    started = time.perf_counter()
    for row, imaginary in enumerate(imaginary_axis):
        for column, real in enumerate(real_axis):
            result = geometry_adaptive_potential(
                complex(real, imaginary),
                hoppings,
                basis=basis,
                momentum_samples=momentum_samples,
                tolerance=tolerance,
            )
            potential[row, column] = result.potential
            evaluations += result.cylinder_1.evaluations + result.cylinder_2.evaluations
        if row % max(1, len(imaginary_axis) // 10) == 0:
            print(f"potential {basis}: row {row + 1}/{len(imaginary_axis)}", flush=True)
    density = spectral_density_from_potential(
        potential,
        real_step=float(real_axis[1] - real_axis[0]),
        imaginary_step=float(imaginary_axis[1] - imaginary_axis[0]),
    )
    return potential, density, evaluations, time.perf_counter() - started


def run_t001(
    profile: dict[str, Any], output_root: Path
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Paper-size Fig. 2(a-c) from Eq. (11), with no legacy array input."""

    square = square_sites(int(profile["square_length"]))
    rhombus = diamond_sites(int(profile["rhombus_radius"]))
    spectra: dict[str, np.ndarray] = {}
    arrays: dict[str, np.ndarray] = {}
    rows: dict[str, Any] = {}
    for label, sites in (("square", square), ("rhombus", rhombus)):
        print(f"T001 {label}: diagonalizing {len(sites)} sites", flush=True)
        eigenvalues, density, residuals, runtime = _geometry_eigensystem(
            sites, model_eq11()
        )
        spectra[label] = eigenvalues
        arrays[f"{label}_coordinates"] = np.asarray(sites, dtype=np.int64)
        arrays[f"{label}_spectrum"] = eigenvalues
        arrays[f"{label}_density"] = density
        arrays[f"{label}_residuals"] = residuals
        rows[label] = {
            "site_count": len(sites),
            "runtime_seconds": runtime,
            "density_sum": float(density.sum()),
            "density_metrics": density_metrics(sites, density),
            "maximum_eigenpair_residual": float(np.max(residuals)),
        }

    real_axis = np.linspace(
        float(profile["potential_real_range"][0]),
        float(profile["potential_real_range"][1]),
        int(profile["potential_points"]),
    )
    imaginary_axis = np.linspace(
        float(profile["potential_imaginary_range"][0]),
        float(profile["potential_imaginary_range"][1]),
        int(profile["potential_points"]),
    )
    probes = real_axis[None, :] + 1j * imaginary_axis[:, None]
    for label in ("square", "rhombus"):
        potential, density, evaluations, runtime = _geometry_potential_grid(
            model_eq11(),
            label,
            real_axis,
            imaginary_axis,
            momentum_samples=int(profile["potential_momentum_samples"]),
            tolerance=float(profile["potential_tolerance"]),
        )
        finite_potential = spectral_potential_grid(spectra[label], probes)
        absolute_error = np.abs(potential - finite_potential)
        arrays[f"{label}_potential"] = potential
        arrays[f"{label}_spectral_density"] = density
        arrays[f"{label}_finite_potential"] = finite_potential
        rows[label]["potential"] = {
            "runtime_seconds": runtime,
            "objective_evaluations": evaluations,
            "mean_absolute_finite_size_error": float(np.mean(absolute_error)),
            "median_absolute_finite_size_error": float(np.median(absolute_error)),
            "maximum_absolute_finite_size_error": float(np.max(absolute_error)),
            "finite": bool(np.all(np.isfinite(potential)) and np.all(np.isfinite(density))),
        }
    arrays["real_axis"] = real_axis
    arrays["imaginary_axis"] = imaginary_axis
    cloud_distance = symmetric_cloud_distance(spectra["square"], spectra["rhombus"])
    acceptance = {
        "paper_site_counts_exact": len(square) == 1600 and len(rhombus) == 1861,
        "all_eigenpair_residuals_below_1e_10": all(
            rows[label]["maximum_eigenpair_residual"] < 1e-10
            for label in rows
        ),
        "complete_normalized_eigenbases": all(
            abs(rows[label]["density_sum"] - rows[label]["site_count"]) < 1e-8
            for label in rows
        ),
        "geometry_changes_spectrum": cloud_distance["mean"] > 0.02,
        "paper_grid_potentials_finite": all(rows[label]["potential"]["finite"] for label in rows),
        "finite_size_potential_mean_error_below_0_02": all(
            rows[label]["potential"]["mean_absolute_finite_size_error"] < 0.02
            for label in rows
        ),
    }
    payload = {
        "schema_version": 1,
        "target_id": "T001",
        "scientific_scale": "paper_exact",
        "method": "Eq. (11) OBC eigensystems plus Eqs. (8)-(10) hierarchical potential",
        "numerical_input_boundary": "paper formulas and frozen config only",
        "geometries": rows,
        "geometry_cloud_distance": cloud_distance,
        "arrays": "T001_paper_arrays.npz",
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }
    return payload, arrays


def run_t002a(
    profile: dict[str, Any], output_root: Path
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Paper-size Fig. 4(a) aggregate critical-skin density."""

    radius = int(profile["critical_density_radius"])
    sites = diamond_sites(radius)
    print(f"T002-A: diagonalizing {len(sites)} sites", flush=True)
    eigenvalues, raw_density, residuals, runtime = _geometry_eigensystem(
        sites, model_eq15()
    )
    symmetric_density = reflection_symmetrized_density(sites, raw_density)
    localization = rhombus_localization_metrics(sites, symmetric_density)
    acceptance = {
        "paper_site_count_exact": len(sites) == int(profile["critical_density_site_count"]),
        "complete_normalized_eigenbasis": abs(float(raw_density.sum()) - len(sites)) < 1e-8,
        "all_eigenpair_residuals_below_1e_10": float(np.max(residuals)) < 1e-10,
        "boundary_enrichment_above_two": float(localization["boundary_enrichment"]) > 2.0,
        "edge_not_corner_dominated": float(localization["corner_fraction_of_boundary_mass"]) < 0.1,
    }
    payload = {
        "schema_version": 1,
        "target_id": "T002-A",
        "scientific_scale": "paper_exact",
        "method": "complete right eigensystem of Eq. (15) on the N=6385 rhombus",
        "site_count": len(sites),
        "runtime_seconds": runtime,
        "maximum_eigenpair_residual": float(np.max(residuals)),
        "localization": localization,
        "arrays": "T002A_paper_arrays.npz",
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }
    arrays = {
        "coordinates": np.asarray(sites, dtype=np.int64),
        "spectrum": eigenvalues,
        "raw_density": raw_density,
        "reflection_symmetrized_density": symmetric_density,
        "residuals": residuals,
    }
    return payload, arrays


def _negative_density_mass_ratio(density: np.ndarray) -> float:
    total = float(np.sum(np.abs(density)))
    return 0.0 if total == 0.0 else float(np.sum(np.abs(np.minimum(density, 0.0))) / total)


def run_t002c(
    profile: dict[str, Any], output_root: Path
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Formula-defined Fig. 4(c) spectral density for Eq. (15)."""

    real_axis = np.linspace(*map(float, profile["critical_density_real_range"]), int(profile["critical_density_real_points"]))
    imaginary_axis = np.linspace(*map(float, profile["critical_density_imaginary_range"]), int(profile["critical_density_imaginary_points"]))
    potential, density, evaluations, runtime = _geometry_potential_grid(
        model_eq15(),
        "rhombus",
        real_axis,
        imaginary_axis,
        momentum_samples=int(profile["critical_density_momentum_samples"]),
        tolerance=float(profile["critical_density_tolerance"]),
    )
    symmetry_error = float(np.mean(np.abs(density - density[::-1, :])))
    negative_ratio = _negative_density_mass_ratio(density)
    support = np.argwhere(np.clip(density, 0.0, None) > np.quantile(np.clip(density, 0.0, None), 0.75))
    acceptance = {
        "potential_and_density_finite": bool(np.all(np.isfinite(potential)) and np.all(np.isfinite(density))),
        "conjugation_symmetry_mean_error_below_0_02": symmetry_error < 0.02,
        "negative_density_mass_ratio_below_0_06": negative_ratio < 0.06,
        "two_dimensional_support_resolved": bool(len(support) > 10 and np.ptp(support[:, 0]) > 2 and np.ptp(support[:, 1]) > 2),
    }
    payload = {
        "schema_version": 1,
        "target_id": "T002-C",
        "scientific_scale": "paper_formula_grid",
        "method": "Eqs. (8)-(10) applied to Eq. (15) in the rhombus basis",
        "runtime_seconds": runtime,
        "objective_evaluations": evaluations,
        "conjugation_symmetry_mean_error": symmetry_error,
        "negative_density_mass_ratio": negative_ratio,
        "arrays": "T002C_formula_arrays.npz",
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }
    return payload, {"real_axis": real_axis, "imaginary_axis": imaginary_axis, "potential": potential, "density": density}


def run_t003(
    profile: dict[str, Any], spectra: dict[str, np.ndarray]
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Supplement Note 3 GBZ solve over an independent OBC energy cover."""

    arrays: dict[str, np.ndarray] = {}
    rows: dict[str, Any] = {}
    all_passed = True
    for basis in ("square", "rhombus"):
        energies = _farthest_point_sample(spectra[basis], int(profile["gbz_energy_count"]))
        point_rows: list[tuple[float, ...]] = []
        started = time.perf_counter()
        for index, energy in enumerate(energies):
            for point in solve_gbz_for_energy(
                complex(energy),
                model_eq11(),
                basis=basis,
                momentum_samples=int(profile["gbz_momentum_samples"]),
                minimization_tolerance=float(profile["gbz_minimizer_tolerance"]),
                seed_count=int(profile["gbz_seed_count"]),
            ):
                point_rows.append(
                    (
                        point.energy.real,
                        point.energy.imag,
                        point.mu_1,
                        point.mu_2,
                        point.k_1,
                        point.k_2,
                        point.residual,
                    )
                )
            if index % max(1, len(energies) // 8) == 0:
                print(f"T003 {basis}: energy {index + 1}/{len(energies)}", flush=True)
        points = np.asarray(point_rows, dtype=np.float64)
        if points.size == 0:
            points = np.empty((0, 7), dtype=np.float64)
        arrays[f"{basis}_energies"] = energies
        arrays[f"{basis}_points"] = points
        residual_max = float(np.max(points[:, 6])) if len(points) else float("inf")
        mu_1_std = float(np.std(points[:, 2])) if len(points) else float("inf")
        rows[basis] = {
            "energy_count": len(energies),
            "gbz_point_count": len(points),
            "runtime_seconds": time.perf_counter() - started,
            "characteristic_residual_max": residual_max,
            "mu_1_standard_deviation": mu_1_std,
            "mu_1_positive_fraction": float(np.mean(points[:, 2] > 0.0)) if len(points) else 0.0,
            "mu_2_negative_fraction": float(np.mean(points[:, 3] < 0.0)) if len(points) else 0.0,
        }
        all_passed &= bool(len(points) and residual_max <= float(profile["gbz_residual_gate"]))
    acceptance = {
        "both_geometry_energy_covers_complete": all(rows[basis]["energy_count"] == int(profile["gbz_energy_count"]) for basis in rows),
        "all_characteristic_residuals_pass": all_passed,
        "localization_signs_match": all(rows[basis]["mu_1_positive_fraction"] > 0.99 and rows[basis]["mu_2_negative_fraction"] > 0.99 for basis in rows),
        "rhombus_mu1_is_flatter_than_square": rows["rhombus"]["mu_1_standard_deviation"] < 0.1 * rows["square"]["mu_1_standard_deviation"],
    }
    return {
        "schema_version": 1,
        "target_id": "T003",
        "scientific_scale": "paper_model_independent_energy_cover",
        "method": "Supplement Note 3 Eqs. (S9)-(S11)",
        "energy_sampling": "deterministic farthest-point cover of independently generated OBC spectra",
        "rows": rows,
        "arrays": "T003_gbz_arrays.npz",
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }, arrays


def _fit_symmetric_exponential_density(density: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(density, dtype=np.float64).reshape(-1)
    symmetric = 0.5 * (values + values[::-1])
    half = len(values) // 2
    distance = np.arange(half + 1, dtype=np.float64)
    normalized = symmetric[: half + 1] / symmetric[0]
    mask = (distance > 0.0) & (normalized > 1e-7)
    slope, intercept = np.polyfit(distance[mask], np.log(normalized[mask]), 1)
    prediction = slope * distance[mask] + intercept
    response = np.log(normalized[mask])
    residual_sum = float(np.sum((response - prediction) ** 2))
    total_sum = float(np.sum((response - response.mean()) ** 2))
    return {
        "amplitude_kappa": float(-0.5 * slope),
        "density_log_slope": float(slope),
        "intercept": float(intercept),
        "r_squared": 1.0 - residual_sum / total_sum,
        "fit_points": int(np.count_nonzero(mask)),
    }


def run_t010(
    profile: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Complete the missing S4 TDL curve and kappa-versus-1/L series."""

    lengths = [int(value) for value in profile["s4_lengths"]]
    arrays: dict[str, np.ndarray] = {}
    rows: list[dict[str, Any]] = []
    for length in lengths:
        values = full_spectrum(s24_hamiltonian(length, delta=float(profile["s4_delta"])))
        states = s24_state_profiles(length, delta=float(profile["s4_delta"]))
        density = np.asarray(states["largest_imaginary_density"], dtype=np.float64)
        fit = _fit_symmetric_exponential_density(density)
        arrays[f"spectrum_L{length}"] = values
        arrays[f"central_density_L{length}"] = density
        rows.append({"length": length, "inverse_length": 1.0 / length, **fit})
    inverse = np.asarray([row["inverse_length"] for row in rows], dtype=np.float64)
    kappa = np.asarray([row["amplitude_kappa"] for row in rows], dtype=np.float64)
    slope, intercept = np.polyfit(inverse, kappa, 1)
    prediction = slope * inverse + intercept
    r_squared = 1.0 - float(np.sum((kappa - prediction) ** 2)) / float(np.sum((kappa - kappa.mean()) ** 2))

    tdl_lengths = [int(value) for value in profile["s4_tdl_lengths"]]
    tdl_spectra = [full_spectrum(s24_hamiltonian(length, delta=float(profile["s4_delta"]))) for length in tdl_lengths]
    for length, values in zip(tdl_lengths, tdl_spectra, strict=True):
        arrays[f"tdl_spectrum_L{length}"] = values
    tdl_distance = symmetric_cloud_distance(tdl_spectra[0], tdl_spectra[1])
    acceptance = {
        "printed_lengths_complete": lengths == [20, 40, 60, 80],
        "all_profile_fits_r2_above_0_85": all(float(row["r_squared"]) > 0.85 for row in rows),
        "kappa_linear_in_inverse_length": r_squared > 0.98,
        "positive_c0_and_c1": intercept > 0.0 and slope > 0.0,
        "tdl_refinement_distance_finite": np.isfinite(tdl_distance["p95"]),
    }
    return {
        "schema_version": 1,
        "target_id": "T010",
        "scientific_scale": "paper_lengths_plus_independent_tdl_refinement",
        "method": "Eq. (S24) exact diagonalization and Eq. (S25) amplitude fit",
        "profile_rows": rows,
        "kappa_fit": {"c0": float(intercept), "c1": float(slope), "r_squared": r_squared},
        "tdl_lengths": tdl_lengths,
        "tdl_successive_cloud_distance": tdl_distance,
        "arrays": "T010_s4_arrays.npz",
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }, arrays


def _periodic_distance(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.linalg.norm(np.angle(np.exp(1.0j * (first - second)))))


def _bloch_scalar(hoppings: HoppingModel, kx: float, ky: float) -> complex:
    return complex(sum(value * np.exp(1j * (dx * kx + dy * ky)) for (dx, dy), value in hoppings.items()))


def _fermi_points(hoppings: HoppingModel, seed_points: int = 17) -> list[dict[str, float | int]]:
    roots: list[np.ndarray] = []
    seeds = np.linspace(-np.pi, np.pi, seed_points, endpoint=False)
    for kx in seeds:
        for ky in seeds:
            result = optimize.root(
                lambda value: np.asarray(
                    (
                        _bloch_scalar(hoppings, float(value[0]), float(value[1])).real,
                        _bloch_scalar(hoppings, float(value[0]), float(value[1])).imag,
                    )
                ),
                np.asarray((kx, ky)),
            )
            if not result.success or np.linalg.norm(result.fun) > 1e-9:
                continue
            folded = (np.asarray(result.x) + np.pi) % (2.0 * np.pi) - np.pi
            if not any(_periodic_distance(folded, root) < 1e-6 for root in roots):
                roots.append(folded)
    rows: list[dict[str, float | int]] = []
    step = 1e-5
    for kx, ky in roots:
        d_kx = (_bloch_scalar(hoppings, kx + step, ky) - _bloch_scalar(hoppings, kx - step, ky)) / (2.0 * step)
        d_ky = (_bloch_scalar(hoppings, kx, ky + step) - _bloch_scalar(hoppings, kx, ky - step)) / (2.0 * step)
        jacobian = d_kx.real * d_ky.imag - d_ky.real * d_kx.imag
        rows.append(
            {
                "kx": float(kx),
                "ky": float(ky),
                "residual": float(abs(_bloch_scalar(hoppings, kx, ky))),
                "jacobian": float(jacobian),
                "charge": int(np.sign(jacobian)),
            }
        )
    return sorted(rows, key=lambda row: (float(row["kx"]), float(row["ky"])))


def run_t011(profile: dict[str, Any]) -> dict[str, Any]:
    """Locate both charge signs and connect them to the two winding maps."""

    normal_points = _fermi_points(model_eq11(), int(profile["fermi_seed_points"]))
    critical_points = _fermi_points(model_eq15(), int(profile["fermi_seed_points"]))
    normal_winding = directional_winding_rows(
        model_eq11(),
        basis="square_y",
        transverse_points=int(profile["winding_transverse_points"]),
        path_points=int(profile["winding_path_points"]),
    )
    critical_winding = directional_winding_rows(
        model_eq15(),
        basis="diagonal_1m1",
        transverse_points=int(profile["winding_transverse_points"]),
        path_points=int(profile["winding_path_points"]),
    )
    normal_sectors = sorted({int(row["winding"]) for row in normal_winding})
    critical_sectors = sorted({int(row["winding"]) for row in critical_winding})
    acceptance = {
        "normal_has_both_fermi_charge_signs": {int(row["charge"]) for row in normal_points} == {-1, 1},
        "critical_has_four_analytic_fermi_points": len(critical_points) == 4,
        "critical_has_both_fermi_charge_signs": {int(row["charge"]) for row in critical_points} == {-1, 1},
        "all_fermi_residuals_below_1e_8": max(float(row["residual"]) for row in normal_points + critical_points) < 1e-8,
        "normal_winding_is_sign_consistent": set(normal_sectors).issubset({0, 1}) or set(normal_sectors).issubset({-1, 0}),
        "critical_winding_changes_sign": {-1, 1}.issubset(set(critical_sectors)),
    }
    return {
        "schema_version": 1,
        "target_id": "T011",
        "scientific_scale": "paper_exact_equations",
        "method": "Eq. (S28) directional winding and Jacobian charge of H(k)=0",
        "normal_fermi_points": normal_points,
        "critical_fermi_points": critical_points,
        "normal_winding_sectors": normal_sectors,
        "critical_winding_sectors": critical_sectors,
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }


def run_t009(profile: dict[str, Any]) -> dict[str, Any]:
    """Literal Eq. (S29) check against the exact trace identity."""

    rng = np.random.default_rng(int(profile["seed"]))
    rows: list[dict[str, Any]] = []
    geometries = (
        ("normal", square_sites(int(profile["s29_square_length"])), model_eq11()),
        ("critical", diamond_sites(int(profile["s29_rhombus_radius"])), model_eq15()),
    )
    for label, sites, hoppings in geometries:
        matrix = build_obc_hamiltonian(sites, hoppings)
        for delta in map(float, profile["s29_disorder_strengths"]):
            disorder = rng.uniform(0.0, delta, len(sites))
            literal = biorthogonal_first_order_disorder(matrix, [disorder])[0]
            trace_mean = float(np.mean(disorder))
            literal_complex = complex(literal["mean_shift_real"], literal["mean_shift_imag"])
            rows.append(
                {
                    "geometry": label,
                    "site_count": len(sites),
                    "delta": delta,
                    "literal_mean_shift": [literal_complex.real, literal_complex.imag],
                    "trace_over_n": trace_mean,
                    "absolute_identity_error": float(abs(literal_complex - trace_mean)),
                    "within_uniform_support_bound": bool(-1e-12 <= literal_complex.real <= delta + 1e-12),
                }
            )
    acceptance = {
        "literal_formula_equals_trace_over_n": max(row["absolute_identity_error"] for row in rows) < 1e-10,
        "all_literal_means_lie_between_zero_and_delta": all(row["within_uniform_support_bound"] for row in rows),
        "normal_and_critical_use_same_identity": {row["geometry"] for row in rows} == {"normal", "critical"},
    }
    return {
        "schema_version": 1,
        "target_id": "T009",
        "scientific_scale": "literal_formula_discriminating_check",
        "method": "biorthogonal completeness: N^-1 sum_i <L_i|V|R_i>/<L_i|R_i> = Tr(V)/N",
        "rows": rows,
        "publication_implication": "For delta_j in [0,delta], literal Eq. (S29) is bounded by delta and cannot produce a size-dependent value near 60 without an unprinted observable convention.",
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }


def run_t012(profile: dict[str, Any]) -> dict[str, Any]:
    """Independent root/Jensen verification of the exact Eq. (5) identity."""

    left = complex(*profile["eq5_left_hopping"])
    right = complex(*profile["eq5_right_hopping"])
    momenta = (np.arange(int(profile["eq5_momentum_samples"])) + 0.5) * (
        2.0 * np.pi / int(profile["eq5_momentum_samples"])
    )
    rows: list[dict[str, float | list[float]]] = []
    for pair in profile["eq5_energies"]:
        energy = complex(*pair)
        roots = np.roots(np.asarray((right, -energy, left), dtype=np.complex128))
        exact = float(np.log(abs(right)) + np.log(np.max(np.abs(roots))))

        def objective(mu: float) -> float:
            beta = np.exp(float(mu) + 1j * momenta)
            values = left / beta + right * beta - energy
            return float(np.mean(np.log(np.maximum(np.abs(values), np.finfo(float).tiny))))

        minimum = optimize.minimize_scalar(
            objective,
            bounds=tuple(map(float, profile["eq5_deformation_bounds"])),
            method="bounded",
            options={"xatol": float(profile["eq5_tolerance"])},
        )
        rows.append(
            {
                "energy": [energy.real, energy.imag],
                "root_moduli": [float(value) for value in sorted(np.abs(roots))],
                "root_formula_potential": exact,
                "direct_minimum_potential": float(minimum.fun),
                "absolute_difference": float(abs(minimum.fun - exact)),
            }
        )
    acceptance = {
        "all_minimizations_converged_to_root_identity": max(float(row["absolute_difference"]) for row in rows) < float(profile["eq5_acceptance_tolerance"]),
        "multiple_complex_energies_checked": len(rows) >= 3,
    }
    return {
        "schema_version": 1,
        "target_id": "T012",
        "scientific_scale": "analytic_identity_plus_independent_quadrature",
        "method": "Jensen/root form compared with direct deformation minimization",
        "rows": rows,
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }


def _ronkin_nd(
    energy: complex,
    deformations: np.ndarray,
    *,
    momentum_points: int,
) -> float:
    dimension = len(deformations)
    momentum = (np.arange(momentum_points) + 0.5) * 2.0 * np.pi / momentum_points
    axes = np.meshgrid(*([momentum] * dimension), indexing="ij")
    characteristic = np.full(axes[0].shape, -energy, dtype=np.complex128)
    for index, axis in enumerate(axes):
        characteristic += np.exp(deformations[index] + 1j * axis)
        characteristic += 0.5 * np.exp(-deformations[index] - 1j * axis)
    return float(np.mean(np.log(np.maximum(np.abs(characteristic), np.finfo(float).tiny))))


def run_t013(profile: dict[str, Any]) -> dict[str, Any]:
    """Dimension-parameterized evaluator for the Eqs. (17)-(20) hierarchy."""

    energy = complex(*profile["hierarchy_energy"])
    rows: list[dict[str, Any]] = []
    for dimension in map(int, profile["hierarchy_dimensions"]):
        initial = np.zeros(dimension, dtype=np.float64)
        result = optimize.minimize(
            lambda value: _ronkin_nd(
                energy,
                np.asarray(value),
                momentum_points=int(profile["hierarchy_momentum_points"]),
            ),
            initial,
            method="Powell",
            bounds=[tuple(map(float, profile["hierarchy_deformation_bounds"]))] * dimension,
            options={"xtol": float(profile["hierarchy_tolerance"]), "ftol": float(profile["hierarchy_tolerance"]), "maxiter": 80},
        )
        permuted = _ronkin_nd(
            energy,
            np.asarray(result.x)[::-1],
            momentum_points=int(profile["hierarchy_momentum_points"]),
        )
        rows.append(
            {
                "dimension": dimension,
                "minimum_potential": float(result.fun),
                "deformations": [float(value) for value in result.x],
                "permuted_potential": permuted,
                "permutation_difference": float(abs(permuted - result.fun)),
                "optimizer_success": bool(result.success),
            }
        )
    acceptance = {
        "same_dimension_parameterized_path_covers_d1_to_d4": [row["dimension"] for row in rows] == [1, 2, 3, 4],
        "all_dimension_runs_finite": all(np.isfinite(row["minimum_potential"]) for row in rows),
        "separable_family_is_permutation_invariant": max(row["permutation_difference"] for row in rows) < 1e-8,
    }
    return {
        "schema_version": 1,
        "target_id": "T013",
        "scientific_scale": "parameterized_arbitrary_dimension_method_check",
        "method": "single dimension-agnostic Ronkin/minimization evaluator for Eqs. (17)-(20)",
        "scope_boundary": "The finite d=1..4 checks exercise the arbitrary-d construction interface; the source derivation supplies the universal recursion.",
        "rows": rows,
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }


def _transform_hoppings(hoppings: HoppingModel, matrix: tuple[tuple[int, int], tuple[int, int]]) -> HoppingModel:
    transformed: HoppingModel = {}
    for (dx, dy), amplitude in hoppings.items():
        displacement = (
            matrix[0][0] * dx + matrix[0][1] * dy,
            matrix[1][0] * dx + matrix[1][1] * dy,
        )
        transformed[displacement] = transformed.get(displacement, 0.0j) + amplitude
    return transformed


def _finite_geometry_potential_probe(profile: dict[str, Any]) -> list[dict[str, Any]]:
    bases = [
        tuple(tuple(int(value) for value in row) for row in matrix)
        for matrix in profile["geometry_basis_matrices"]
    ]
    rows: list[dict[str, Any]] = []
    for pair in profile["theorem_probe_energies"]:
        energy = complex(*pair)
        amoeba = amoeba_potential(
            energy,
            model_eq11(),
            momentum_samples=int(profile["theorem_momentum_samples"]),
            tolerance=float(profile["theorem_tolerance"]),
        ).potential
        geometry_values: list[float] = []
        for basis in bases:
            transformed = _transform_hoppings(model_eq11(), basis)
            branches = [
                minimize_cylindrical_potential(
                    energy,
                    transformed,
                    outer_axis=axis,
                    momentum_samples=int(profile["theorem_momentum_samples"]),
                    deformation_bounds=tuple(map(float, profile["theorem_deformation_bounds"])),
                    tolerance=float(profile["theorem_tolerance"]),
                ).potential
                for axis in (0, 1)
            ]
            geometry_values.append(float(min(branches)))
        rows.append(
            {
                "energy": [energy.real, energy.imag],
                "amoeba_potential": float(amoeba),
                "geometry_potentials": geometry_values,
                "maximum_geometry_minus_amoeba": float(max(geometry_values) - amoeba),
            }
        )
    return rows


def run_t014(profile: dict[str, Any]) -> dict[str, Any]:
    """Audit the minimization inequality underlying the regular-geometry subset theorem."""

    rng = np.random.default_rng(int(profile["seed"]))
    synthetic_rows: list[dict[str, float]] = []
    for _ in range(int(profile["theorem_random_trials"])):
        values = rng.normal(size=(17, 13))
        min_inside_mean = float(np.mean(np.min(values, axis=1)))
        min_after_mean = float(np.min(np.mean(values, axis=0)))
        synthetic_rows.append(
            {
                "mean_of_pointwise_minimum": min_inside_mean,
                "minimum_of_means": min_after_mean,
                "nonnegative_gap": min_after_mean - min_inside_mean,
            }
        )
    model_rows = _finite_geometry_potential_probe(profile)
    acceptance = {
        "min_integral_inequality_holds_all_trials": min(row["nonnegative_gap"] for row in synthetic_rows) >= -1e-14,
        "eq11_finite_probes_respect_inequality_with_quadrature_tolerance": max(row["maximum_geometry_minus_amoeba"] for row in model_rows) < float(profile["theorem_numeric_gate"]),
        "both_analytic_and_model_checks_present": bool(synthetic_rows and model_rows),
    }
    return {
        "schema_version": 1,
        "target_id": "T014",
        "scientific_scale": "analytic_inequality_plus_finite_falsification",
        "method": "mean(min f) <= min(mean f), followed by the Supplement S16-S22 harmonic-support argument",
        "synthetic_inequality_trials": synthetic_rows,
        "eq11_geometry_probes": model_rows,
        "acceptance": acceptance,
        "status": "passed" if all(acceptance.values()) else "failed",
    }


def _disk_sites(radius: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (x, y)
        for x in range(-radius, radius + 1)
        for y in range(-radius, radius + 1)
        if x * x + y * y <= radius * radius
    )


def run_t015_t016_probe(profile: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Non-authoritative finite probes for two explicitly underdefined claims."""

    geometry_rows = _finite_geometry_potential_probe(profile)
    t015 = {
        "schema_version": 1,
        "target_id": "T015",
        "status": "finite_attempt_completed_not_a_proof",
        "method": "declared finite basis family falsification probe",
        "basis_count": len(profile["geometry_basis_matrices"]),
        "rows": geometry_rows,
        "scientific_boundary": "The publication explicitly calls Eq. (14)/(S23) a conjecture and supplies neither a geometry universe nor a finite acceptance protocol; a finite search cannot establish the all-geometries union.",
    }

    probes = np.asarray(
        [complex(*pair) for pair in profile["smooth_probe_energies"]],
        dtype=np.complex128,
    )
    amoeba = np.asarray(
        [
            amoeba_potential(
                complex(energy),
                model_eq11(),
                momentum_samples=int(profile["theorem_momentum_samples"]),
                tolerance=float(profile["theorem_tolerance"]),
            ).potential
            for energy in probes
        ]
    )
    disk_rows: list[dict[str, Any]] = []
    for radius in map(int, profile["smooth_disk_radii"]):
        sites = _disk_sites(radius)
        spectrum = full_spectrum(build_obc_hamiltonian(sites, model_eq11()))
        finite = spectral_potential_grid(spectrum, probes)
        disk_rows.append(
            {
                "radius": radius,
                "site_count": len(sites),
                "mean_absolute_potential_difference": float(np.mean(np.abs(finite - amoeba))),
                "maximum_absolute_potential_difference": float(np.max(np.abs(finite - amoeba))),
            }
        )
    t016 = {
        "schema_version": 1,
        "target_id": "T016",
        "status": "finite_attempt_completed_not_authoritative",
        "method": "independently chosen Eq. (11) integer-disk sequence",
        "rows": disk_rows,
        "scientific_boundary": "The paper does not specify a model, lattice discretization, smooth-shape sequence, convergence metric, or tolerance for this claim, so this declared probe cannot be substituted for a paper contract.",
    }
    return t015, t016


def run_campaign(config_path: Path, profile_name: str, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile = config["profiles"][profile_name]
    output_root.mkdir(parents=True, exist_ok=True)

    t001, t001_arrays = run_t001(profile, output_root)
    np.savez_compressed(output_root / "T001_paper_arrays.npz", **t001_arrays)
    _write_json(output_root / "T001.json", t001)

    spectra = {
        "square": np.asarray(t001_arrays["square_spectrum"]),
        "rhombus": np.asarray(t001_arrays["rhombus_spectrum"]),
    }
    t002a, t002a_arrays = run_t002a(profile, output_root)
    np.savez_compressed(output_root / "T002A_paper_arrays.npz", **t002a_arrays)
    _write_json(output_root / "T002A.json", t002a)

    t002c, t002c_arrays = run_t002c(profile, output_root)
    np.savez_compressed(output_root / "T002C_formula_arrays.npz", **t002c_arrays)
    _write_json(output_root / "T002C.json", t002c)

    t003, t003_arrays = run_t003(profile, spectra)
    np.savez_compressed(output_root / "T003_gbz_arrays.npz", **t003_arrays)
    _write_json(output_root / "T003.json", t003)

    results: dict[str, dict[str, Any]] = {
        "T001": t001,
        "T002-A": t002a,
        "T002-C": t002c,
        "T003": t003,
        "T009": run_t009(profile),
        "T010": {},
        "T011": run_t011(profile),
        "T012": run_t012(profile),
        "T013": run_t013(profile),
        "T014": run_t014(profile),
    }
    t010, t010_arrays = run_t010(profile)
    results["T010"] = t010
    np.savez_compressed(output_root / "T010_s4_arrays.npz", **t010_arrays)
    t015, t016 = run_t015_t016_probe(profile)
    results["T015"] = t015
    results["T016"] = t016
    for target_id in ("T009", "T010", "T011", "T012", "T013", "T014", "T015", "T016"):
        _write_json(output_root / f"{target_id}.json", results[target_id])

    passed_targets = [
        target_id
        for target_id, payload in results.items()
        if payload.get("status") == "passed"
    ]
    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": profile_name,
        "numerical_input_policy": config["numerical_input_policy"],
        "reproduced_target_ids": passed_targets,
        "finite_non_authoritative_attempt_target_ids": ["T015", "T016"],
        "literal_discrepancy_check_target_ids": ["T009"],
        "all_reproduction_acceptance_passed": set(passed_targets)
        == {"T001", "T002-A", "T002-C", "T003", "T009", "T010", "T011", "T012", "T013", "T014"},
    }
    _write_json(output_root / "campaign_summary.json", summary)
    return summary
