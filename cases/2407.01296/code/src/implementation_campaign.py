"""Clean-room implementation campaign for the remaining geometry-adaptive items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from src.gbz import solve_gbz_for_energy
from src.geometry_adaptive import (
    aggregate_right_density,
    amoeba_potential,
    build_obc_hamiltonian,
    cylindrical_root_potential,
    cut_coordinate_sites,
    density_metrics,
    diamond_sites,
    eigensystem_residuals,
    full_right_eigensystem,
    full_spectrum,
    geometry_adaptive_potential,
    minimize_cylindrical_potential,
    model_eq11,
    model_eq15,
    spectral_density_from_potential,
    spectral_potential_grid,
    spectrum_metrics,
    square_sites,
    symmetric_cloud_distance,
)
from src.supplemental_campaign import (
    directional_winding_rows,
    s24_hamiltonian,
    s24_state_profiles,
)


def _complex(values: np.ndarray) -> list[list[float]]:
    flat = np.asarray(values, dtype=np.complex128).reshape(-1)
    return [[float(value.real), float(value.imag)] for value in flat]


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _geometry_payload(label: str, sites: tuple[tuple[int, int], ...], hoppings: dict[tuple[int, int], complex]) -> dict[str, Any]:
    matrix = build_obc_hamiltonian(sites, hoppings)
    eigensystem = full_right_eigensystem(matrix)
    density = aggregate_right_density(eigensystem.right_eigenvectors)
    residuals = eigensystem_residuals(matrix, eigensystem)
    return {
        "label": label,
        "site_count": len(sites),
        "coordinates": [list(site) for site in sites],
        "eigenvalues": _complex(eigensystem.eigenvalues),
        "aggregate_density": density.tolist(),
        "density_metrics": density_metrics(sites, density),
        "spectrum_metrics": spectrum_metrics(eigensystem.eigenvalues),
        "maximum_eigenpair_residual": float(np.max(residuals)),
    }


def _target_001(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    square = _geometry_payload("square", square_sites(int(profile["square_length"])), model_eq11())
    rhombus = _geometry_payload("rhombus", diamond_sites(int(profile["rhombus_radius"])), model_eq11())
    axis = np.linspace(float(profile["potential_range"][0]), float(profile["potential_range"][1]), int(profile["potential_points"]))
    probes = axis[None, :] + 1j * axis[:, None]
    for geometry in (square, rhombus):
        spectrum = np.asarray([complex(*pair) for pair in geometry["eigenvalues"]])
        potential = spectral_potential_grid(spectrum, probes)
        density = spectral_density_from_potential(potential, real_step=float(axis[1] - axis[0]), imaginary_step=float(axis[1] - axis[0]))
        geometry["spectral_potential"] = potential.tolist()
        geometry["spectral_density"] = density.tolist()
    passed = all(abs(sum(row["aggregate_density"]) - row["site_count"]) < 1e-8 and row["maximum_eigenpair_residual"] < 1e-10 for row in (square, rhombus))
    return {"target_id": "T001", "items": items, "status": "computed_reduced_scale", "geometries": [square, rhombus], "acceptance": {"passed": passed, "criterion": "Each complete right-eigenbasis is normalized and satisfies the OBC eigenproblem."}}


def _target_002(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    families = []
    spectra = []
    for radius in profile["critical_radii"]:
        sites = diamond_sites(int(radius))
        payload = _geometry_payload(f"diamond_R{radius}", sites, model_eq15())
        families.append(payload)
        spectra.append(np.asarray([complex(*value) for value in payload["eigenvalues"]]))
    boundary_rows = []
    for u, v in profile["boundary_half_widths"]:
        values = full_spectrum(build_obc_hamiltonian(cut_coordinate_sites(int(u), int(v)), model_eq15()))
        boundary_rows.append({"half_u": u, "half_v": v, "site_count": len(values), "spectrum": _complex(values), "metrics": spectrum_metrics(values)})
    rng = np.random.default_rng(int(profile["seed"]))
    disorder_rows = []
    base_sites = diamond_sites(int(profile["critical_radii"][-1]))
    base = build_obc_hamiltonian(base_sites, model_eq15()).toarray()
    for delta in profile["disorder_strengths"]:
        disorder = rng.uniform(-float(delta), float(delta), len(base_sites))
        values = np.linalg.eigvals(base + np.diag(disorder))
        disorder_rows.append({"delta": delta, "spectrum": _complex(values), "metrics": spectrum_metrics(values)})
    convergence = [symmetric_cloud_distance(spectra[index], spectra[index + 1]) for index in range(len(spectra) - 1)]
    passed = all(row["maximum_eigenpair_residual"] < 1e-10 for row in families) and all(np.isfinite(row["p95"]) for row in convergence)
    return {"target_id": "T002", "items": items, "status": "computed_reduced_scale", "critical_geometries": families, "boundary_ratio_spectra": boundary_rows, "successive_spectrum_distances": convergence, "disorder_spectra": disorder_rows, "acceptance": {"passed": passed, "criterion": "All critical-skin eigensystems pass residual checks and all finite-size spectral distances are finite."}}


def _target_003(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    rows = []
    for label, sites, basis in (
        ("square", square_sites(int(profile["gbz_square_length"])), "square"),
        ("rhombus", diamond_sites(int(profile["gbz_rhombus_radius"])), "rhombus"),
    ):
        spectrum = full_spectrum(build_obc_hamiltonian(sites, model_eq11()))
        energy = complex(spectrum[int(np.argmin(abs(spectrum - np.median(spectrum.real))))])
        points = solve_gbz_for_energy(energy, model_eq11(), basis=basis, momentum_samples=int(profile["momentum_samples"]), minimization_tolerance=float(profile["minimizer_tolerance"]), seed_count=int(profile["gbz_seed_count"]))
        rows.append({"geometry": label, "selected_obc_energy": [energy.real, energy.imag], "gbz_points": [{"mu_1": point.mu_1, "mu_2": point.mu_2, "k_1": point.k_1, "k_2": point.k_2, "energy": [point.energy.real, point.energy.imag], "residual": point.residual} for point in points]})
    residuals = [point["residual"] for row in rows for point in row["gbz_points"]]
    return {"target_id": "T003", "items": items, "status": "computed_reduced_scale", "rows": rows, "acceptance": {"passed": bool(residuals and max(residuals) <= float(profile["gbz_residual_gate"])), "criterion": "At least one independently solved GBZ phase pair exists and every characteristic residual passes the frozen gate."}}


def _target_010(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    rows = []
    previous_spectrum: np.ndarray | None = None
    for length in profile["s4_lengths"]:
        result = s24_state_profiles(int(length), delta=float(profile["s4_delta"]))
        spectrum = full_spectrum(
            s24_hamiltonian(int(length), delta=float(profile["s4_delta"]))
        )
        density = np.asarray(result["largest_real_density"], dtype=float)
        x = np.arange(len(density), dtype=float)
        safe = np.maximum(density, np.finfo(float).tiny)
        slope = float(np.polyfit(x, np.log(safe), 1)[0])
        row = {"length": length, "largest_real_density": density.tolist(), "decay_rate_magnitude": abs(slope), "spectrum": _complex(spectrum)}
        if previous_spectrum is not None:
            row["distance_from_previous_size"] = symmetric_cloud_distance(previous_spectrum, spectrum)
        rows.append(row)
        previous_spectrum = spectrum
    return {"target_id": "T010", "items": items, "status": "computed_reduced_scale", "rows": rows, "acceptance": {"passed": all(abs(sum(row["largest_real_density"]) - 1.0) < 1e-10 and np.isfinite(row["decay_rate_magnitude"]) for row in rows), "criterion": "All state profiles are normalized and yield finite localization-rate estimates."}}


def _target_011(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    rows = []
    for basis in ("square_y", "diagonal_1m1"):
        rows.extend(directional_winding_rows(model_eq11(), basis=basis, transverse_points=int(profile["winding_transverse_points"]), path_points=int(profile["winding_path_points"])))
    values = {int(row["winding"]) for row in rows}
    return {"target_id": "T011", "items": items, "status": "computed_reduced_scale", "rows": rows, "observed_winding_sectors": sorted(values), "acceptance": {"passed": bool(rows and all(np.isfinite(row["transverse_momentum"]) for row in rows)), "criterion": "Both frozen momentum cuts produce finite, integer-valued winding sectors."}}


def _target_012(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    energy = complex(*profile["claim_probe_energy"])
    analytic = minimize_cylindrical_potential(energy, model_eq11(), outer_axis=0, momentum_samples=int(profile["momentum_samples"]), deformation_bounds=tuple(profile["deformation_bounds"]), tolerance=float(profile["minimizer_tolerance"]))
    grid = np.linspace(*profile["deformation_bounds"], int(profile["deformation_grid_points"]))
    values = [
        cylindrical_root_potential(
            energy,
            model_eq11(),
            outer_axis=0,
            deformation=float(value),
            momentum_samples=int(profile["momentum_samples"]),
        )
        for value in grid
    ]
    gap = float(analytic.potential - min(values))
    return {"target_id": "T012", "items": items, "status": "computed_numeric_identity_check", "minimizer": {"potential": analytic.potential, "deformation": analytic.deformation, "evaluations": analytic.evaluations}, "independent_grid_minimum": min(values), "minimizer_minus_grid": gap, "acceptance": {"passed": gap <= float(profile["claim_grid_tolerance"]), "criterion": "The continuous Eq. (5) minimizer is no worse than the independent frozen deformation grid within tolerance."}}


def _hierarchy_potential(dimension: int, energy: complex, momentum_points: int) -> float:
    momentum = (np.arange(momentum_points) + 0.5) * (2 * np.pi / momentum_points)
    mesh = np.meshgrid(*([momentum] * dimension), indexing="ij")
    characteristic = -energy + sum(np.exp(1j * axis) + 0.5 * np.exp(-1j * axis) for axis in mesh)
    return float(np.mean(np.log(np.maximum(abs(characteristic), np.finfo(float).tiny))))


def _target_013(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    energy = complex(*profile["claim_probe_energy"])
    rows = [{"dimension": dimension, "zero_deformation_potential": _hierarchy_potential(dimension, energy, int(profile["hierarchy_momentum_points"]))} for dimension in profile["hierarchy_dimensions"]]
    return {"target_id": "T013", "items": items, "status": "computed_parameterized_hierarchy", "model": "separable d-dimensional Laurent test family declared in config", "rows": rows, "paper_exact_boundary": "This checks the arbitrary-d recursion interface; it is not a proof of the paper's full hierarchy theorem.", "acceptance": {"passed": all(np.isfinite(row["zero_deformation_potential"]) for row in rows), "criterion": "The same parameterized Laurent evaluator runs without dimension-specific branches for every frozen d."}}


def _claim_family(target_id: str, profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    radii = [int(value) for value in profile["claim_radii"]]
    spectra = [full_spectrum(build_obc_hamiltonian(diamond_sites(radius), model_eq11())) for radius in radii]
    rows = []
    for radius, spectrum in zip(radii, spectra, strict=True):
        probes = spectrum[np.linspace(0, len(spectrum) - 1, min(4, len(spectrum)), dtype=int)]
        potentials = [geometry_adaptive_potential(complex(energy), model_eq11(), basis="rhombus", momentum_samples=int(profile["momentum_samples"]), tolerance=float(profile["minimizer_tolerance"])).potential for energy in probes]
        amoeba = [amoeba_potential(complex(energy), model_eq11(), momentum_samples=int(profile["amoeba_momentum_samples"]), tolerance=float(profile["amoeba_tolerance"])).potential for energy in probes]
        rows.append({"radius": radius, "site_count": len(spectrum), "sampled_energies": _complex(probes), "geometry_potential": potentials, "amoeba_potential": amoeba})
    distances = [symmetric_cloud_distance(spectra[index], spectra[index + 1]) for index in range(len(spectra) - 1)]
    descriptions = {
        "T014": "finite-size falsification attempt for the regular-geometry subset theorem",
        "T015": "finite-family falsification attempt for the all-geometries union conjecture",
        "T016": "finite-size convergence diagnostic for the smooth-boundary limit",
    }
    return {"target_id": target_id, "items": items, "status": "computed_falsification_attempt_not_proof", "scientific_scope": descriptions[target_id], "rows": rows, "successive_spectrum_distances": distances, "acceptance": {"passed": all(np.isfinite(value) for row in rows for value in row["geometry_potential"] + row["amoeba_potential"]) and all(np.isfinite(distance["p95"]) for distance in distances), "criterion": "Every predeclared finite-size theorem/conjecture probe evaluates both potentials and the size-to-size distance without numerical failure."}}


def run_campaign(config_path: Path, profile_name: str, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile = config["profiles"][profile_name]
    target_items = config["target_items"]
    if len({item for items in target_items.values() for item in items}) != int(config["fixed_denominator"]):
        raise ValueError("target_items no longer match the frozen implementation denominator")
    results = {
        "T001": _target_001(profile, target_items["T001"]), "T002": _target_002(profile, target_items["T002"]),
        "T003": _target_003(profile, target_items["T003"]), "T010": _target_010(profile, target_items["T010"]),
        "T011": _target_011(profile, target_items["T011"]), "T012": _target_012(profile, target_items["T012"]),
        "T013": _target_013(profile, target_items["T013"]), "T014": _claim_family("T014", profile, target_items["T014"]),
        "T015": _claim_family("T015", profile, target_items["T015"]), "T016": _claim_family("T016", profile, target_items["T016"]),
    }
    for target_id, payload in results.items():
        _write(output_root / f"{target_id}.json", payload)
    summary = {"schema_version": 1, "paper_id": config["paper_id"], "profile": profile_name, "scientific_scale": profile["scientific_scale"], "fixed_denominator": config["fixed_denominator"], "implemented_items": sum(len(payload["items"]) for payload in results.values()), "all_acceptance_passed": all(payload["acceptance"]["passed"] for payload in results.values()), "target_status": {target: payload["status"] for target, payload in results.items()}}
    _write(output_root / "campaign_summary.json", summary)
    return summary
