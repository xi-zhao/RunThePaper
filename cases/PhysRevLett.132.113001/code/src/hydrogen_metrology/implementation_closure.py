"""Corrected clean-room implementations for four previously invalid items."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import erf

from .metrology import regression_curves


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


def mode_shift_mhz(gamma: float, doppler_sigma_mhz: float) -> float:
    """Positive mode shift of the asymmetric Doppler factor in method Eq. 4."""

    if doppler_sigma_mhz <= 0.0:
        raise ValueError("doppler_sigma_mhz must be positive")

    def negative_shape(offset: float) -> float:
        gaussian = np.exp(-0.5 * (offset / doppler_sigma_mhz) ** 2)
        asymmetry = 1.0 + erf(
            gamma * offset / (np.sqrt(2.0) * doppler_sigma_mhz)
        )
        return -float(gaussian * asymmetry)

    result = minimize_scalar(
        negative_shape,
        bounds=(-8.0 * doppler_sigma_mhz, 8.0 * doppler_sigma_mhz),
        method="bounded",
        options={"xatol": 1.0e-13},
    )
    if not result.success:
        raise RuntimeError("failed to locate asymmetric-component mode")
    return float(result.x)


def method_lineshape(
    frequencies_mhz: np.ndarray,
    *,
    doppler_shift_mhz: float,
    doppler_sigma_mhz: float,
    field_sigma_mhz: float,
    asymmetry_gamma: float,
    doppler_weights: list[float],
    families: list[dict[str, Any]],
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Evaluate the full i,m_f sum of method-paper Eqs. 4 and 5.

    Every Stark shift and intensity is supplied explicitly.  The function
    therefore works for a complete paper parameter package but never invents
    missing fitted values.
    """

    frequencies = np.asarray(frequencies_mhz, dtype=float)
    if frequencies.ndim != 1 or not np.all(np.isfinite(frequencies)):
        raise ValueError("frequencies_mhz must be one-dimensional and finite")
    if len(doppler_weights) != 2 or any(weight < 0.0 for weight in doppler_weights):
        raise ValueError("doppler_weights must contain two nonnegative values")
    delta_nu = mode_shift_mhz(asymmetry_gamma, doppler_sigma_mhz)
    total = np.zeros_like(frequencies)
    rows: list[dict[str, Any]] = []
    for family in families:
        k_value = int(family["k"])
        width = float(
            np.sqrt(doppler_sigma_mhz**2 + abs(k_value) * field_sigma_mhz**2)
        )
        components = family.get("mf_components")
        if not isinstance(components, list) or not components:
            raise ValueError("every k family requires non-empty mf_components")
        for component in components:
            mf = int(component["mf"])
            stark_shift = float(component["stark_shift_mhz"])
            mf_intensity = float(component["intensity"])
            if mf_intensity < 0.0:
                raise ValueError("m_f intensities must be nonnegative")
            for index, orientation in enumerate((-1, 1)):
                center = stark_shift + orientation * (doppler_shift_mhz - delta_nu)
                offset = frequencies - center
                gaussian = np.exp(-0.5 * (offset / width) ** 2)
                asymmetry = 1.0 + erf(
                    orientation
                    * asymmetry_gamma
                    * offset
                    / (np.sqrt(2.0) * doppler_sigma_mhz)
                )
                contribution = doppler_weights[index] * mf_intensity * gaussian * asymmetry
                total += contribution
                rows.append(
                    {
                        "k": k_value,
                        "mf": mf,
                        "doppler_component": index + 1,
                        "orientation": orientation,
                        "center_mhz": center,
                        "stark_shift_mhz": stark_shift,
                        "gaussian_sigma_mhz": width,
                        "erf_sigma_mhz": doppler_sigma_mhz,
                        "weight": doppler_weights[index] * mf_intensity,
                        "expected_mode_mhz": stark_shift + orientation * doppler_shift_mhz,
                    }
                )
    maximum = float(np.max(total))
    if maximum <= 0.0:
        raise ValueError("calculated line shape has no positive intensity")
    return total / maximum, rows


def assemble_binding_terms(
    term_package: list[dict[str, Any]], required_terms: list[str]
) -> dict[str, Any]:
    """Strict decimal sum for a fully sourced QED binding-energy package."""

    rows = term_package if isinstance(term_package, list) else []
    by_name = {
        str(row.get("name") or ""): row
        for row in rows
        if isinstance(row, dict) and str(row.get("name") or "")
    }
    missing = [name for name in required_terms if name not in by_name]
    unknown = sorted(set(by_name) - set(required_terms))
    invalid: list[str] = []
    total = Decimal("0")
    if not missing and not unknown:
        for name in required_terms:
            row = by_name[name]
            if row.get("unit") != "kHz" or not str(row.get("source_ref") or "").strip() or not str(row.get("source_sha256") or "").strip():
                invalid.append(name)
                continue
            try:
                total += Decimal(str(row["value_khz"]))
            except (InvalidOperation, KeyError):
                invalid.append(name)
    complete = not missing and not unknown and not invalid
    return {
        "status": "ready" if complete else "blocked_on_paper_input",
        "required_terms": required_terms,
        "missing_terms": missing,
        "unknown_terms": unknown,
        "invalid_terms": invalid,
        "total_khz": str(total) if complete else None,
        "input_schema": {
            "term_package": [
                {
                    "name": "one required term name",
                    "value_khz": "exact decimal string",
                    "unit": "kHz",
                    "source_ref": "equation/table locator",
                    "source_sha256": "hash of the frozen source containing the value",
                }
            ]
        },
    }


