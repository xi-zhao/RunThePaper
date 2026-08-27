"""Paper-scale, no-render scientific bundle for arXiv:2605.02873.

The numerical generator consumes only the frozen JSON configuration and the
independently derived Fresnel implementation.  Printed paper values are used
only after generation as comparison references; paper images, author arrays,
and author source code are not inputs.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .try_fresnel import Geometry, fresnel_field, noise_inner, solve_main, width_scan


TARGET_STEMS = {
    "T-FIG001A": "fig001a_baseline",
    "T-FIG001B": "fig001b_scores",
    "T-FIG001C": "fig001c_codes",
    "T-FIG001D": "fig001d_retention",
    "T-FIGS001": "figs001_width_scan",
}

FORMULA_DEPENDENCIES = {
    "T-FIG001A": ["EQC001", "EQC002"],
    "T-FIG001B": ["EQC001", "EQC002", "EQC003"],
    "T-FIG001C": ["EQC002", "EQC003", "EQC004", "EQC005", "EQC007"],
    "T-FIG001D": ["EQC003", "EQC004", "EQC005", "EQC006", "EQC007"],
    "T-FIGS001": ["EQC001", "EQC002", "EQC003", "EQC004", "EQC008"],
}


def _write_csv(path: Path, header: list[str], rows: Iterable[Iterable[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _data_ref(stem: str) -> str:
    return f"outputs/data/{stem}.csv"


def _check_ref(stem: str) -> str:
    return f"outputs/checks/{stem}_science.json"


def _assertion(
    assertion_id: str,
    tier: str,
    passed: bool,
    claim: str,
    evidence: str,
) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "tier": tier,
        "essential": True,
        "status": "passed" if passed else "failed",
        "evidence": evidence,
        "claim": claim,
    }


def _write_check(
    output_root: Path,
    target_id: str,
    *,
    parameters: dict[str, Any],
    metrics: dict[str, Any],
    assertions: list[dict[str, Any]],
) -> bool:
    stem = TARGET_STEMS[target_id]
    passed = all(item["status"] == "passed" for item in assertions)
    payload = {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "paper_id": "2605.02873",
        "target_id": target_id,
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "scientific_role": "theory_numerical",
        "generated_data_provenance": "independent_numerics",
        "formula_dependencies": FORMULA_DEPENDENCIES[target_id],
        "parameters": parameters,
        "metrics": metrics,
        "physics_assertions": assertions,
        "artifacts": {
            "data": _data_ref(stem),
            "figure": f"outputs/figures/{stem}.png",
        },
        "scientific_input_boundary": {
            "paper_images_used": False,
            "author_arrays_used": False,
            "author_code_used": False,
            "printed_results_used_for_comparison_only": True,
        },
    }
    _write_json(output_root / "checks" / f"{stem}_science.json", payload)
    return passed


def _relative_frobenius(generated: np.ndarray, reference: np.ndarray) -> float:
    return float(np.linalg.norm(generated - reference) / np.linalg.norm(reference))


def _zero_crossings(values: np.ndarray) -> int:
    signs = np.sign(values)
    nonzero = signs[signs != 0.0]
    return int(np.sum(nonzero[1:] != nonzero[:-1]))


def _geometry(parameters: dict[str, Any]) -> Geometry:
    geometry = parameters.get("geometry")
    if not isinstance(geometry, dict):
        raise ValueError("parameters.geometry must be an object")
    return Geometry(**geometry)


def run_bundle(config_path: Path, output_root: Path) -> dict[str, Any]:
    """Regenerate all five scorecard datasets and their scientific checks."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "2605.02873":
        raise ValueError("configuration paper_id must be 2605.02873")
    if config.get("mode") != "final_reproduction":
        raise ValueError("final bundle requires mode=final_reproduction")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("configuration must contain a parameters object")

    geometry = _geometry(parameters)
    main = parameters.get("main_numerics")
    scan = parameters.get("width_scan")
    references = parameters.get("paper_references")
    acceptance = parameters.get("acceptance")
    if not all(isinstance(item, dict) for item in (main, scan, references, acceptance)):
        raise ValueError(
            "main_numerics, width_scan, paper_references, and acceptance must be objects"
        )

    y_points = int(main["y_points"])
    quadrature_order = int(main["quadrature_order"])
    convergence_y_points = int(main["convergence_y_points"])
    convergence_quadrature_order = int(main["convergence_quadrature_order"])
    solution = solve_main(
        geometry=geometry,
        y_points=y_points,
        quadrature_order=quadrature_order,
    )
    converged = solve_main(
        geometry=geometry,
        y_points=convergence_y_points,
        quadrature_order=convergence_quadrature_order,
    )
    reported_parameters = {
        "geometry": parameters["geometry"],
        "y_points": y_points,
        "slit_quadrature_order": quadrature_order,
        "convergence_y_points": convergence_y_points,
        "convergence_slit_quadrature_order": convergence_quadrature_order,
    }

    statuses = [
        _panel_a(output_root, solution, converged, reported_parameters, acceptance),
        _panel_b(
            output_root,
            solution,
            converged,
            reported_parameters,
            quadrature_order,
            acceptance,
        ),
        _panel_c(output_root, solution, converged, reported_parameters, acceptance),
        _panel_d(
            output_root,
            solution,
            converged,
            reported_parameters,
            references,
            acceptance,
        ),
        _supplement_scan(
            output_root,
            geometry,
            scan,
            references,
            acceptance,
            reported_parameters,
        ),
    ]
    summary = {
        "schema_version": 1,
        "paper_id": "2605.02873",
        "status": "passed" if all(statuses) else "failed",
        "mode": config["mode"],
        "target_ids": list(TARGET_STEMS),
        "scientific_inputs": ["frozen_config", "independent_formula_implementation"],
        "comparison_only_inputs": ["printed_paper_matrices", "printed_table_s1"],
        "forbidden_scientific_inputs": [],
    }
    if summary["status"] != "passed":
        raise AssertionError(f"final scientific bundle failed: {summary}")
    return summary


