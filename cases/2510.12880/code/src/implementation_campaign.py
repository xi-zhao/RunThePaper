"""Clean-room implementation closure for all spin-chain reproduction items."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

import numpy as np

from .kitaev_aklt import (
    _rotation_eigenvalues,
    configuration_sector,
    exact_point_zero_mode_count,
    full_hamiltonian,
    lowest_eigenspace,
    open_hamiltonian,
    overlap_in_sector,
    product_configuration,
    product_state_diagnostics,
    sector_hamiltonian,
)


@dataclass(frozen=True)
class TargetResult:
    target_id: str
    status: str
    scientific_scale: str
    data: dict[str, Any]
    checks: dict[str, bool]
    boundary: dict[str, Any]

    def payload(self, item_ids: list[str]) -> dict[str, Any]:
        payload = asdict(self)
        payload["item_ids"] = item_ids
        payload["checks_passed"] = all(self.checks.values())
        return _json_safe(payload)


def run_campaign(config: dict[str, Any], profile_name: str) -> dict[str, dict[str, Any]]:
    if config.get("paper_id") != "2510.12880":
        raise ValueError("configuration paper_id does not match this case")
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise ValueError(f"unknown profile: {profile_name}")
    target_items = config.get("target_items")
    if not isinstance(target_items, dict) or not target_items:
        raise ValueError("target_items must be a non-empty object")
    flattened = [item for items in target_items.values() for item in items]
    if len(flattened) != len(set(flattened)):
        raise ValueError("each atomic item must map exactly once")
    runners: dict[str, Callable[[dict[str, Any]], TargetResult]] = {
        "T001": _ground_overlap,
        "T002": _excited_overlap,
        "V001": _periodic_exact_point,
        "V002": _periodic_controls,
        "V003": _open_exact_point,
        "V004": _open_pi_over_two,
        "V005": _open_three_pi_over_two,
        "V006": _parity_constraints,
        "V007": _perturbation_sector,
    }
    if set(target_items) != set(runners):
        raise ValueError("target item map and runner map differ")
    profile = profiles[profile_name]
    return {
        target_id: runners[target_id](profile).payload(item_ids)
        for target_id, item_ids in target_items.items()
    }


def _boundary(statement: str) -> dict[str, Any]:
    return {
        "implementation_attestation_only": True,
        "paper_exact_promotion": False,
        "scientific_coverage_promotion": False,
        "remaining_scientific_boundary": statement,
    }


def _ground_overlap(profile: dict[str, Any]) -> TargetResult:
    rows = []
    for theta in profile["overlap_thetas"]:
        result = overlap_in_sector(int(profile["overlap_sites"]), float(theta), (1,) * int(profile["overlap_sites"]))
        rows.append({"theta": theta, **result})
    return TargetResult(
        "T001",
        "passed",
        "reduced_scale",
        {"rows": rows},
        {
            "finite": all(np.isfinite(row["fidelity"]) for row in rows),
            "unit_interval": all(0.0 <= row["fidelity"] <= 1.0 for row in rows),
            "exact_point_unity": abs(rows[-1]["fidelity"] - 1.0) < 1.0e-10,
        },
        _boundary("The full published N/theta grid and existing digitized comparison remain separate scientific evidence."),
    )


def _excited_overlap(profile: dict[str, Any]) -> TargetResult:
    sites = int(profile["overlap_sites"])
    sector = (-1,) + (1,) * (sites - 1)
    rows = []
    for theta in profile["overlap_thetas"]:
        result = overlap_in_sector(sites, float(theta), sector)
        rows.append({"theta": theta, **result})
    return TargetResult(
        "T002",
        "passed",
        "reduced_scale",
        {"rows": rows},
        {
            "finite": all(np.isfinite(row["fidelity"]) for row in rows),
            "unit_interval": all(0.0 <= row["fidelity"] <= 1.0 for row in rows),
            "exact_point_unity": abs(rows[-1]["fidelity"] - 1.0) < 1.0e-10,
        },
        _boundary("Reduced-size execution attests the one-flip-sector path; it does not replace accepted full-panel evidence."),
    )


def _periodic_exact_point(profile: dict[str, Any]) -> TargetResult:
    rows = [exact_point_zero_mode_count(int(n)) for n in profile["exact_point_sites"]]
    return TargetResult(
        "V001",
        "passed",
        "finite_size_exact_check",
        {"rows": rows},
        {
            "nullity_formula": all(row["total_zero_modes"] == row["expected_zero_modes"] for row in rows),
            "mps_zero_energy": all(abs(row["maximum_mps_energy"]) < 1.0e-10 for row in rows),
        },
        _boundary("The exact finite-size subset is not an N=8--12 execution claim."),
    )


def _periodic_controls(profile: dict[str, Any]) -> TargetResult:
    sites = int(profile["control_sites"])
    alternating = [
        product_state_diagnostics(sites, np.pi / 2.0, kind)
        for kind in ("alternating_xy", "alternating_yx")
    ]
    uniform = product_state_diagnostics(sites, 3.0 * np.pi / 2.0, "uniform_z")
    theta = float(profile["mirror_theta"])
    left = np.linalg.eigvalsh(full_hamiltonian(sites, theta)[0])
    right = np.linalg.eigvalsh(full_hamiltonian(sites, np.pi - theta)[0])
    mirror_error = float(np.max(np.abs(left - right)))
    return TargetResult(
        "V002",
        "passed",
        "finite_size_exact_check",
        {"alternating": alternating, "uniform_z": uniform, "mirror_error": mirror_error},
        {
            "alternating_zero_energy": all(abs(row["energy"]) < 1.0e-10 for row in alternating),
            "uniform_energy": abs(uniform["energy"] + sites) < 1.0e-10,
            "product_states_exact": max([row["residual_norm"] for row in alternating] + [uniform["residual_norm"]]) < 1.0e-10,
            "mirror_spectrum": mirror_error < 1.0e-10,
        },
        _boundary("These are representative exact finite-size controls, not a new phase-boundary determination."),
    )


def _open_spectrum(sites: int, theta: float) -> tuple[np.ndarray, np.ndarray]:
    hamiltonian, configurations = open_hamiltonian(sites, theta)
    return np.linalg.eigvalsh(hamiltonian), configurations


def _open_exact_point(profile: dict[str, Any]) -> TargetResult:
    rows = []
    for sites in profile["open_sites"]:
        values, _ = _open_spectrum(int(sites), np.pi / 4.0)
        nullity = int(np.count_nonzero(np.abs(values) < 1.0e-10))
        rows.append({"number_sites": sites, "nullity": nullity, "expected": 2 ** (int(sites) + 1) - 1})
    return TargetResult(
        "V003", "passed", "finite_size_exact_check", {"rows": rows},
        {"degeneracy_formula": all(row["nullity"] == row["expected"] for row in rows)},
        _boundary("Finite N=2,4 diagonalization supports but does not prove the all-even-N edge-state theorem."),
    )


def _open_pi_over_two(profile: dict[str, Any]) -> TargetResult:
    rows = []
    for sites in profile["open_sites"]:
        values, _ = _open_spectrum(int(sites), np.pi / 2.0)
        ground = float(values[0])
        multiplicity = int(np.count_nonzero(values - ground < 1.0e-10))
        rows.append({"number_sites": sites, "ground_energy": ground, "multiplicity": multiplicity, "expected": 2 * int(sites) + 1})
    return TargetResult(
        "V004", "passed", "finite_size_exact_check", {"rows": rows},
        {"zero_ground_energy": all(abs(row["ground_energy"]) < 1.0e-10 for row in rows), "degeneracy_formula": all(row["multiplicity"] == row["expected"] for row in rows)},
        _boundary("Finite N=2,4 checks do not constitute an all-N proof."),
    )


def _open_three_pi_over_two(profile: dict[str, Any]) -> TargetResult:
    rows = []
    for sites in profile["open_sites"]:
        values, _ = _open_spectrum(int(sites), 3.0 * np.pi / 2.0)
        ground = float(values[0])
        multiplicity = int(np.count_nonzero(values - ground < 1.0e-10))
        rows.append({"number_sites": sites, "ground_energy": ground, "expected_energy": -(int(sites) - 1), "multiplicity": multiplicity})
    return TargetResult(
        "V005", "passed", "finite_size_exact_check", {"rows": rows},
        {"ground_energy": all(abs(row["ground_energy"] - row["expected_energy"]) < 1.0e-10 for row in rows), "fourfold": all(row["multiplicity"] == 4 for row in rows)},
        _boundary("The numerical multiplicity check does not independently label the two edge conserved quantities."),
    )


def _parity_constraints(profile: dict[str, Any]) -> TargetResult:
    sites = int(profile["parity_sites"])
    hamiltonian, basis = sector_hamiltonian(sites, 0.0, (1,) * sites)
    energy, subspace, residual = lowest_eigenspace(hamiltonian)
    state = subspace[:, 0]
    rotation_rows = {}
    checks = {"unique_ground_state": subspace.shape[1] == 1, "eigen_residual": residual < 1.0e-10}
    for axis in ("x", "y"):
        signs = np.prod(_rotation_eigenvalues(axis)[basis], axis=1)
        rotation_residual = float(np.linalg.norm(signs * state - state))
        rotation_rows[axis] = {"expectation": float(np.real(np.vdot(state, signs * state))), "residual": rotation_residual}
        checks[f"global_{axis}_parity_even"] = rotation_residual < 1.0e-10
    return TargetResult(
        "V006", "passed", "finite_size_symmetry_check", {"energy": energy, "global_rotations": rotation_rows}, checks,
        _boundary("Global pi-rotation parity is a necessary symmetry consequence; a direct all-bond triplet-support proof remains unaccepted."),
    )


def _perturbation_sector(profile: dict[str, Any]) -> TargetResult:
    sites = int(profile["perturbation_sites"])
    h0, basis = full_hamiltonian(sites, 3.0 * np.pi / 2.0)
    perturbation, _ = full_hamiltonian(sites, 0.0)
    state = np.zeros(len(basis), dtype=np.complex128)
    index = {tuple(int(v) for v in row): i for i, row in enumerate(basis)}[product_configuration(sites, "uniform_z")]
    state[index] = 1.0
    applied = perturbation @ state
    first_order = float(np.real(np.vdot(state, applied)))
    values, vectors = np.linalg.eigh(h0)
    coefficients = vectors.conj().T @ applied
    excited = np.abs(values - values[0]) > 1.0e-10
    second_order = float(np.sum(np.abs(coefficients[excited]) ** 2 / (values[0] - values[excited])))
    support_sectors = {
        configuration_sector(row)
        for row, amplitude in zip(basis, applied, strict=True)
        if abs(amplitude) > 1.0e-12
    }
    return TargetResult(
        "V007", "passed", "second_order_finite_size_check",
        {"first_order": first_order, "second_order": second_order, "support_sectors": [list(row) for row in sorted(support_sectors)]},
        {"first_order_zero": abs(first_order) < 1.0e-10, "second_order_negative": second_order < 0.0, "uniform_positive_sector": support_sectors == {(1,) * sites}},
        _boundary("The implementation verifies first and second order at finite N; the every-order perturbative statement still requires an analytic proof or fresh review."),
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value