def run_campaign(config: dict[str, Any], profile_name: str) -> dict[str, dict[str, Any]]:
    if config.get("paper_id") != "PhysRevLett.132.113001":
        raise ValueError("configuration paper_id does not match this case")
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise ValueError(f"unknown profile: {profile_name}")
    target_items = config.get("target_items")
    runners: dict[str, Callable[[dict[str, Any], dict[str, Any]], TargetResult]] = {
        "T003": _line_shape,
        "T005": _field_regression,
        "T006": _doppler_regression,
        "T013": _theory_binding_boundary,
    }
    if not isinstance(target_items, dict) or set(target_items) != set(runners):
        raise ValueError("target item map and runner map differ")
    flattened = [item for items in target_items.values() for item in items]
    if len(flattened) != len(set(flattened)):
        raise ValueError("each atomic item must map exactly once")
    profile = profiles[profile_name]
    paper = config["paper_parameters"]
    return {
        target_id: runners[target_id](profile, paper).payload(target_items[target_id])
        for target_id in target_items
    }


def _line_shape(profile: dict[str, Any], paper: dict[str, Any]) -> TargetResult:
    fixture = paper["line_shape_method_validation_fixture"]
    frequencies = np.linspace(
        float(profile["frequency_min_mhz"]),
        float(profile["frequency_max_mhz"]),
        int(profile["frequency_points"]),
    )
    intensity, rows = method_lineshape(frequencies, **fixture)
    expected_components = 2 * sum(len(family["mf_components"]) for family in fixture["families"])
    widths_correct = all(
        abs(
            row["gaussian_sigma_mhz"]
            - np.sqrt(fixture["doppler_sigma_mhz"] ** 2 + abs(row["k"]) * fixture["field_sigma_mhz"] ** 2)
        )
        < 1.0e-12
        for row in rows
    )
    return TargetResult(
        "T003",
        "passed",
        "method_validation_not_paper_parameters",
        {"frequency_mhz": frequencies, "normalized_intensity": intensity, "components": rows},
        {
            "full_i_mf_sum": len(rows) == expected_components,
            "finite_nonnegative": bool(np.all(np.isfinite(intensity)) and np.min(intensity) >= 0.0),
            "normalized": abs(float(np.max(intensity)) - 1.0) < 1.0e-12,
            "published_width_expression": widths_correct,
            "erf_uses_doppler_width": all(row["erf_sigma_mhz"] == fixture["doppler_sigma_mhz"] for row in rows),
        },
        {
            "implementation_attestation_only": True,
            "scientific_coverage_promotion": False,
            "remaining_scientific_boundary": "The equation path is repaired, but paper-fitted m_f Stark shifts/intensities and line-shape parameters are not frozen; this fixture is not Fig. 3 evidence.",
        },
    )


def _field_regression(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    field = np.linspace(0.0, float(profile["field_max_v_per_cm"]), int(profile["field_points"]))
    curves = regression_curves(field, np.asarray([0.0, 1.0]))
    return TargetResult(
        "T005", "passed", "published_domain_formula_check",
        {"field_v_per_cm": curves["field"], "trend_khz": curves["field_trend_khz"], "one_sigma_khz": curves["field_band_khz"]},
        {"published_domain": abs(float(field[0])) < 1.0e-12 and abs(float(field[-1]) - 1.6) < 1.0e-12, "quadratic_trend": bool(np.allclose(curves["field_trend_khz"], -0.3 * field**2)), "quadratic_band": bool(np.allclose(curves["field_band_khz"], 3.5 * field**2))},
        {"implementation_attestation_only": True, "scientific_coverage_promotion": False, "remaining_scientific_boundary": "The corrected published-domain curve still lacks a fresh scientific acceptance decision and source-data residual re-fit."},
    )


def _doppler_regression(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    doppler = np.linspace(0.0, float(profile["doppler_max_mhz"]), int(profile["doppler_points"]))
    curves = regression_curves(np.asarray([0.0, 1.0]), doppler)
    return TargetResult(
        "T006", "passed", "published_domain_formula_check",
        {"doppler_mhz": curves["doppler"], "trend_khz": curves["doppler_trend_khz"], "one_sigma_khz": curves["doppler_band_khz"]},
        {"published_domain": abs(float(doppler[0])) < 1.0e-12 and abs(float(doppler[-1]) - 9.0) < 1.0e-12, "linear_trend": bool(np.allclose(curves["doppler_trend_khz"], -0.9 * doppler)), "linear_band": bool(np.allclose(curves["doppler_band_khz"], 1.8 * doppler))},
        {"implementation_attestation_only": True, "scientific_coverage_promotion": False, "remaining_scientific_boundary": "The corrected published-domain curve still lacks a fresh scientific acceptance decision and source-data residual re-fit."},
    )


def _theory_binding_boundary(_: dict[str, Any], paper: dict[str, Any]) -> TargetResult:
    result = assemble_binding_terms(paper["theory_binding_term_package"], paper["required_theory_binding_terms"])
    return TargetResult(
        "T013",
        result["status"],
        "strict_input_boundary",
        result,
        {"schema_declared": bool(result["input_schema"]), "blocker_complete": result["status"] == "blocked_on_paper_input" and set(result["missing_terms"]) == set(result["required_terms"])},
        {"implementation_attestation_only": True, "scientific_coverage_promotion": False, "remaining_scientific_boundary": "The full cited QED term package is absent from the frozen case. The runner fails closed until every named term has a source locator and source hash."},
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
    return value