def _panel_a(
    output_root: Path,
    solution: Any,
    converged: Any,
    parameters: dict[str, Any],
    acceptance: dict[str, Any],
) -> bool:
    stem = TARGET_STEMS["T-FIG001A"]
    y_m = solution.observables.y_m
    normalized = solution.observables.R0 / np.max(solution.observables.R0)
    converged_norm = converged.observables.R0 / np.max(converged.observables.R0)
    interpolated = np.interp(y_m, converged.observables.y_m, converged_norm)
    convergence_max_abs = float(np.max(np.abs(normalized - interpolated)))
    minimum = float(np.min(normalized))
    peak = float(np.max(normalized))
    convergence_limit = float(acceptance["baseline_convergence_max_abs"])
    _write_csv(
        output_root / "data" / f"{stem}.csv",
        ["y_m", "y_mm", "R0", "R0_normalized"],
        zip(y_m, y_m * 1e3, solution.observables.R0, normalized, strict=True),
    )
    assertions = [
        _assertion(
            "ASSERT-FIG001A-NONNEGATIVE",
            "analytic",
            minimum >= -1e-12,
            "The baseline intensity is nonnegative over the paper source range.",
            _check_ref(stem),
        ),
        _assertion(
            "ASSERT-FIG001A-UNIT-PEAK",
            "numeric",
            abs(peak - 1.0) <= 1e-12,
            "The displayed baseline is normalized to unit peak.",
            _data_ref(stem),
        ),
        _assertion(
            "ASSERT-FIG001A-CONVERGED",
            "numeric",
            convergence_max_abs < convergence_limit,
            "The baseline curve is stable under denser y and slit quadrature.",
            _check_ref(stem),
        ),
    ]
    return _write_check(
        output_root,
        "T-FIG001A",
        parameters=parameters,
        metrics={
            "minimum_normalized_response": minimum,
            "peak_normalized_response": peak,
            "convergence_max_abs": convergence_max_abs,
            "zero_crossings": 0,
        },
        assertions=assertions,
    )


