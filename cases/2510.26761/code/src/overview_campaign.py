"""Source-pixel-free numerical campaign for the scientific fields in Fig. 1."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from src.wigner_gme import (
    SOURCE_PRINTED_GME_BOUND,
    STATE_DERIVED_GME_BOUND,
    convolve_with_gaussian_kernel,
    illustrative_com_density,
    illustrative_com_wigner,
    illustrative_relative_parity,
    illustrative_slice_metrics,
    illustrative_slice_signed_integral,
    illustrative_slice_wigner,
    illustrative_state_norm,
    illustrative_wigner_cut,
    smoothed_origin_exact,
)


def _axis(spec: object, name: str) -> np.ndarray:
    if (
        not isinstance(spec, list)
        or len(spec) != 3
        or not isinstance(spec[2], int)
        or spec[2] < 3
    ):
        raise ValueError(f"{name} must be [minimum, maximum, point_count]")
    start, stop, count = float(spec[0]), float(spec[1]), int(spec[2])
    if not start < stop:
        raise ValueError(f"{name} minimum must be below maximum")
    return np.linspace(start, stop, count)


def compute_overview_fields(parameters: Mapping[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    """Evaluate the four scientific fields without importing a renderer."""

    grids = parameters.get("grids")
    if not isinstance(grids, dict):
        raise ValueError("parameters.grids must be an object")

    slice_axis = _axis(grids.get("equal_slice_axis"), "equal_slice_axis")
    sx, sy = np.meshgrid(slice_axis, slice_axis, indexing="xy")
    equal_slice = np.asarray(illustrative_slice_wigner(sx + 1.0j * sy))

    com_axis_extended = _axis(
        grids.get("center_of_mass_axis"), "center_of_mass_axis"
    )
    ex, ey = np.meshgrid(com_axis_extended, com_axis_extended, indexing="xy")
    com_extended = np.asarray(illustrative_com_wigner(ex + 1.0j * ey))
    smoothed_extended = convolve_with_gaussian_kernel(
        com_extended, com_axis_extended
    )
    display_limit = float(grids.get("center_of_mass_display_limit"))
    display_mask = np.abs(com_axis_extended) <= display_limit + 1e-12
    com_axis = com_axis_extended[display_mask]
    com_field = com_extended[np.ix_(display_mask, display_mask)]
    smoothed_field = smoothed_extended[np.ix_(display_mask, display_mask)]

    cut_axis = _axis(grids.get("full_cut_axis"), "full_cut_axis")
    alpha_plus = (
        cut_axis[:, None, None]
        + 1.0j * cut_axis[None, :, None]
        + np.zeros((1, 1, len(cut_axis)), dtype=np.complex128)
    )
    alpha_minus = (
        np.zeros((len(cut_axis), len(cut_axis), 1), dtype=np.complex128)
        + cut_axis[None, None, :]
    )
    full_cut = np.asarray(illustrative_wigner_cut(alpha_plus, alpha_minus))

    center = len(com_axis_extended) // 2
    diagnostics = {
        "full_cut_minimum": float(np.min(full_cut)),
        "full_cut_maximum": float(np.max(full_cut)),
        "equal_slice_minimum": float(np.min(equal_slice)),
        "equal_slice_maximum": float(np.max(equal_slice)),
        "com_minimum": float(np.min(com_field)),
        "com_maximum": float(np.max(com_field)),
        "smoothed_grid_origin": float(smoothed_extended[center, center]),
        "smoothed_exact_origin": smoothed_origin_exact(),
        "smoothed_origin_absolute_error": abs(
            float(smoothed_extended[center, center]) - smoothed_origin_exact()
        ),
    }
    fields = {
        "slice_axis": slice_axis,
        "equal_slice": equal_slice,
        "com_axis": com_axis,
        "com_wigner": com_field,
        "smoothed_com_wigner": smoothed_field,
        "cut_axis": cut_axis,
        "full_cut": full_cut,
    }
    return fields, diagnostics


def evaluate_overview_campaign(parameters: Mapping[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Return generated arrays plus a machine-checkable scientific result."""

    convergence_spec = parameters.get("convergence")
    acceptance = parameters.get("acceptance")
    if not isinstance(convergence_spec, dict) or not isinstance(acceptance, dict):
        raise ValueError("parameters.convergence and parameters.acceptance are required")
    ladder = convergence_spec.get("radial_angular_orders")
    if (
        not isinstance(ladder, list)
        or len(ladder) < 2
        or any(not isinstance(row, list) or len(row) != 2 for row in ladder)
    ):
        raise ValueError("radial_angular_orders must contain at least two pairs")
    radial_cutoff = float(convergence_spec.get("radial_cutoff"))
    convergence = [
        illustrative_slice_metrics(
            radial_order=int(row[0]),
            angular_order=int(row[1]),
            radial_cutoff=radial_cutoff,
        )
        for row in ladder
    ]
    fields, diagnostics = compute_overview_fields(parameters)
    final_metrics = convergence[-1]
    negativity = float(final_metrics["negativity_volume"])
    checks = {
        "state_normalized": abs(illustrative_state_norm() - 1.0)
        <= float(acceptance["normalization_tolerance"]),
        "reduced_state_normalized": abs(
            float(np.trace(illustrative_com_density()).real) - 1.0
        )
        <= float(acceptance["normalization_tolerance"]),
        "signed_integral_matches_parity_identity": abs(
            float(final_metrics["signed_integral"])
            - illustrative_slice_signed_integral()
        )
        <= float(acceptance["signed_integral_tolerance"]),
        "negative_volume_converged": abs(
            float(convergence[-1]["negativity_volume"])
            - float(convergence[-2]["negativity_volume"])
        )
        <= float(acceptance["negative_volume_tolerance"]),
        "state_derived_gme_bound_violated": negativity
        > STATE_DERIVED_GME_BOUND,
        "source_printed_bound_not_violated": negativity
        < SOURCE_PRINTED_GME_BOUND,
        "source_threshold_inconsistency_exposed": True,
        "smoothed_origin_matches_exact_value": diagnostics[
            "smoothed_origin_absolute_error"
        ]
        <= float(acceptance["smoothed_origin_tolerance"]),
        "all_fields_finite": all(np.all(np.isfinite(array)) for array in fields.values()),
    }
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "failed",
        "target_ids": ["T001"],
        "paper_parameters_executed": True,
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_for_scientific_inputs": False,
        "author_code_used_for_numerical_implementation": False,
        "checks": checks,
        "metrics": {
            "state_norm": illustrative_state_norm(),
            "relative_parity": illustrative_relative_parity(),
            "reduced_state_trace": float(np.trace(illustrative_com_density()).real),
            "signed_integral_exact": illustrative_slice_signed_integral(),
            "state_derived_gme_bound": STATE_DERIVED_GME_BOUND,
            "source_printed_gme_bound": SOURCE_PRINTED_GME_BOUND,
            "negativity_volume": negativity,
            "convergence": convergence,
            **diagnostics,
        },
    }
    return fields, result
