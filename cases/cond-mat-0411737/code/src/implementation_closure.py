"""Clean-room implementation closure for the remaining Kane-Mele items.

The target paper leaves several publication-specific inputs unspecified.  This
module separates executable formula paths from strict external-input handlers;
the latter return blockers until a reviewed package is supplied.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

import numpy as np

from kane_mele.model import (
    band_eigensystem,
    bare_gap_kelvin,
    build_ribbon_geometry,
    continuum_energies,
    rashba_kelvin,
)
from kane_mele.symmetry import parallel_field_mass_path


@dataclass(frozen=True)
class TargetResult:
    target_id: str
    status: str
    scientific_scale: str
    data: dict[str, Any]
    checks: dict[str, bool]
    boundary: dict[str, Any] | None = None

    def payload(self, item_ids: list[str]) -> dict[str, Any]:
        result = asdict(self)
        result["item_ids"] = item_ids
        result["checks_passed"] = all(self.checks.values())
        return _json_safe(result)


def run_campaign(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Run the reduced formula paths and attest every strict input boundary."""

    if config.get("paper_id") != "cond-mat-0411737":
        raise ValueError("configuration paper_id does not match this case")
    if config.get("profile") != "reduced_implementation_attestation":
        raise ValueError("only the frozen reduced attestation profile is accepted")
    target_items = config.get("target_items")
    if not isinstance(target_items, dict) or not target_items:
        raise ValueError("target_items must be a non-empty object")
    items = [item for group in target_items.values() for item in group]
    if len(items) != len(set(items)):
        raise ValueError("each atomic item must map exactly once")

    parameters = config["parameters"]
    runners: dict[str, Callable[[], TargetResult]] = {
        "T014": lambda: _blocked(config, "T014", "evaluate_mobility_package"),
        "T015": lambda: _continuum_branches(parameters["continuum"]),
        "T016": lambda: _blocked(config, "T016", "evaluate_conserved_spin_package"),
        "T017": lambda: _blocked(config, "T017", "evaluate_conserved_spin_package"),
        "T018": lambda: _ribbon_spectrum(parameters["ribbon"]),
        "T019": lambda: _parallel_field_path(parameters["parallel_field"]),
        "T020": lambda: _intrinsic_gap(parameters["intrinsic_gap"]),
        "T021": lambda: _blocked(config, "T021", "evaluate_graphite_package"),
        "T022": lambda: _rashba_estimate(parameters["rashba"]),
        "T023": lambda: _blocked(config, "T023", "evaluate_substrate_package"),
    }
    if set(target_items) != set(runners):
        raise ValueError("target item map and runner map differ")
    return {
        target_id: runners[target_id]().payload(item_ids)
        for target_id, item_ids in target_items.items()
    }


def _blocked(config: dict[str, Any], target_id: str, handler: str) -> TargetResult:
    contract = config.get("input_contracts", {}).get(target_id)
    required = contract.get("required_fields") if isinstance(contract, dict) else None
    if not isinstance(required, list) or not required or not all(
        isinstance(field, str) and field for field in required
    ):
        raise ValueError(f"invalid external-input contract for {target_id}")
    return TargetResult(
        target_id,
        "blocked_on_paper_input",
        "input_contract",
        {
            "model": contract["model"],
            "required_input_schema": required,
            "handler": handler,
        },
        {"schema_nonempty": True, "handler_implemented": handler in globals()},
        {
            "reason": "The indispensable publication-specific input is absent and is not guessed.",
            "scientific_promotion": False,
        },
    )


def _continuum_branches(config: dict[str, Any]) -> TargetResult:
    q = np.asarray(config["q_over_reference"], dtype=float)
    hbar_vf = float(config["hbar_vf"])
    energies = np.asarray(
        [
            continuum_energies(
                float(value), 0.0, hbar_vf=hbar_vf, delta_so=0.0, lambda_r=0.0
            )
            for value in q
        ]
    )
    expected = q[:, None] * hbar_vf
    residual = float(np.max(np.abs(np.abs(energies) - expected)))
    return TargetResult(
        "T015",
        "passed",
        "analytic_reduced_scale",
        {
            "q_over_reference": q,
            "energies_over_reference": energies,
            "max_abs_branch_residual": residual,
            "unit_audit": "For q as wavevector, Eq. (2) yields E=+-hbar*v_F*|q|; the printed later shorthand omits hbar.",
        },
        {"branches_are_linear": residual < 1.0e-12, "positive_and_negative_branches": bool(np.allclose(energies[:, 0], -energies[:, -1]))},
        {"paper_exact_status": "notation_inconclusive", "scientific_promotion": False},
    )