def _panel_b(
    output_root: Path,
    solution: Any,
    converged: Any,
    parameters: dict[str, Any],
    quadrature_order: int,
    acceptance: dict[str, Any],
) -> bool:
    stem = TARGET_STEMS["T-FIG001B"]
    obs = solution.observables
    normalized_t = obs.g_t / np.max(np.abs(obs.g_t))
    normalized_f = obs.g_f / np.max(np.abs(obs.g_f))
    converged_t = converged.observables.g_t / np.max(np.abs(converged.observables.g_t))
    converged_f = converged.observables.g_f / np.max(np.abs(converged.observables.g_f))
    convergence_max_abs = float(
        max(
            np.max(
                np.abs(
                    normalized_t
                    - np.interp(obs.y_m, converged.observables.y_m, converged_t)
                )
            ),
            np.max(
                np.abs(
                    normalized_f
                    - np.interp(obs.y_m, converged.observables.y_m, converged_f)
                )
            ),
        )
    )
    epsilon = float(acceptance["finite_difference_epsilon"])
    field_t_plus = fresnel_field(
        solution.geometry, obs.y_m, quadrature_order, theta_t=epsilon
    )
    field_t_minus = fresnel_field(
        solution.geometry, obs.y_m, quadrature_order, theta_t=-epsilon
    )
    field_f_plus = fresnel_field(
        solution.geometry, obs.y_m, quadrature_order, theta_f=epsilon
    )
    field_f_minus = fresnel_field(
        solution.geometry, obs.y_m, quadrature_order, theta_f=-epsilon
    )
    finite_t = (np.abs(field_t_plus) ** 2 - np.abs(field_t_minus) ** 2) / (2 * epsilon)
    finite_f = (np.abs(field_f_plus) ** 2 - np.abs(field_f_minus) ** 2) / (2 * epsilon)
    derivative_relative_l2 = float(
        max(
            np.linalg.norm(finite_t - obs.g_t) / np.linalg.norm(obs.g_t),
            np.linalg.norm(finite_f - obs.g_f) / np.linalg.norm(obs.g_f),
        )
    )
    _write_csv(
        output_root / "data" / f"{stem}.csv",
        ["y_m", "y_mm", "g_t", "g_f", "g_t_normalized", "g_f_normalized"],
        zip(
            obs.y_m,
            obs.y_m * 1e3,
            obs.g_t,
            obs.g_f,
            normalized_t,
            normalized_f,
            strict=True,
        ),
    )
    derivative_limit = float(acceptance["derivative_relative_l2_max"])
    convergence_limit = float(acceptance["score_convergence_max_abs"])
    assertions = [
        _assertion(
            "ASSERT-FIG001B-DERIVATIVE",
            "analytic",
            derivative_relative_l2 < derivative_limit,
            "Analytic response moments agree with independent central finite differences of intensity.",
            _check_ref(stem),
        ),
        _assertion(
            "ASSERT-FIG001B-CONVERGED",
            "numeric",
            convergence_max_abs < convergence_limit,
            "Both separately normalized score curves are quadrature-converged.",
            _check_ref(stem),
        ),
    ]
    return _write_check(
        output_root,
        "T-FIG001B",
        parameters=parameters,
        metrics={
            "central_difference_epsilon": epsilon,
            "derivative_relative_l2_max": derivative_relative_l2,
            "convergence_max_abs": convergence_max_abs,
            "tilt_zero_crossings": _zero_crossings(normalized_t),
            "defocus_zero_crossings": _zero_crossings(normalized_f),
        },
        assertions=assertions,
    )


