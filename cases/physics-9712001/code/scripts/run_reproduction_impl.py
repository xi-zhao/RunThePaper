#!/usr/bin/env python3
"""Generate every numerical target from independent scientific numerics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pt_spectrum.model import (  # noqa: E402
    ground_state_shooting,
    low_spectrum,
    massive_n1_energy,
    near_one_asymptotic_energy,
    wkb_energy,
)


def json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"unsupported JSON value: {type(value)!r}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n",
        encoding="utf-8",
    )


def write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def declared_grid(config: dict[str, Any]) -> np.ndarray:
    values: list[float] = []
    values.extend(float(item) for item in config.get("explicit_exponents", []))
    values.extend(float(item) for item in config.get("anchor_exponents", []))
    for start, stop, count in config.get("linear_segments", []):
        values.extend(np.linspace(float(start), float(stop), int(count)).tolist())
    if "linear_segment" in config:
        start, stop, count = config["linear_segment"]
        values.extend(np.linspace(float(start), float(stop), int(count)).tolist())
    values.extend(1.0 + float(item) for item in config.get("near_one_epsilons", []))
    if not values:
        raise ValueError("spectrum grid is empty")
    return np.array(sorted(set(round(value, 12) for value in values)), dtype=float)


def spectrum_rows(
    exponent: float,
    values: np.ndarray,
    *,
    real_tolerance: float,
    solver: str,
    energy_min: float = -np.inf,
    energy_max: float = np.inf,
    mass_squared: float = 0.0,
) -> list[dict[str, Any]]:
    rows = []
    for rank, value in enumerate(values):
        rows.append(
            {
                "N": float(exponent),
                "mass_squared": float(mass_squared),
                "mode_rank": rank,
                "energy_real": float(value.real),
                "energy_imag": float(value.imag),
                "is_real": bool(abs(value.imag) <= real_tolerance),
                "visible_in_paper_window": bool(energy_min <= value.real <= energy_max),
                "solver": solver,
            }
        )
    return rows


def run_fig1(parameters: dict[str, Any], real_tolerance: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for exponent in declared_grid(parameters):
        if exponent <= parameters["shooting_cutoff"]:
            result = ground_state_shooting(
                exponent,
                boundary=parameters["shooting_boundary"],
                relative_tolerance=parameters["shooting_rtol"],
                absolute_tolerance=parameters["shooting_atol"],
                max_step=parameters["shooting_max_step"],
            )
            values = np.array([complex(result.energy)], dtype=np.complex128)
            solver = "riccati_shooting"
        else:
            contour = exponent > 2.0
            discretization = (
                parameters["complex_contour"] if contour else parameters["real_axis"]
            )
            values = low_spectrum(
                exponent,
                half_width=discretization["half_width"],
                points=discretization["points"],
                bend_scale=discretization.get("bend_scale", 2.0),
                eigenvalues=parameters["eigenvalues"],
                shift=parameters["shift"],
                tolerance=parameters["eigensolver_tolerance"],
                use_complex_contour=contour,
            )
            solver = "complex_contour_fd" if contour else "real_axis_fd"
        rows.extend(
            spectrum_rows(
                exponent,
                values,
                real_tolerance=real_tolerance,
                solver=solver,
                energy_min=0.0,
                energy_max=parameters["energy_max"],
            )
        )
    return rows


def run_table_i(parameters: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
    rows: list[dict[str, Any]] = []
    resolution_difference = 0.0
    for exponent in parameters["exponents"]:
        count = parameters["levels_by_exponent"][str(float(exponent))]
        common = dict(
            half_width=parameters["half_width"],
            bend_scale=parameters["bend_scale"],
            eigenvalues=parameters["eigenvalues"],
            shift=parameters["shift"],
            use_complex_contour=True,
        )
        fine = low_spectrum(exponent, points=parameters["points"], **common)
        coarse = low_spectrum(exponent, points=parameters["coarse_points"], **common)
        resolution_difference = max(
            resolution_difference,
            float(np.max(np.abs(fine[:count].real - coarse[:count].real))),
        )
        for level in range(count):
            rows.append(
                {
                    "N": float(exponent),
                    "n": level,
                    "exact_fd": float(fine[level].real),
                    "exact_imag": float(fine[level].imag),
                    "coarse_fd": float(coarse[level].real),
                    "wkb": wkb_energy(exponent, level),
                }
            )
    return rows, resolution_difference


def nearest_value(values: np.ndarray, target: float) -> complex:
    return complex(min(values, key=lambda value: abs(value - target)))


def run_table_ii(parameters: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for epsilon in parameters["epsilons"]:
        exponent = 1.0 + float(epsilon)
        primary = ground_state_shooting(
            exponent,
            boundary=parameters["boundary"],
            relative_tolerance=parameters["relative_tolerance"],
            absolute_tolerance=parameters["absolute_tolerance"],
            max_step=parameters["max_step"],
        )
        secondary = ground_state_shooting(
            exponent,
            boundary=parameters["secondary_boundary"],
            relative_tolerance=parameters["relative_tolerance"],
            absolute_tolerance=parameters["absolute_tolerance"],
            max_step=parameters["max_step"],
        )
        finite_difference = low_spectrum(
            exponent,
            half_width=parameters["fd_half_width"],
            points=parameters["fd_points"],
            eigenvalues=parameters["fd_eigenvalues"],
            shift=primary.energy,
            tolerance=max(parameters["relative_tolerance"], 1e-11),
            use_complex_contour=False,
        )
        fd_value = nearest_value(finite_difference, primary.energy)
        rows.append(
            {
                "epsilon": float(epsilon),
                "N": exponent,
                "exact_shooting": primary.energy,
                "patch_residual": primary.residual,
                "secondary_boundary_energy": secondary.energy,
                "finite_difference_energy": fd_value.real,
                "finite_difference_imag": fd_value.imag,
                "asymptotic_eq11": near_one_asymptotic_energy(float(epsilon)),
            }
        )
    return rows


def run_fig3(parameters: dict[str, Any], real_tolerance: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grid = declared_grid(parameters)
    for mass_squared in parameters["mass_squared_values"]:
        for exponent in grid:
            values = low_spectrum(
                exponent,
                mass_squared=mass_squared,
                half_width=parameters["half_width"],
                points=parameters["points"],
                eigenvalues=parameters["eigenvalues"],
                shift=parameters["shift"],
                tolerance=parameters["eigensolver_tolerance"],
                use_complex_contour=False,
            )
            rows.extend(
                spectrum_rows(
                    exponent,
                    values,
                    real_tolerance=real_tolerance,
                    solver="real_axis_fd",
                    energy_min=parameters["energy_min"],
                    energy_max=parameters["energy_max"],
                    mass_squared=mass_squared,
                )
            )
    return rows


def check_record(
    check_id: str,
    value: float,
    threshold: float,
    *,
    comparison: str = "max_abs",
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "passed" if value <= threshold else "failed",
        "value": float(value),
        "threshold": float(threshold),
        "comparison": comparison,
    }


def build_science_checks(
    config: dict[str, Any],
    fig1_rows: list[dict[str, Any]],
    table_i_rows: list[dict[str, Any]],
    table_i_resolution_difference: float,
    table_ii_rows: list[dict[str, Any]],
    fig3_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    references = config["printed_references_for_validation_only"]
    tolerance = config["acceptance"]

    exact_i_errors = []
    wkb_i_errors = []
    for row in table_i_rows:
        reference = references["table_i"][str(row["N"])]
        exact_i_errors.append(abs(row["exact_fd"] - reference["exact"][row["n"]]))
        wkb_i_errors.append(abs(row["wkb"] - reference["wkb"][row["n"]]))

    table_ii_exact_errors = [
        abs(row["exact_shooting"] - references["table_ii"]["exact"][index])
        for index, row in enumerate(table_ii_rows)
    ]
    table_ii_asymptotic_errors = [
        abs(row["asymptotic_eq11"] - references["table_ii"]["asymptotic"][index])
        for index, row in enumerate(table_ii_rows)
    ]
    solver_differences = [
        abs(row["exact_shooting"] - row["finite_difference_energy"])
        for row in table_ii_rows
    ]
    domain_differences = [
        abs(row["exact_shooting"] - row["secondary_boundary_energy"])
        for row in table_ii_rows
    ]

    n2_rows = [
        row for row in fig1_rows if abs(row["N"] - 2.0) < 1e-12 and row["mode_rank"] < 6
    ]
    n2_error = max(
        abs(row["energy_real"] - (2 * row["mode_rank"] + 1)) for row in n2_rows
    )

    massive_errors = []
    for row in fig3_rows:
        if abs(row["N"] - 1.0) < 1e-12 and row["mode_rank"] < 5:
            expected = massive_n1_energy(row["mass_squared"], row["mode_rank"])
            massive_errors.append(abs(row["energy_real"] - expected))

    discrepancy_rows = []
    for index, row in enumerate(table_ii_rows):
        difference = row["exact_shooting"] - references["table_ii"]["exact"][index]
        if abs(difference) > tolerance["table_ii_first_four_max_abs_error"]:
            discrepancy_rows.append(
                {
                    "epsilon": row["epsilon"],
                    "paper_exact": references["table_ii"]["exact"][index],
                    "independent_shooting": row["exact_shooting"],
                    "independent_finite_difference": row["finite_difference_energy"],
                    "difference": difference,
                    "classification": "inconclusive_pending_fresh_review",
                }
            )

    checks = [
        check_record(
            "table_i_exact_values",
            max(exact_i_errors, default=0.0),
            tolerance["table_i_exact_max_abs_error"],
        ),
        check_record(
            "table_i_wkb_formula",
            max(wkb_i_errors, default=0.0),
            tolerance["printed_four_digit_formula_tolerance"],
        ),
        check_record(
            "table_i_resolution_convergence",
            table_i_resolution_difference,
            tolerance["table_i_resolution_max_abs_difference"],
        ),
        check_record(
            "table_ii_first_four_exact_values",
            max(table_ii_exact_errors[:4], default=0.0),
            tolerance["table_ii_first_four_max_abs_error"],
        ),
        check_record(
            "table_ii_asymptotic_formula",
            max(table_ii_asymptotic_errors, default=0.0),
            tolerance["printed_four_digit_formula_tolerance"],
        ),
        check_record(
            "table_ii_independent_solver_agreement",
            max(solver_differences, default=0.0),
            tolerance["table_ii_independent_solver_max_abs_difference"],
        ),
        check_record(
            "table_ii_domain_convergence",
            max(domain_differences, default=0.0),
            tolerance["table_ii_domain_max_abs_difference"],
        ),
        check_record(
            "massless_n2_harmonic_spectrum",
            n2_error,
            tolerance["harmonic_n2_max_abs_error"],
        ),
        check_record(
            "massive_n1_shifted_oscillator",
            max(massive_errors, default=np.inf),
            tolerance["massive_n1_max_abs_error"],
        ),
    ]
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": (
            "passed" if all(item["status"] == "passed" for item in checks) else "failed"
        ),
        "checks": checks,
        "table_ii_paper_discrepancies": discrepancy_rows,
        "paper_error_candidate_emitted": False,
        "paper_assessment": (
            "inconclusive_pending_fresh_review"
            if discrepancy_rows
            else "paper_supported_pending_fresh_review"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    arguments = parser.parse_args()
    started = time.perf_counter()
    config_path = Path(arguments.config).resolve()
    output_root = Path(arguments.output_root).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "physics-9712001":
        raise ValueError("config paper_id mismatch")

    parameters = config["parameters"]
    real_tolerance = float(parameters["real_imag_tolerance"])
    fig1_rows = run_fig1(parameters["fig1"], real_tolerance)
    table_i_rows, table_i_resolution_difference = run_table_i(parameters["table_i"])
    table_ii_rows = run_table_ii(parameters["table_ii"])
    fig3_rows = run_fig3(parameters["fig3"], real_tolerance)

    data_dir = output_root / "data"
    checks_dir = output_root / "checks"
    spectrum_fields = [
        "N",
        "mass_squared",
        "mode_rank",
        "energy_real",
        "energy_imag",
        "is_real",
        "visible_in_paper_window",
        "solver",
    ]
    write_csv(data_dir / "fig1_massless_spectrum.csv", spectrum_fields, fig1_rows)
    write_csv(
        data_dir / "table_i_exact_wkb.csv",
        ["N", "n", "exact_fd", "exact_imag", "coarse_fd", "wkb"],
        table_i_rows,
    )
    write_csv(
        data_dir / "table_ii_near_one.csv",
        [
            "epsilon",
            "N",
            "exact_shooting",
            "patch_residual",
            "secondary_boundary_energy",
            "finite_difference_energy",
            "finite_difference_imag",
            "asymptotic_eq11",
        ],
        table_ii_rows,
    )
    write_csv(data_dir / "fig3_massive_spectrum.csv", spectrum_fields, fig3_rows)

    science = build_science_checks(
        config,
        fig1_rows,
        table_i_rows,
        table_i_resolution_difference,
        table_ii_rows,
        fig3_rows,
    )
    write_json(checks_dir / "science_checks.json", science)

    data_paths = sorted(data_dir.glob("*.csv"))
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "config_path": str(config_path),
        "config_sha256": sha256(config_path),
        "generated_data": [
            {
                "path": str(path.relative_to(output_root)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in data_paths
        ],
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
    }
    write_json(checks_dir / "generated_data_manifest.json", manifest)
    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "status": science["status"],
        "elapsed_seconds": time.perf_counter() - started,
        "fig1_rows": len(fig1_rows),
        "fig3_rows": len(fig3_rows),
        "table_i_rows": len(table_i_rows),
        "table_ii_rows": len(table_ii_rows),
        "paper_error_candidate_emitted": False,
        "paper_assessment": science["paper_assessment"],
    }
    write_json(checks_dir / "run_summary.json", summary)
    print(json.dumps(summary, sort_keys=True, default=json_default))


if __name__ == "__main__":
    main()