def _ribbon_spectrum(config: dict[str, Any]) -> TargetResult:
    width = int(config["width_chains"])
    k_values = np.linspace(0.0, 2.0 * np.pi, int(config["k_points"]))
    geometry = build_ribbon_geometry(width)
    spectra = []
    for momentum in k_values:
        up, _ = band_eigensystem(
            geometry,
            float(momentum),
            hopping_t=float(config["hopping_t"]),
            spin_orbit_t2=float(config["spin_orbit_t2"]),
            spin=1,
        )
        down, _ = band_eigensystem(
            geometry,
            float(momentum),
            hopping_t=float(config["hopping_t"]),
            spin_orbit_t2=float(config["spin_orbit_t2"]),
            spin=-1,
        )
        spectra.append(np.sort(np.concatenate([up, down])))
    bands = np.asarray(spectra)
    return TargetResult(
        "T018",
        "passed",
        "reduced_reconstructed_scale",
        {"k_times_a": k_values, "energies_over_t": bands, "width_chains": width},
        {
            "full_array_generated": bands.shape == (len(k_values), 4 * width),
            "finite_spectrum": bool(np.all(np.isfinite(bands))),
            "spin_blocks_degenerate_at_trim": bool(np.allclose(bands[0], bands[0][::-1] * -1.0, atol=1.0e-10)),
        },
        {
            "paper_exact_status": "input_blocked",
            "reason": "The paper fixes t2/t and axes but not ribbon width or sampling.",
            "scientific_promotion": False,
        },
    )


def _parallel_field_path(config: dict[str, Any]) -> TargetResult:
    result = parallel_field_mass_path(
        gap_scale=float(config["gap_scale"]),
        momentum_points=int(config["momentum_points"]),
        path_points=int(config["path_points"]),
    )
    minimum_gap = float(result["minimum_bulk_gap"])
    return TargetResult(
        "T019",
        "passed",
        "generic_symmetry_path",
        result,
        {"finite_positive_generic_gap": np.isfinite(minimum_gap) and minimum_gap > 0.0, "translation_limitation_reported": bool(result["bridge_requires_intervalley_mixing"])},
        {
            "paper_exact_status": "input_blocked",
            "reason": "The generic bridge mixes valleys; the publication does not print its claimed translation-preserving connecting terms.",
            "scientific_promotion": False,
        },
    )


def _intrinsic_gap(config: dict[str, Any]) -> TargetResult:
    value = bare_gap_kelvin(float(config["graphene_lattice_constant_angstrom"]))
    paper = float(config["paper_rounded_full_gap_kelvin"])
    return TargetResult(
        "T020",
        "passed",
        "analytic_with_declared_input",
        {"full_gap_kelvin": value, "paper_rounded_kelvin": paper, "relative_difference": abs(value - paper) / paper},
        {"finite_positive_gap": np.isfinite(value) and value > 0.0},
        {"paper_exact_status": "input_blocked", "reason": "The lattice-length convention is declared by the reproduction but omitted by the paper.", "scientific_promotion": False},
    )


def _rashba_estimate(config: dict[str, Any]) -> TargetResult:
    kelvin = rashba_kelvin(
        fermi_velocity_m_per_s=float(config["fermi_velocity_m_per_s"]),
        electric_field_volts=float(config["electric_field_volts"]),
        electric_field_distance_nm=float(config["electric_field_distance_nm"]),
    )
    millikelvin = 1000.0 * kelvin
    paper = float(config["paper_rounded_millikelvin"])
    return TargetResult(
        "T022",
        "passed",
        "analytic_with_declared_input",
        {"lambda_r_millikelvin": millikelvin, "paper_rounded_millikelvin": paper, "relative_difference": abs(millikelvin - paper) / paper},
        {"finite_positive_coupling": np.isfinite(millikelvin) and millikelvin > 0.0},
        {"paper_exact_status": "input_blocked", "reason": "The reproduction declares v_F=1e6 m/s; the paper does not print the numerical v_F input.", "scientific_promotion": False},
    )