def _panel_c(
    output_root: Path,
    solution: Any,
    converged: Any,
    parameters: dict[str, Any],
    acceptance: dict[str, Any],
) -> bool:
    stem = TARGET_STEMS["T-FIG001C"]
    obs = solution.observables
    codes = np.vstack((solution.optimized_codes, solution.toy_codes))
    converged_codes = np.vstack((converged.optimized_codes, converged.toy_codes))
    names = ("w_t", "w_f", "h_1", "h_2")
    interpolation_errors = []
    for index, code in enumerate(codes):
        interpolated = np.interp(
            obs.y_m, converged.observables.y_m, converged_codes[index]
        )
        interpolation_errors.append(
            float(np.max(np.abs(code - interpolated)) / max(np.max(np.abs(code)), 1.0))
        )
    convergence_relative_max = max(interpolation_errors)
    constant = np.ones_like(obs.y_m)
    zero_means = [
        noise_inner(code, constant, solution.noise_weight, obs.y_m) for code in codes
    ]
    norms = [
        noise_inner(code, code, solution.noise_weight, obs.y_m) for code in codes
    ]
    pairs = {
        "optimized": noise_inner(
            codes[0], codes[1], solution.noise_weight, obs.y_m
        ),
        "toy": noise_inner(codes[2], codes[3], solution.noise_weight, obs.y_m),
    }
    orthogonality_residual = float(
        max(
            max(abs(value) for value in zero_means),
            max(abs(value - 1.0) for value in norms),
            max(abs(value) for value in pairs.values()),
        )
    )
    optimized_crossings = [_zero_crossings(code) for code in solution.optimized_codes]
    toy_crossings = [_zero_crossings(code) for code in solution.toy_codes]
    fringe_lock = min(optimized_crossings) > max(toy_crossings)
    _write_csv(
        output_root / "data" / f"{stem}.csv",
        ["y_m", "y_mm", *names],
        zip(obs.y_m, obs.y_m * 1e3, *codes, strict=True),
    )
    orthogonality_limit = float(acceptance["orthogonality_residual_max"])
    convergence_limit = float(acceptance["code_convergence_relative_max"])
    assertions = [
        _assertion(
            "ASSERT-FIG001C-ORTHONORMAL",
            "analytic",
            orthogonality_residual < orthogonality_limit,
            "Optimized and toy pairs separately satisfy the declared nuisance-orthonormal construction.",
            _check_ref(stem),
        ),
        _assertion(
            "ASSERT-FIG001C-FRINGE-LOCKED",
            "numeric",
            fringe_lock,
            "Each optimized code has more zero crossings than either smooth toy code on the paper range.",
            _data_ref(stem),
        ),
        _assertion(
            "ASSERT-FIG001C-CONVERGED",
            "numeric",
            convergence_relative_max < convergence_limit,
            "All four physical/toy code curves are stable under denser quadrature.",
            _check_ref(stem),
        ),
    ]
    return _write_check(
        output_root,
        "T-FIG001C",
        parameters=parameters,
        metrics={
            "noise_metric_zero_means": dict(zip(names, zero_means, strict=True)),
            "noise_metric_norms": dict(zip(names, norms, strict=True)),
            "noise_metric_pair_inner_products": pairs,
            "orthogonality_residual_max": orthogonality_residual,
            "convergence_relative_max": convergence_relative_max,
            "optimized_zero_crossings": optimized_crossings,
            "toy_zero_crossings": toy_crossings,
            "fringe_lock_check": fringe_lock,
        },
        assertions=assertions,
    )


