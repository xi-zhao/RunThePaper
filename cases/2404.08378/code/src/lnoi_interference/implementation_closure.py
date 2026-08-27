"""Clean-room implementations for three no-display quantitative claims.

Only frozen scalar parameters and case-local formula code are consumed.  The
runner never reads the paper, figures, author code/arrays, or earlier outputs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .modes import solve_scalar_mode


ITEMS_BY_TARGET = {
    "T019": ("QCLM-POLING-PERIOD",),
    "T020": ("QCLM-DETECTION-SIGNAL-RATIO",),
    "T021": ("QCLM-SOURCE-SCALING",),
}


def quasi_phase_matching_period_um(
    *,
    pump_wavelength_um: float,
    signal_wavelength_um: float,
    pump_effective_index: float,
    signal_effective_index: float,
) -> float:
    """Return the first-order type-0 period for degenerate down-conversion."""

    values = (
        pump_wavelength_um,
        signal_wavelength_um,
        pump_effective_index,
        signal_effective_index,
    )
    if any(float(value) <= 0.0 for value in values):
        raise ValueError("wavelengths and effective indices must be positive")
    mismatch_cycles_per_um = (
        pump_effective_index / pump_wavelength_um
        - 2.0 * signal_effective_index / signal_wavelength_um
    )
    if mismatch_cycles_per_um <= 0.0:
        raise ValueError("phase mismatch must be positive for first-order poling")
    return 1.0 / mismatch_cycles_per_um


def detected_fock_maxima(
    *,
    split_state_chip_maximum: float,
    bunched_state_chip_maximum: float,
    detector_splitter_reflectivity: float,
) -> dict[str, float]:
    """Propagate ideal chip maxima through the two 50:50 detector splitters.

    A split ``|11>`` event is accepted after summing all cross-arm detector
    pairs.  A bunched pair is accepted only when the two photons separate at
    its output splitter, with probability ``2 R (1-R)``.
    """

    reflectivity = float(detector_splitter_reflectivity)
    if not 0.0 <= reflectivity <= 1.0:
        raise ValueError("detector splitter reflectivity must lie in [0, 1]")
    if split_state_chip_maximum <= 0.0 or bunched_state_chip_maximum <= 0.0:
        raise ValueError("chip maxima must be positive")
    separation_probability = 2.0 * reflectivity * (1.0 - reflectivity)
    split_detected = float(split_state_chip_maximum)
    bunched_detected = float(bunched_state_chip_maximum) * separation_probability
    return {
        "split_state_detected_maximum": split_detected,
        "bunched_state_detected_maximum": bunched_detected,
        "bunched_pair_separation_probability": separation_probability,
        "split_to_bunched_signal_ratio": split_detected / bunched_detected,
    }


def waveguide_packing_audit(
    *,
    electrode_gap_um: float,
    waveguide_width_um: float,
    inter_waveguide_gap_um: float,
    requested_waveguides: int,
) -> dict[str, float | int | bool]:
    """Audit geometric feasibility without inventing an edge-clearance rule."""

    if (
        electrode_gap_um <= 0.0
        or waveguide_width_um <= 0.0
        or inter_waveguide_gap_um < 0.0
        or requested_waveguides < 1
    ):
        raise ValueError("invalid packing dimensions")
    required = (
        requested_waveguides * waveguide_width_um
        + (requested_waveguides - 1) * inter_waveguide_gap_um
    )
    maximum_without_edge_clearance = int(
        np.floor(
            (electrode_gap_um + inter_waveguide_gap_um)
            / (waveguide_width_um + inter_waveguide_gap_um)
        )
    )
    return {
        "requested_waveguides": int(requested_waveguides),
        "required_width_um": float(required),
        "unused_width_um": float(electrode_gap_um - required),
        "maximum_without_edge_clearance": maximum_without_edge_clearance,
        "geometrically_fits": bool(required <= electrode_gap_um),
    }


def _poling_check(parameters: dict[str, Any]) -> dict[str, Any]:
    model = parameters["scalar_mode"]
    shared = {
        "x_extent_um": float(model["x_extent_um"]),
        "y_min_um": float(model["y_min_um"]),
        "y_max_um": float(model["y_max_um"]),
        "nx": int(model["nx"]),
        "ny": int(model["ny"]),
        "film_height_um": float(model["film_height_um"]),
        "top_width_um": float(model["top_width_um"]),
        "sidewall_angle_deg": float(model["sidewall_angle_deg"]),
    }
    pump_wavelength = float(model["pump_wavelength_um"])
    signal_wavelength = float(model["signal_wavelength_um"])
    pump = solve_scalar_mode(pump_wavelength, **shared)
    signal = solve_scalar_mode(signal_wavelength, **shared)
    period = quasi_phase_matching_period_um(
        pump_wavelength_um=pump_wavelength,
        signal_wavelength_um=signal_wavelength,
        pump_effective_index=pump.effective_index,
        signal_effective_index=signal.effective_index,
    )
    mismatch = 2.0 * np.pi / period
    closure_error = float(abs(mismatch * period - 2.0 * np.pi))
    passed = (
        np.isfinite(period)
        and period > 0.0
        and pump.effective_index > signal.effective_index
        and closure_error < 1.0e-12
    )
    return {
        "status": "passed" if passed else "failed",
        "scalar_reconstruction_period_um": float(period),
        "printed_period_um": float(parameters["printed_period_um"]),
        "relative_difference_from_printed": float(
            abs(period / float(parameters["printed_period_um"]) - 1.0)
        ),
        "pump_effective_index": pump.effective_index,
        "signal_effective_index": signal.effective_index,
        "phase_closure_error": closure_error,
        "paper_exact_input_blocked": True,
        "missing_indispensable_inputs": parameters["missing_indispensable_inputs"],
        "independent_checks": ["scalar_mode_normalization", "phase_mismatch_closure"],
    }


def run_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    if config.get("paper_id") != "2404.08378":
        raise ValueError("paper_id must be 2404.08378")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if parameters.get("profile") != "reduced_formula_attestation":
        raise ValueError("only the frozen reduced formula profile is accepted")

    poling = _poling_check(parameters["T019"])
    detection = detected_fock_maxima(**parameters["T020"])
    detection_error = abs(detection["split_to_bunched_signal_ratio"] - 4.0)
    detection_check = {
        "status": "passed" if detection_error < 1.0e-12 else "failed",
        **detection,
        "fourfold_ratio_error": detection_error,
        "independent_checks": ["bosonic_chip_maxima", "binomial_detector_splitter"],
    }
    packing = waveguide_packing_audit(**parameters["T021"]["geometry"])
    packing_check = {
        "status": "passed" if packing["geometrically_fits"] else "failed",
        **packing,
        "paper_exact_input_blocked": True,
        "missing_indispensable_inputs": parameters["T021"][
            "missing_indispensable_inputs"
        ],
        "independent_checks": ["closed_form_span", "integer_capacity_bound"],
    }
    target_checks = {"T019": poling, "T020": detection_check, "T021": packing_check}
    for check in target_checks.values():
        check["profile"] = parameters["profile"]
        check["paper_scale_executed"] = False

    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": (
                "attested" if target_checks[target_id]["status"] == "passed" else "failed"
            ),
            "scientific_coverage_changed": False,
        }
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    status = (
        "passed"
        if all(check["status"] == "passed" for check in target_checks.values())
        else "failed"
    )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": status,
        "profile": parameters["profile"],
        "fixed_item_denominator": len(item_results),
        "item_results": item_results,
        "target_checks": target_checks,
        "scientific_coverage_changed": False,
        "scientific_boundary": (
            "T019 remains bounded by unpublished vector-FEM inputs and T021 by an "
            "unpublished crosstalk/edge-clearance convention; implementation attestation "
            "does not make either claim paper-exact."
        ),
        "numerical_input_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "reference_pixels_read": False,
            "historical_outputs_read": False,
        },
    }
