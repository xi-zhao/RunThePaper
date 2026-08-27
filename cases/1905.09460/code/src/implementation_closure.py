"""Clean-room implementation witnesses for the 28 frozen closure items.

The campaign proves that every declared numerical route is executable without
reading the paper, source figures, author arrays, or author code.  Its reduced
parameters are an engineering attestation only; they do not promote any
scientific item to paper-exact coverage.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.linalg import lu_factor

from .nonhermitian_quasicrystal import (
    aah_hamiltonian,
    edge_state_counts,
    etalon_transmission,
    inverse_participation_ratios,
    laser_operator,
    normalized_eigensystem,
    spectral_bandwidth,
)


ITEMS_BY_TARGET = {
    "T001": [
        "FIG001_A_H0",
        "FIG001_A_H066",
        "FIG001_A_H074",
        "FIG001_A_H100",
        "FIG001_B_MAX_ABS_IM_E",
        "FIG001_C_MAX_IPR",
        "FIG001_C_MIN_IPR",
    ],
    "T002": [
        "FIG003_A_BANDWIDTH",
        "FIG003_B_D010",
        "FIG003_B_D020",
        "FIG003_B_D030",
        "FIG003_B_D035",
    ],
    "T003": [
        "SUPP001_A_H0",
        "SUPP001_A_H066",
        "SUPP001_A_H074",
        "SUPP001_A_H100",
        "SUPP001_B_MAX_ABS_IM_E",
        "SUPP001_C_MAX_IPR",
        "SUPP001_C_MIN_IPR",
    ],
    "T004": [
        "SUPP002_IMAG_APPROX",
        "SUPP002_IMAG_EXACT",
        "SUPP002_REAL_APPROX",
        "SUPP002_REAL_EXACT",
    ],
    "T005": ["FIG001_D_W_EQ5", "FIG001_D_W_EQS12"],
    "T006": ["SUPP001_D_NL", "SUPP001_D_NR"],
    "T007": ["CLM_WINDING_EB_INVARIANCE"],
}


def h2_hamiltonian(
    length: int,
    *,
    hopping: float,
    potential_strength: float,
    alpha: float,
    theta: float,
    complex_phase: float,
) -> np.ndarray:
    """Construct the finite matrix H2 printed in Supplement Eq. (S-12)."""

    if length < 3:
        raise ValueError("length must be at least three")
    sites = np.arange(1, length + 1, dtype=float)
    matrix = np.diag((2.0 * hopping * np.cos(2.0 * np.pi * alpha * sites)).astype(complex))
    coupling = potential_strength / 2.0
    matrix += np.diag(np.full(length - 1, coupling, dtype=complex), 1)
    matrix += np.diag(np.full(length - 1, coupling, dtype=complex), -1)
    matrix[0, -1] = coupling * np.exp(complex_phase * length - 1j * theta)
    matrix[-1, 0] = coupling * np.exp(-complex_phase * length + 1j * theta)
    return matrix


def _determinant_winding(matrices: list[np.ndarray], base_energy: complex) -> float:
    phases = []
    for matrix in matrices:
        lu, pivots = lu_factor(
            matrix - base_energy * np.eye(matrix.shape[0]),
            check_finite=False,
        )
        diagonal = np.diag(lu)
        if np.any(diagonal == 0.0):
            raise ValueError("base energy intersects the finite-size spectrum")
        row_swaps = int(np.count_nonzero(pivots != np.arange(matrix.shape[0])))
        phases.append(float(np.sum(np.angle(diagonal)) + row_swaps * np.pi))
    unwrapped = np.unwrap(np.asarray(phases))
    return float((unwrapped[-1] - unwrapped[0]) / (2.0 * np.pi))


def direct_winding_eq5(
    complex_phase: float,
    *,
    length: int,
    hopping: float,
    potential_strength: float,
    alpha: float,
    base_energy: complex,
    theta_points: int,
) -> float:
    """Evaluate main Eq. (5) directly from finite-matrix determinants."""

    theta = np.linspace(0.0, 2.0 * np.pi, theta_points)
    matrices = [
        aah_hamiltonian(
            length,
            hopping=hopping,
            potential_strength=potential_strength,
            alpha=alpha,
            theta=float(value) / length,
            complex_phase=complex_phase,
            boundary="periodic",
            index_start=1,
        )
        for value in theta
    ]
    return _determinant_winding(matrices, base_energy)


def direct_winding_s12(
    complex_phase: float,
    *,
    length: int,
    hopping: float,
    potential_strength: float,
    alpha: float,
    base_energy: complex,
    theta_points: int,
) -> float:
    """Evaluate the independent H2 determinant route in Supplement Eq. (S-12)."""

    theta = np.linspace(0.0, 2.0 * np.pi, theta_points)
    matrices = [
        h2_hamiltonian(
            length,
            hopping=hopping,
            potential_strength=potential_strength,
            alpha=alpha,
            theta=float(value),
            complex_phase=complex_phase,
        )
        for value in theta
    ]
    return _determinant_winding(matrices, base_energy)


def _rk4_step(
    field: np.ndarray,
    gain: float,
    dt: float,
    derivative: Any,
) -> tuple[np.ndarray, float]:
    k1_field, k1_gain = derivative(field, gain)
    k2_field, k2_gain = derivative(field + 0.5 * dt * k1_field, gain + 0.5 * dt * k1_gain)
    k3_field, k3_gain = derivative(field + 0.5 * dt * k2_field, gain + 0.5 * dt * k2_gain)
    k4_field, k4_gain = derivative(field + dt * k3_field, gain + dt * k3_gain)
    next_field = field + (dt / 6.0) * (k1_field + 2.0 * k2_field + 2.0 * k3_field + k4_field)
    next_gain = gain + (dt / 6.0) * (k1_gain + 2.0 * k2_gain + 2.0 * k3_gain + k4_gain)
    return next_field, float(next_gain)


def transient_laser_spectrum(
    modulation_depth: float,
    *,
    potential_strength: float,
    alpha: float,
    theta: float,
    cavity_loss: float,
    small_signal_gain: float,
    modulation_frequency_ghz: float,
    gain_width_ghz: float,
    gamma_parallel: float,
    mode_limit: int,
    time_step: float,
    final_time: float,
    noise_scale: float,
    seed: int,
) -> dict[str, Any]:
    """Integrate the coupled field/gain equations (8)-(9) with RK4."""

    if gamma_parallel <= 0.0 or time_step <= 0.0 or final_time <= 0.0:
        raise ValueError("gamma_parallel and integration times must be positive")
    modes = np.arange(-mode_limit, mode_limit + 1, dtype=float)
    rng = np.random.default_rng(seed)
    field = noise_scale * (rng.normal(size=modes.size) + 1j * rng.normal(size=modes.size))
    gain = 0.0
    ratio = modulation_frequency_ghz / gain_width_ghz

    def derivative(current_field: np.ndarray, current_gain: float) -> tuple[np.ndarray, float]:
        operator = laser_operator(
            modes,
            modulation_depth=modulation_depth,
            potential_strength=potential_strength,
            alpha=alpha,
            theta=theta,
            cavity_loss=cavity_loss,
            saturated_gain=current_gain,
            modulation_to_gainwidth_ratio=ratio,
        )
        intensity = float(np.vdot(current_field, current_field).real)
        return -1j * (operator @ current_field), gamma_parallel * (small_signal_gain - current_gain * (1.0 + intensity))

    steps = int(round(final_time / time_step))
    for _ in range(steps):
        field, gain = _rk4_step(field, gain, time_step, derivative)
        if not np.all(np.isfinite(field)) or not np.isfinite(gain):
            raise FloatingPointError("transient integration became non-finite")
    spectrum = np.abs(field) ** 2
    intensity = float(spectrum.sum())
    if intensity <= 0.0:
        raise FloatingPointError("transient integration produced zero intensity")
    normalized = spectrum / intensity
    return {
        "mode_indices": modes.astype(int).tolist(),
        "normalized_spectrum": normalized.tolist(),
        "gain": gain,
        "intensity": intensity,
        "bandwidth": spectral_bandwidth(modes, normalized),
        "steps": steps,
    }


def _spectrum_summary(parameters: dict[str, Any], boundary: str) -> dict[str, Any]:
    rows = []
    for phase in parameters["spectral_phases"]:
        values, vectors = normalized_eigensystem(
            aah_hamiltonian(
                int(parameters["length"]),
                hopping=float(parameters["hopping"]),
                potential_strength=float(parameters["potential_strength"]),
                alpha=float(parameters["alpha"]),
                theta=0.0,
                complex_phase=float(phase),
                boundary=boundary,
            )
        )
        ipr = inverse_participation_ratios(vectors)
        rows.append(
            {
                "complex_phase": float(phase),
                "max_abs_imaginary_energy": float(np.max(np.abs(values.imag))),
                "minimum_ipr": float(np.min(ipr)),
                "maximum_ipr": float(np.max(ipr)),
            }
        )
    finite = all(np.isfinite(list(row.values())).all() for row in rows)
    return {"boundary": boundary, "rows": rows, "passed": bool(finite)}


def _edge_classifier_matrix(parameters: dict[str, Any]) -> dict[str, Any]:
    rows = []
    length = int(parameters["length"])
    sites = np.arange(length, dtype=float)
    for phase in parameters["complex_phases"]:
        _, vectors = normalized_eigensystem(
            aah_hamiltonian(
                length,
                hopping=float(parameters["hopping"]),
                potential_strength=float(parameters["potential_strength"]),
                alpha=float(parameters["alpha"]),
                complex_phase=float(phase),
                boundary="open",
            )
        )
        weights = np.abs(vectors) ** 2
        weights /= weights.sum(axis=0, keepdims=True)
        ipr = inverse_participation_ratios(vectors)
        centers = sites @ weights
        candidates: dict[str, dict[str, int]] = {}
        for width in parameters["edge_widths"]:
            for threshold in parameters["edge_weight_thresholds"]:
                left, right = edge_state_counts(vectors, edge_width=int(width), minimum_edge_weight=float(threshold))
                candidates[f"boundary_weight_w{width}_p{threshold}"] = {"left": left, "right": right}
            minimum_ipr = float(parameters["center_ipr_minimum"])
            candidates[f"center_ipr_w{width}"] = {
                "left": int(np.count_nonzero((centers < float(width)) & (ipr >= minimum_ipr))),
                "right": int(np.count_nonzero((centers >= length - float(width)) & (ipr >= minimum_ipr))),
            }
        rows.append({"complex_phase": float(phase), "candidate_counts": candidates})
    return {
        "rows": rows,
        "paper_exact_classifier_status": "input_blocked",
        "blocked_input_schema": parameters["blocked_input_schema"],
        "passed": bool(rows and all(row["candidate_counts"] for row in rows)),
    }


def _central_gap_midpoints(parameters: dict[str, Any]) -> list[float]:
    length = int(parameters["length"])
    values = np.linalg.eigvalsh(
        aah_hamiltonian(
            length,
            hopping=float(parameters["hopping"]),
            potential_strength=float(parameters["potential_strength"]),
            alpha=float(parameters["alpha"]),
            complex_phase=0.0,
            boundary="periodic",
        ).real
    )
    gaps = np.diff(values)
    centres = 0.5 * (values[:-1] + values[1:])
    energy_limit = float(parameters["central_energy_fraction"]) * float(np.max(np.abs(values)))
    candidates = [(float(gap), float(centre)) for gap, centre in zip(gaps, centres, strict=True) if abs(centre) <= energy_limit]
    candidates.sort(reverse=True)
    count = int(parameters["base_energy_count"])
    if len(candidates) < count:
        raise ValueError("not enough central spectral gaps for the requested E_B sweep")
    return sorted(centre for _, centre in candidates[:count])


def run_campaign(config: dict[str, Any]) -> dict[str, Any]:
    parameters = config["parameters"]
    lattice = parameters["lattice"]
    target_checks: dict[str, dict[str, Any]] = {}

    target_checks["T001"] = _spectrum_summary(lattice, "periodic")
    target_checks["T003"] = _spectrum_summary(lattice, "open")

    laser_parameters = parameters["laser_transient"]
    laser_rows = {}
    for index, depth in enumerate(laser_parameters["modulation_depths"]):
        laser_rows[str(depth)] = transient_laser_spectrum(
            float(depth),
            potential_strength=float(laser_parameters["potential_strength"]),
            alpha=float(laser_parameters["alpha"]),
            theta=float(laser_parameters["theta"]),
            cavity_loss=float(laser_parameters["cavity_loss"]),
            small_signal_gain=float(laser_parameters["small_signal_gain"]),
            modulation_frequency_ghz=float(laser_parameters["modulation_frequency_ghz"]),
            gain_width_ghz=float(laser_parameters["gain_width_ghz"]),
            gamma_parallel=float(laser_parameters["gamma_parallel_attestation_value"]),
            mode_limit=int(laser_parameters["mode_limit"]),
            time_step=float(laser_parameters["time_step"]),
            final_time=float(laser_parameters["final_time"]),
            noise_scale=float(laser_parameters["noise_scale"]),
            seed=int(laser_parameters["seed"]) + index,
        )
    target_checks["T002"] = {
        "profiles": laser_rows,
        "paper_exact_status": "input_blocked",
        "blocked_input_schema": laser_parameters["blocked_input_schema"],
        "passed": bool(all(np.isfinite(row["bandwidth"]) and row["intensity"] > 0.0 for row in laser_rows.values())),
    }

    etalon_parameters = parameters["etalon"]
    frequency = np.linspace(float(etalon_parameters["frequency_min"]), float(etalon_parameters["frequency_max"]), int(etalon_parameters["points"]))
    transmission = etalon_transmission(
        frequency,
        refractive_index=float(etalon_parameters["refractive_index"]),
        phase=float(etalon_parameters["phase"]),
    )
    error = np.abs(transmission.exact - transmission.first_order)
    target_checks["T004"] = {
        "reflectance": transmission.reflectance,
        "maximum_first_order_error": float(np.max(error)),
        "all_components_finite": bool(np.isfinite(transmission.exact.real).all() and np.isfinite(transmission.exact.imag).all() and np.isfinite(transmission.first_order.real).all() and np.isfinite(transmission.first_order.imag).all()),
    }
    target_checks["T004"]["passed"] = target_checks["T004"]["all_components_finite"]

    winding_parameters = parameters["winding"]
    winding_rows = []
    for phase in winding_parameters["complex_phases"]:
        common = {
            "length": int(winding_parameters["length"]),
            "hopping": float(winding_parameters["hopping"]),
            "potential_strength": float(winding_parameters["potential_strength"]),
            "alpha": float(winding_parameters["alpha"]),
            "base_energy": complex(float(winding_parameters["base_energy"])),
            "theta_points": int(winding_parameters["theta_points"]),
        }
        eq5 = direct_winding_eq5(float(phase), **common)
        eqs12 = direct_winding_s12(float(phase), **common)
        winding_rows.append({"complex_phase": float(phase), "eq5": eq5, "eqs12": eqs12, "absolute_difference": abs(eq5 - eqs12)})
    target_checks["T005"] = {
        "rows": winding_rows,
        "paper_scale_status": "code_ready_not_run",
        "passed": bool(all(np.isfinite([row["eq5"], row["eqs12"]]).all() and row["absolute_difference"] <= float(winding_parameters["route_tolerance"]) for row in winding_rows)),
    }

    target_checks["T006"] = _edge_classifier_matrix(parameters["edge_classifier"])

    base_energy_parameters = parameters["base_energy_sweep"]
    base_energies = _central_gap_midpoints(base_energy_parameters)
    windings = [
        direct_winding_eq5(
            float(base_energy_parameters["complex_phase"]),
            length=int(base_energy_parameters["length"]),
            hopping=float(base_energy_parameters["hopping"]),
            potential_strength=float(base_energy_parameters["potential_strength"]),
            alpha=float(base_energy_parameters["alpha"]),
            base_energy=complex(value),
            theta_points=int(base_energy_parameters["theta_points"]),
        )
        for value in base_energies
    ]
    invariant = bool(max(windings) - min(windings) <= float(base_energy_parameters["winding_tolerance"]))
    target_checks["T007"] = {
        "base_energy_selection": "largest formula-derived gaps inside the predeclared central energy window",
        "base_energies": base_energies,
        "windings": windings,
        "claim_invariant_on_declared_set": invariant,
        "passed": bool(all(np.isfinite(windings))),
    }

    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": "attested" if target_checks[target_id]["passed"] else "failed",
            "scientific_status": "unchanged",
        }
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    return {
        "schema_version": 1,
        "paper_id": "1905.09460",
        "profile": config["profile"],
        "purpose": "implementation_attestation_only",
        "scientific_coverage_changed": False,
        "source_pixels_used": False,
        "author_arrays_used": False,
        "author_code_used": False,
        "target_checks": target_checks,
        "item_results": item_results,
        "status": "passed" if all(row["passed"] for row in target_checks.values()) else "failed",
    }