def _panel_d(
    output_root: Path,
    solution: Any,
    converged: Any,
    parameters: dict[str, Any],
    references: dict[str, Any],
    acceptance: dict[str, Any],
) -> bool:
    stem = TARGET_STEMS["T-FIG001D"]
    paper_full = np.asarray(references["full_fisher"], dtype=np.float64)
    paper_optimized = np.asarray(references["optimized_fisher"], dtype=np.float64)
    paper_opt_retention = np.asarray(
        references["optimized_retention"], dtype=np.float64
    )
    paper_toy_retention = np.asarray(references["toy_retention"], dtype=np.float64)
    full_relative = _relative_frobenius(solution.full_fisher, paper_full)
    optimized_relative = _relative_frobenius(
        solution.optimized_fisher, paper_optimized
    )
    opt_retention_error = float(
        np.max(np.abs(solution.optimized_retention - paper_opt_retention))
    )
    toy_retention_error = float(
        np.max(np.abs(solution.toy_retention - paper_toy_retention))
    )
    convergence_max_abs = float(
        max(
            np.max(np.abs(solution.optimized_retention - converged.optimized_retention)),
            np.max(np.abs(solution.toy_retention - converged.toy_retention)),
        )
    )
    bounds_pass = bool(
        np.all(solution.optimized_retention >= -1e-10)
        and np.all(solution.optimized_retention <= 1.0 + 1e-9)
        and np.all(solution.toy_retention >= -1e-10)
        and np.all(solution.toy_retention <= 1.0 + 1e-9)
    )
    _write_csv(
        output_root / "data" / f"{stem}.csv",
        ["code_family", "principal_mode", "generated_retention", "paper_text_reference"],
        [
            ("toy", 1, float(solution.toy_retention[0]), float(paper_toy_retention[0])),
            (
                "optimized",
                1,
                float(solution.optimized_retention[0]),
                float(paper_opt_retention[0]),
            ),
            ("toy", 2, float(solution.toy_retention[1]), float(paper_toy_retention[1])),
            (
                "optimized",
                2,
                float(solution.optimized_retention[1]),
                float(paper_opt_retention[1]),
            ),
        ],
    )
    fisher_limit = float(acceptance["fisher_relative_frobenius_max"])
    retention_limit = float(acceptance["retention_max_abs"])
    convergence_limit = float(acceptance["retention_convergence_max_abs"])
    assertions = [
        _assertion(
            "ASSERT-FIG001D-PAPER-MATRICES",
            "numeric",
            full_relative < fisher_limit and optimized_relative < fisher_limit,
            "Independently generated full and optimized Fisher matrices agree with the paper text.",
            _check_ref(stem),
        ),
        _assertion(
            "ASSERT-FIG001D-RETENTION",
            "numeric",
            opt_retention_error < retention_limit and toy_retention_error < retention_limit,
            "All four optimized/toy principal retention values agree with the paper text.",
            _data_ref(stem),
        ),
        _assertion(
            "ASSERT-FIG001D-BOUNDS",
            "analytic",
            bounds_pass,
            "Every independently computed projection-retention eigenvalue lies in [0,1] within roundoff.",
            _check_ref(stem),
        ),
        _assertion(
            "ASSERT-FIG001D-CONVERGED",
            "numeric",
            convergence_max_abs < convergence_limit,
            "Retention values are stable under denser quadrature.",
            _check_ref(stem),
        ),
    ]
    return _write_check(
        output_root,
        "T-FIG001D",
        parameters=parameters,
        metrics={
            "generated_full_fisher": solution.full_fisher.tolist(),
            "paper_full_fisher": paper_full.tolist(),
            "full_fisher_relative_frobenius": full_relative,
            "generated_optimized_fisher": solution.optimized_fisher.tolist(),
            "paper_optimized_fisher": paper_optimized.tolist(),
            "optimized_fisher_relative_frobenius": optimized_relative,
            "generated_optimized_retention": solution.optimized_retention.tolist(),
            "paper_optimized_retention": paper_opt_retention.tolist(),
            "optimized_retention_max_abs": opt_retention_error,
            "generated_toy_retention": solution.toy_retention.tolist(),
            "paper_toy_retention": paper_toy_retention.tolist(),
            "toy_retention_max_abs": toy_retention_error,
            "convergence_max_abs": convergence_max_abs,
            "retention_bounds_pass": bounds_pass,
        },
        assertions=assertions,
    )