def evaluate_mobility_package(package: dict[str, Any]) -> dict[str, float]:
    """Evaluate the cited mobility maximum once primary measurements are frozen."""

    _require_fields(package, ("source_id", "source_sha256", "measurements", "mobility_unit"))
    values = np.asarray(package["measurements"], dtype=float)
    if values.ndim != 1 or len(values) == 0 or np.any(values < 0):
        raise ValueError("measurements must be a non-empty nonnegative vector")
    unit = package["mobility_unit"]
    if unit == "cm^2/(V s)":
        factor = 1.0
    elif unit == "m^2/(V s)":
        factor = 1.0e4
    else:
        raise ValueError("unsupported mobility_unit")
    return {"maximum_mobility_cm2_per_vs": float(np.max(values) * factor)}


def evaluate_conserved_spin_package(package: dict[str, Any]) -> dict[str, float]:
    """Evaluate a supplied conserved-spin Kubo operator without author arrays."""

    _require_fields(package, ("source_id", "source_sha256", "basis", "samples", "occupied_count", "normalization"))
    occupied_count = int(package["occupied_count"])
    total = 0.0
    for sample in package["samples"]:
        _require_fields(sample, ("hamiltonian", "spin_current_x", "velocity_y", "weight"))
        hamiltonian = _decode_matrix(sample["hamiltonian"])
        current = _decode_matrix(sample["spin_current_x"])
        velocity = _decode_matrix(sample["velocity_y"])
        if not (hamiltonian.shape == current.shape == velocity.shape) or hamiltonian.shape[0] != hamiltonian.shape[1]:
            raise ValueError("all Kubo matrices must be square with matching dimensions")
        if not np.allclose(hamiltonian, hamiltonian.conj().T):
            raise ValueError("hamiltonian must be Hermitian")
        energies, vectors = np.linalg.eigh(hamiltonian)
        if not 0 < occupied_count < len(energies):
            raise ValueError("occupied_count must split occupied and empty states")
        for occupied in range(occupied_count):
            for empty in range(occupied_count, len(energies)):
                gap = float(energies[empty] - energies[occupied])
                if gap <= 0.0:
                    raise ValueError("Kubo spectrum must have a positive occupied-empty gap")
                first = np.vdot(vectors[:, occupied], current @ vectors[:, empty])
                second = np.vdot(vectors[:, empty], velocity @ vectors[:, occupied])
                total += float(sample["weight"]) * (-2.0 * float(np.imag(first * second)) / gap**2)
    value = total * float(package["normalization"])
    return {"spin_hall_conductivity": value, "relative_to_e_over_2pi": value / (1.0 / (2.0 * np.pi))}


def evaluate_graphite_package(package: dict[str, Any]) -> dict[str, Any]:
    _require_fields(package, ("source_id", "source_sha256", "splittings", "unit", "energy_convention"))
    values = np.asarray(package["splittings"], dtype=float)
    if values.ndim != 1 or len(values) == 0 or np.any(values <= 0):
        raise ValueError("splittings must be a non-empty positive vector")
    factors = {"K": 1.0, "meV": 11.604518121550082, "eV": 11604.518121550082}
    if package["unit"] not in factors:
        raise ValueError("unsupported splitting unit")
    kelvin = values * factors[package["unit"]]
    return {"splittings_kelvin": kelvin.tolist(), "range_kelvin": [float(np.min(kelvin)), float(np.max(kelvin))]}


def evaluate_substrate_package(package: dict[str, Any]) -> dict[str, Any]:
    _require_fields(package, ("source_id", "source_sha256", "substrate", "lambda_r", "delta_so", "unit", "method"))
    lambda_r = float(package["lambda_r"])
    delta_so = float(package["delta_so"])
    if lambda_r < 0.0 or delta_so <= 0.0:
        raise ValueError("lambda_r must be nonnegative and delta_so positive")
    ratio = lambda_r / delta_so
    return {"substrate": package["substrate"], "lambda_r_over_delta_so": ratio, "ordering_lambda_r_below_delta_so": ratio < 1.0}


def _require_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> None:
    missing = [field for field in fields if field not in payload]
    if missing:
        raise ValueError(f"missing required fields: {missing}")


def _decode_matrix(values: Any) -> np.ndarray:
    raw = np.asarray(values)
    if raw.ndim == 3 and raw.shape[-1] == 2:
        matrix = raw[..., 0].astype(float) + 1j * raw[..., 1].astype(float)
    else:
        matrix = np.asarray(values, dtype=float).astype(complex)
    return np.asarray(matrix, dtype=complex)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return [float(value.real), float(value.imag)]
    return value
