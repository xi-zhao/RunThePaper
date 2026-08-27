"""Isolated implementation smoke for every TRY/Fresnel numerical target.

Only the frozen configuration and the independently derived Fresnel model are
read. Paper images, raw sources, author arrays, and author source code are not
accepted as inputs.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .try_fresnel import Geometry, noise_inner, solve_main, width_scan


TARGET_STEMS = {
    "T-FIG001A": "fig001a_baseline",
    "T-FIG001B": "fig001b_scores",
    "T-FIG001C": "fig001c_codes",
    "T-FIG001D": "fig001d_retention",
    "T-FIGS001": "figs001_width_scan",
}


def _write_csv(path: Path, header: list[str], rows: Iterable[Iterable[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _write_check(
    output_root: Path,
    target_id: str,
    *,
    parameters: dict[str, Any],
    assertions: dict[str, bool],
    metrics: dict[str, Any],
) -> None:
    stem = TARGET_STEMS[target_id]
    path = output_root / "checks" / "implementation_validation" / f"{stem}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "passed" if all(assertions.values()) else "failed"
    payload = {
        "schema_version": 1,
        "paper_id": "2605.02873",
        "target_id": target_id,
        "status": status,
        "artifact_stage": "exploratory",
        "parameter_match": "reduced_scale",
        "generated_data_provenance": "independent_numerics",
        "parameters": parameters,
        "assertions": assertions,
        "metrics": metrics,
        "forbidden_scientific_inputs": [],
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if status != "passed":
        raise AssertionError(f"implementation smoke failed for {target_id}: {payload}")


def _gram_error(codes: np.ndarray, solution: Any) -> float:
    gram = np.asarray(
        [
            [
                noise_inner(
                    codes[row],
                    codes[column],
                    solution.noise_weight,
                    solution.observables.y_m,
                )
                for column in range(2)
            ]
            for row in range(2)
        ]
    )
    return float(np.max(np.abs(gram - np.eye(2))))


def run_bundle(config_path: Path, output_root: Path) -> dict[str, Any]:
    """Run all five target implementations using one shared reduced-scale solve."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "2605.02873":
        raise ValueError("configuration paper_id must be 2605.02873")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("configuration must contain a parameters object")
    geometry_params = parameters.get("geometry")
    main_params = parameters.get("main_numerics")
    width_params = parameters.get("width_scan")
    if not all(isinstance(item, dict) for item in (geometry_params, main_params, width_params)):
        raise ValueError("geometry, main_numerics, and width_scan must be objects")

    geometry = Geometry(**geometry_params)
    solution = solve_main(
        geometry=geometry,
        y_points=int(main_params["y_points"]),
        quadrature_order=int(main_params["quadrature_order"]),
    )
    y_m = solution.observables.y_m

    baseline = solution.observables.R0 / float(np.max(solution.observables.R0))
    stem = TARGET_STEMS["T-FIG001A"]
    _write_csv(
        output_root / "data" / "implementation_validation" / f"{stem}.csv",
        ["y_m", "R0_normalized"],
        zip(y_m, baseline, strict=True),
    )
    _write_check(
        output_root,
        "T-FIG001A",
        parameters=parameters,
        assertions={
            "nonnegative": bool(np.min(baseline) >= -1e-12),
            "unit_peak": bool(abs(float(np.max(baseline)) - 1.0) <= 1e-12),
        },
        metrics={
            "minimum": float(np.min(baseline)),
            "maximum": float(np.max(baseline)),
        },
    )

    g_t = solution.observables.g_t / float(np.max(np.abs(solution.observables.g_t)))
    g_f = solution.observables.g_f / float(np.max(np.abs(solution.observables.g_f)))
    stem = TARGET_STEMS["T-FIG001B"]
    _write_csv(
        output_root / "data" / "implementation_validation" / f"{stem}.csv",
        ["y_m", "g_t_normalized", "g_f_normalized"],
        zip(y_m, g_t, g_f, strict=True),
    )
    _write_check(
        output_root,
        "T-FIG001B",
        parameters=parameters,
        assertions={
            "finite": bool(np.all(np.isfinite(g_t)) and np.all(np.isfinite(g_f))),
            "unit_amplitudes": bool(
                abs(float(np.max(np.abs(g_t))) - 1.0) <= 1e-12
                and abs(float(np.max(np.abs(g_f))) - 1.0) <= 1e-12
            ),
        },
        metrics={
            "tilt_peak": float(np.max(np.abs(g_t))),
            "defocus_peak": float(np.max(np.abs(g_f))),
        },
    )

    stem = TARGET_STEMS["T-FIG001C"]
    _write_csv(
        output_root / "data" / "implementation_validation" / f"{stem}.csv",
        ["y_m", "optimized_tilt", "optimized_defocus", "toy_tilt", "toy_defocus"],
        zip(
            y_m,
            solution.optimized_codes[0],
            solution.optimized_codes[1],
            solution.toy_codes[0],
            solution.toy_codes[1],
            strict=True,
        ),
    )
    optimized_gram_error = _gram_error(solution.optimized_codes, solution)
    toy_gram_error = _gram_error(solution.toy_codes, solution)
    _write_check(
        output_root,
        "T-FIG001C",
        parameters=parameters,
        assertions={
            "optimized_noise_orthonormal": optimized_gram_error < 1e-10,
            "toy_noise_orthonormal": toy_gram_error < 1e-10,
        },
        metrics={
            "optimized_gram_error": optimized_gram_error,
            "toy_gram_error": toy_gram_error,
        },
    )

    stem = TARGET_STEMS["T-FIG001D"]
    _write_csv(
        output_root / "data" / "implementation_validation" / f"{stem}.csv",
        ["mode", "optimized_retention", "toy_retention"],
        zip(
            range(2),
            solution.optimized_retention,
            solution.toy_retention,
            strict=True,
        ),
    )
    retention_values = np.concatenate((solution.optimized_retention, solution.toy_retention))
    _write_check(
        output_root,
        "T-FIG001D",
        parameters=parameters,
        assertions={
            "finite": bool(np.all(np.isfinite(retention_values))),
            "bounded": bool(
                np.min(retention_values) >= -1e-10
                and np.max(retention_values) <= 1.0 + 1e-10
            ),
        },
        metrics={
            "optimized_retention": solution.optimized_retention.tolist(),
            "toy_retention": solution.toy_retention.tolist(),
        },
    )

    widths_m = np.asarray(width_params["slit_widths_m"], dtype=np.float64)
    ratios, fisher_tt, fisher_ff = width_scan(
        widths_m,
        base_geometry=geometry,
        y_points=int(width_params["y_points"]),
        quadrature_order=int(width_params["quadrature_order"]),
    )
    stem = TARGET_STEMS["T-FIGS001"]
    _write_csv(
        output_root / "data" / "implementation_validation" / f"{stem}.csv",
        ["slit_width_m", "F_tt", "F_ff", "rho"],
        zip(widths_m, fisher_tt, fisher_ff, ratios, strict=True),
    )
    _write_check(
        output_root,
        "T-FIGS001",
        parameters=parameters,
        assertions={
            "finite_positive": bool(np.all(np.isfinite(ratios)) and np.all(ratios > 0.0)),
            "strictly_increasing": bool(np.all(np.diff(ratios) > 0.0)),
            "narrow_slit_suppression": bool(ratios[0] < 2e-5),
        },
        metrics={
            "ratios": ratios.tolist(),
            "minimum_ratio": float(np.min(ratios)),
            "maximum_ratio": float(np.max(ratios)),
        },
    )

    return {
        "schema_version": 1,
        "paper_id": "2605.02873",
        "status": "passed",
        "mode": config.get("mode"),
        "target_ids": list(TARGET_STEMS),
    }