def _supplement_scan(
    output_root: Path,
    geometry: Geometry,
    scan: dict[str, Any],
    references: dict[str, Any],
    acceptance: dict[str, Any],
    parameters: dict[str, Any],
) -> bool:
    stem = TARGET_STEMS["T-FIGS001"]
    widths_m = np.asarray(scan["slit_widths_m"], dtype=np.float64)
    y_points = int(scan["y_points"])
    quadrature_order = int(scan["quadrature_order"])
    convergence_y_points = int(scan["convergence_y_points"])
    convergence_quadrature_order = int(scan["convergence_quadrature_order"])
    generated, fisher_tt, fisher_ff = width_scan(
        widths_m,
        base_geometry=geometry,
        y_points=y_points,
        quadrature_order=quadrature_order,
    )
    converged, _, _ = width_scan(
        widths_m,
        base_geometry=geometry,
        y_points=convergence_y_points,
        quadrature_order=convergence_quadrature_order,
    )
    paper_table = np.asarray(references["table_s1_rho"], dtype=np.float64)
    absolute_errors = np.abs(generated - paper_table)
    relative_errors = absolute_errors / paper_table
    tolerance_abs = float(acceptance["table_tolerance_absolute"])
    tolerance_rel = float(acceptance["table_tolerance_relative"])
    tolerances = tolerance_abs + tolerance_rel * np.abs(paper_table)
    rows_within_tolerance = absolute_errors <= tolerances
    convergence_relative = np.abs(generated - converged) / np.maximum(
        np.abs(converged), 1e-30
    )
    monotonic = bool(np.all(np.diff(generated) > 0.0))
    narrow_limit = float(acceptance["narrow_slit_ratio_max"])
    narrow_suppression = bool(generated[0] < narrow_limit)
    convergence_limit = float(acceptance["width_convergence_relative_max"])
    _write_csv(
        output_root / "data" / f"{stem}.csv",
        [
            "slit_width_m",
            "slit_width_um",
            "F_tt",
            "F_ff",
            "rho_generated",
            "rho_table_s1_reference",
            "relative_error",
        ],
        zip(
            widths_m,
            widths_m * 1e6,
            fisher_tt,
            fisher_ff,
            generated,
            paper_table,
            relative_errors,
            strict=True,
        ),
    )
    assertions = [
        _assertion(
            "ASSERT-FIGS001-NARROW",
            "analytic",
            narrow_suppression,
            "The 20 micrometre slit has a defocus-to-tilt ratio below 2e-5, consistent with the point-slit limit.",
            _check_ref(stem),
        ),
        _assertion(
            "ASSERT-FIGS001-MONOTONIC",
            "numeric",
            monotonic,
            "The independently generated ratio increases strictly over all five paper widths.",
            _data_ref(stem),
        ),
        _assertion(
            "ASSERT-FIGS001-TABLE",
            "numeric",
            bool(np.all(rows_within_tolerance)),
            "All five independent ratios satisfy the declared printed-table tolerance.",
            _data_ref(stem),
        ),
        _assertion(
            "ASSERT-FIGS001-CONVERGED",
            "numeric",
            float(np.max(convergence_relative)) < convergence_limit,
            "Every width-scan ratio is stable under denser quadrature.",
            _check_ref(stem),
        ),
    ]
    scan_parameters = {
        **parameters,
        "width_scan": scan,
    }
    return _write_check(
        output_root,
        "T-FIGS001",
        parameters=scan_parameters,
        metrics={
            "widths_um": (widths_m * 1e6).tolist(),
            "generated_rho": generated.tolist(),
            "table_s1_rho": paper_table.tolist(),
            "relative_table_errors": relative_errors.tolist(),
            "absolute_table_errors": absolute_errors.tolist(),
            "table_tolerances": tolerances.tolist(),
            "table_rows_within_tolerance": rows_within_tolerance.tolist(),
            "table_relative_error_max": float(np.max(relative_errors)),
            "convergence_relative_errors": convergence_relative.tolist(),
            "convergence_relative_max": float(np.max(convergence_relative)),
            "strictly_monotonic": monotonic,
            "narrow_slit_suppression": narrow_suppression,
        },
        assertions=assertions,
    )
