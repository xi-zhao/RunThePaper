"""Target-scoped final reproduction runner for arXiv:2607.15070."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np

from casimir_model import (
    DEFAULT_BESSEL_ARGUMENT_CUTOFF,
    TIGHT_BESSEL_ARGUMENT_CUTOFF,
    correction_magnitude,
    correction_small_coupling_coefficient,
    direct_proper_time_magnitude,
    energy_ratio,
    landau_magnitude,
    landau_zero_coupling,
    large_coupling_leading,
)


WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = WORKSPACE / "outputs"
MASSES = (0.0, 0.5, 1.0, 1.5)
COLORS = ("black", "#1f77b4", "#ff7f0e", "#2ca02c")
LINESTYLES = ("-", "--", "--", "--")
LINEWIDTHS = (3.0, 2.4, 2.4, 2.4)
TARGETS = ("T001", "T002")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run exactly one guarded paper-reproduction target."
    )
    parser.add_argument("--target", required=True, choices=TARGETS)
    args = parser.parse_args()
    _require_guard(args.target)

    started = time.perf_counter()
    if args.target == "T001":
        result = run_t001()
    else:
        result = run_t002()
    result["runtime_seconds"] = round(time.perf_counter() - started, 6)
    result["environment"] = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "matplotlib": matplotlib.__version__,
        "platform": platform.platform(),
    }
    runtime_path = (
        OUTPUT_ROOT / "checks" / f"{args.target}_execution_runtime.json"
    )
    _write_json(runtime_path, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


def run_t001() -> dict[str, Any]:
    alpha_landau = np.linspace(0.0, 30.0, 301)
    alpha_correction = np.linspace(0.025, 12.0, 480)
    landau_curves: dict[float, np.ndarray] = {}
    correction_curves: dict[float, np.ndarray] = {}
    rows: list[dict[str, Any]] = []

    for mass in MASSES:
        landau_values = np.array(
            [-landau_magnitude(alpha, mass) for alpha in alpha_landau]
        )
        correction_values = np.array(
            [-correction_magnitude(alpha, mass) for alpha in alpha_correction]
        )
        landau_curves[mass] = landau_values
        correction_curves[mass] = correction_values
        for alpha, value in zip(alpha_landau, landau_values, strict=True):
            rows.append(
                {
                    "target_id": "T001",
                    "panel_id": "FIG002A",
                    "alpha0": _format_float(alpha),
                    "m0": _format_float(mass),
                    "normalized_energy": _format_float(value),
                    "series_id": _series_id("FIG2A", mass),
                    "provenance": "independent_numerics",
                }
            )
        for alpha, value in zip(
            alpha_correction,
            correction_values,
            strict=True,
        ):
            rows.append(
                {
                    "target_id": "T001",
                    "panel_id": "FIG002B",
                    "alpha0": _format_float(alpha),
                    "m0": _format_float(mass),
                    "normalized_energy": _format_float(value),
                    "series_id": _series_id("FIG2B", mass),
                    "provenance": "independent_numerics",
                }
            )

    data_path = OUTPUT_ROOT / "data" / "T001_energy_contributions.csv"
    _write_csv(data_path, rows)
    checks = _t001_checks(
        alpha_landau,
        landau_curves,
        alpha_correction,
        correction_curves,
    )
    check_path = OUTPUT_ROOT / "checks" / "T001_scientific_checks.json"
    _write_json(check_path, checks)
    if checks["status"] != "passed":
        return {
            "status": "failed",
            "target_id": "T001",
            "data_path": _relative(data_path),
            "check_path": _relative(check_path),
            "figure_paths": [],
        }

    landau_figure = OUTPUT_ROOT / "figures" / "fig2_landau.png"
    correction_figure = OUTPUT_ROOT / "figures" / "fig2_correction.png"
    _plot_landau(alpha_landau, landau_curves, landau_figure)
    _plot_correction(
        alpha_correction,
        correction_curves,
        correction_figure,
    )
    return {
        "status": "passed",
        "target_id": "T001",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics",
        "data_path": _relative(data_path),
        "check_path": _relative(check_path),
        "figure_paths": [
            _relative(landau_figure),
            _relative(correction_figure),
        ],
    }


def run_t002() -> dict[str, Any]:
    alpha_ratio = np.linspace(0.025, 25.0, 500)
    curves: dict[float, np.ndarray] = {}
    rows: list[dict[str, Any]] = []
    for mass in MASSES:
        ratio_values = np.array(
            [energy_ratio(alpha, mass) for alpha in alpha_ratio]
        )
        curves[mass] = ratio_values
        for alpha, value in zip(alpha_ratio, ratio_values, strict=True):
            rows.append(
                {
                    "target_id": "T002",
                    "panel_id": "FIG003A",
                    "alpha0": _format_float(alpha),
                    "m0": _format_float(mass),
                    "energy_ratio": _format_float(value),
                    "series_id": _series_id("FIG3", mass),
                    "provenance": "independent_numerics",
                }
            )

    data_path = OUTPUT_ROOT / "data" / "T002_energy_ratio.csv"
    _write_csv(data_path, rows)
    checks = _t002_checks(alpha_ratio, curves)
    check_path = OUTPUT_ROOT / "checks" / "T002_scientific_checks.json"
    _write_json(check_path, checks)
    if checks["status"] != "passed":
        return {
            "status": "failed",
            "target_id": "T002",
            "data_path": _relative(data_path),
            "check_path": _relative(check_path),
            "figure_paths": [],
        }

    ratio_figure = OUTPUT_ROOT / "figures" / "fig3_ratio.png"
    _plot_ratio(alpha_ratio, curves, ratio_figure)
    return {
        "status": "passed",
        "target_id": "T002",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics",
        "data_path": _relative(data_path),
        "check_path": _relative(check_path),
        "figure_paths": [
            _relative(ratio_figure),
        ],
    }


def _t001_checks(
    alpha_landau: np.ndarray,
    landau_curves: dict[float, np.ndarray],
    alpha_correction: np.ndarray,
    correction_curves: dict[float, np.ndarray],
) -> dict[str, Any]:
    analytic_errors = {
        _mass_key(mass): _relative_error(
            -landau_curves[mass][0],
            landau_zero_coupling(mass),
        )
        for mass in MASSES
    }
    convergence_points: list[dict[str, float]] = []
    for alpha, mass in ((0.5, 0.0), (2.0, 0.5), (10.0, 1.5)):
        for sector, evaluator in (
            ("landau", landau_magnitude),
            ("correction", correction_magnitude),
        ):
            standard = evaluator(
                alpha,
                mass,
                argument_cutoff=DEFAULT_BESSEL_ARGUMENT_CUTOFF,
            )
            tight = evaluator(
                alpha,
                mass,
                argument_cutoff=TIGHT_BESSEL_ARGUMENT_CUTOFF,
            )
            convergence_points.append(
                {
                    "alpha0": alpha,
                    "m0": mass,
                    "sector": sector,
                    "standard": standard,
                    "tight": tight,
                    "relative_error": _relative_error(standard, tight),
                }
            )

    direct_points: list[dict[str, float]] = []
    for alpha, mass, sector, evaluator in (
        (1.0, 0.5, "landau", landau_magnitude),
        (1.0, 0.5, "correction", correction_magnitude),
        (6.0, 1.0, "landau", landau_magnitude),
        (6.0, 1.0, "correction", correction_magnitude),
    ):
        series = evaluator(
            alpha,
            mass,
            argument_cutoff=TIGHT_BESSEL_ARGUMENT_CUTOFF,
        )
        direct = direct_proper_time_magnitude(
            alpha,
            mass,
            sector=sector,
        )
        direct_points.append(
            {
                "alpha0": alpha,
                "m0": mass,
                "sector": sector,
                "series": series,
                "direct_quadrature": direct.value,
                "quadrature_estimated_error": direct.estimated_error,
                "relative_error": _relative_error(series, direct.value),
            }
        )

    small_alpha_checks: list[dict[str, float]] = []
    small_alpha = 0.025
    for mass in MASSES:
        value = correction_magnitude(
            small_alpha,
            mass,
            argument_cutoff=TIGHT_BESSEL_ARGUMENT_CUTOFF,
        )
        coefficient = correction_small_coupling_coefficient(mass)
        small_alpha_checks.append(
            {
                "alpha0": small_alpha,
                "m0": mass,
                "alpha_times_correction": small_alpha * value,
                "analytic_coefficient": coefficient,
                "relative_error": _relative_error(
                    small_alpha * value,
                    coefficient,
                ),
            }
        )

    monotone_landau = all(
        bool(np.all(np.diff(values) >= -2.0e-12))
        for values in landau_curves.values()
    )
    monotone_correction = all(
        bool(np.all(np.diff(values) >= -2.0e-12))
        for values in correction_curves.values()
    )
    mass_order_landau = _mass_order_pass(landau_curves)
    mass_order_correction = _mass_order_pass(correction_curves)
    large_alpha_check = {
        "landau_exact": landau_magnitude(30.0, 0.0),
        "landau_leading": large_coupling_leading(30.0, 0.0, 1),
        "correction_exact": correction_magnitude(30.0, 0.0),
        "correction_leading": large_coupling_leading(30.0, 0.0, 2),
    }
    large_alpha_check["landau_relative_error"] = _relative_error(
        large_alpha_check["landau_exact"],
        large_alpha_check["landau_leading"],
    )
    large_alpha_check["correction_relative_error"] = _relative_error(
        large_alpha_check["correction_exact"],
        large_alpha_check["correction_leading"],
    )

    thresholds = {
        "analytic_zero_coupling_max_relative_error": 1.0e-13,
        "tail_convergence_max_relative_error": 2.0e-12,
        "direct_quadrature_max_relative_error": 2.0e-7,
        "small_alpha_scaled_max_relative_error": 0.12,
        "large_alpha_leading_max_relative_error": 0.12,
    }
    assertions = [
        _assertion(
            "T001_ZERO_COUPLING",
            max(analytic_errors.values())
            <= thresholds["analytic_zero_coupling_max_relative_error"],
            "The Landau panel exactly recovers the standard massive-plate alpha0=0 values.",
            "analytic",
            "analytic_zero_coupling",
        ),
        _assertion(
            "T001_TAIL_STABILITY",
            max(item["relative_error"] for item in convergence_points)
            <= thresholds["tail_convergence_max_relative_error"],
            "Tightening the positive Bessel cutoff leaves selected values unchanged.",
            "numeric",
            "tail_convergence",
        ),
        _assertion(
            "T001_QUADRATURE_AGREEMENT",
            max(item["relative_error"] for item in direct_points)
            <= thresholds["direct_quadrature_max_relative_error"],
            "The Bessel series agrees with direct proper-time quadrature.",
            "numeric",
            "direct_quadrature",
        ),
        _assertion(
            "T001_SMALL_ALPHA_CORRECTION",
            max(item["relative_error"] for item in small_alpha_checks)
            <= thresholds["small_alpha_scaled_max_relative_error"],
            "alpha0*S_c approaches the independently corrected K3 coefficient.",
            "analytic",
            "small_alpha_correction",
        ),
        _assertion(
            "T001_MONOTONE_SUPPRESSION",
            monotone_landau and monotone_correction,
            "Both negative energy contributions move monotonically toward zero.",
            "numeric",
            "monotonicity",
        ),
        _assertion(
            "T001_MASS_ORDERING",
            mass_order_landau and mass_order_correction,
            "Increasing m0 suppresses the magnitude in both panels.",
            "numeric",
            "mass_ordering",
        ),
        _assertion(
            "T001_LARGE_ALPHA",
            max(
                large_alpha_check["landau_relative_error"],
                large_alpha_check["correction_relative_error"],
            )
            <= thresholds["large_alpha_leading_max_relative_error"],
            "The corrected leading K1 terms describe the large-alpha tails.",
            "analytic",
            "large_alpha",
        ),
    ]
    status = (
        "passed"
        if all(assertion["status"] == "passed" for assertion in assertions)
        else "failed"
    )
    return {
        "schema_version": 1,
        "status": status,
        "target_id": "T001",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics",
        "paper_parameters": {
            "m0": list(MASSES),
            "landau_alpha0_range": [
                float(alpha_landau[0]),
                float(alpha_landau[-1]),
            ],
            "correction_alpha0_domain_and_axis": [
                float(alpha_correction[0]),
                float(alpha_correction[-1]),
                "paper axis begins at the singular endpoint alpha0=0",
            ],
        },
        "thresholds": thresholds,
        "analytic_zero_coupling": analytic_errors,
        "tail_convergence": convergence_points,
        "direct_quadrature": direct_points,
        "small_alpha_correction": small_alpha_checks,
        "large_alpha": large_alpha_check,
        "monotonicity": {
            "landau": monotone_landau,
            "correction": monotone_correction,
        },
        "mass_ordering": {
            "landau": mass_order_landau,
            "correction": mass_order_correction,
        },
        "physics_assertions": assertions,
        "paper_formula_audit": {
            "eq26_lower_bound": "corrected_to_n_ge_0",
            "eq37_dimensionless_denominator": "alpha0_used_in_both_factors",
            "eq39_final_asymptotic": "corrected_square_root_exponent",
            "eq42_small_alpha_correction": "corrected_K3_identity",
        },
    }


def _t002_checks(
    alpha_ratio: np.ndarray,
    curves: dict[float, np.ndarray],
) -> dict[str, Any]:
    identity_points: list[dict[str, float]] = []
    direct_points: list[dict[str, float]] = []
    for alpha, mass in ((1.0, 0.0), (3.0, 0.5), (10.0, 1.5)):
        landau = landau_magnitude(alpha, mass)
        correction = correction_magnitude(alpha, mass)
        direct_ratio = 1.0 + correction / landau
        model_ratio = energy_ratio(alpha, mass)
        identity_points.append(
            {
                "alpha0": alpha,
                "m0": mass,
                "ratio": model_ratio,
                "identity_value": direct_ratio,
                "absolute_error": abs(model_ratio - direct_ratio),
            }
        )
    alpha, mass = 3.0, 0.5
    direct_landau = direct_proper_time_magnitude(
        alpha,
        mass,
        sector="landau",
    )
    direct_correction = direct_proper_time_magnitude(
        alpha,
        mass,
        sector="correction",
    )
    direct_ratio = 1.0 + direct_correction.value / direct_landau.value
    series_ratio = energy_ratio(
        alpha,
        mass,
        argument_cutoff=TIGHT_BESSEL_ARGUMENT_CUTOFF,
    )
    direct_points.append(
        {
            "alpha0": alpha,
            "m0": mass,
            "series_ratio": series_ratio,
            "direct_quadrature_ratio": direct_ratio,
            "relative_error": _relative_error(series_ratio, direct_ratio),
        }
    )

    above_one = all(bool(np.all(values > 1.0)) for values in curves.values())
    monotone = all(
        bool(np.all(np.diff(values) <= 2.0e-10))
        for values in curves.values()
    )
    mass_order = _ratio_mass_order_pass(curves)
    endpoint_offsets = {
        _mass_key(mass): float(values[-1] - 1.0)
        for mass, values in curves.items()
    }
    thresholds = {
        "identity_max_absolute_error": 1.0e-13,
        "quadrature_max_relative_error": 2.0e-7,
        "alpha25_max_offset_from_one": 0.06,
    }
    assertions = [
        _assertion(
            "T002_RATIO_IDENTITY",
            max(item["absolute_error"] for item in identity_points)
            <= thresholds["identity_max_absolute_error"],
            "The plotted ratio is pointwise 1+S_c/S_L.",
            "analytic",
            "ratio_identity",
        ),
        _assertion(
            "T002_QUADRATURE_AGREEMENT",
            max(item["relative_error"] for item in direct_points)
            <= thresholds["quadrature_max_relative_error"],
            "A direct proper-time quadrature reproduces the ratio.",
            "numeric",
            "direct_quadrature_ratio",
        ),
        _assertion(
            "T002_POSITIVE_MONOTONE",
            above_one and monotone,
            "Every mass curve remains above one and decreases with alpha0.",
            "numeric",
            "ratio_shape",
        ),
        _assertion(
            "T002_MASS_ORDERING",
            mass_order,
            "At fixed alpha0 the ratio follows the paper's m0 ordering.",
            "numeric",
            "mass_ordering",
        ),
        _assertion(
            "T002_LARGE_ALPHA_LIMIT",
            max(endpoint_offsets.values())
            <= thresholds["alpha25_max_offset_from_one"],
            "All four curves approach one by the paper's upper alpha0 range.",
            "analytic",
            "large_alpha_limit",
        ),
    ]
    status = (
        "passed"
        if all(assertion["status"] == "passed" for assertion in assertions)
        else "failed"
    )
    return {
        "schema_version": 1,
        "status": status,
        "target_id": "T002",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics",
        "paper_parameters": {
            "m0": list(MASSES),
            "alpha0_domain_and_axis": [
                float(alpha_ratio[0]),
                float(alpha_ratio[-1]),
                "paper axis begins at the singular endpoint alpha0=0",
            ],
        },
        "thresholds": thresholds,
        "ratio_identity": identity_points,
        "direct_quadrature_ratio": direct_points,
        "shape": {
            "above_one": above_one,
            "monotone_decreasing": monotone,
            "mass_ordering": mass_order,
            "alpha25_offsets_from_one": endpoint_offsets,
        },
        "physics_assertions": assertions,
    }


def _plot_landau(
    alpha: np.ndarray,
    curves: dict[float, np.ndarray],
    output_path: Path,
) -> None:
    figure, axis = _paper_figure(
        pixel_size=(1185, 825),
        axes_box=(196, 20, 1149, 726),
    )
    _plot_curves(axis, alpha, curves)
    axis.set_xlim(0.0, 30.0)
    axis.set_ylim(-0.6, 0.005)
    axis.set_xticks(np.arange(5.0, 31.0, 5.0))
    axis.set_yticks(np.arange(-0.6, 0.01, 0.1))
    axis.set_xlabel(r"$\alpha_0$")
    axis.set_ylabel(
        r"$\dfrac{8\pi^2 L^3 E_{\mathrm{L}}^{\mathrm{ren}}}{A}$",
        labelpad=4,
    )
    _styled_legend(axis, loc="lower right")
    _save_figure(figure, output_path)


def _plot_correction(
    alpha: np.ndarray,
    curves: dict[float, np.ndarray],
    output_path: Path,
) -> None:
    figure, axis = _paper_figure(
        pixel_size=(1185, 825),
        axes_box=(196, 22, 1149, 695),
    )
    _plot_curves(axis, alpha, curves)
    axis.set_xlim(0.0, 12.0)
    axis.set_ylim(-1.6, 0.01)
    axis.set_xticks(np.arange(2.0, 12.1, 2.0))
    axis.set_yticks(np.arange(-1.6, 0.01, 0.2))
    axis.set_xlabel(r"$\alpha_0$")
    axis.set_ylabel(
        r"$\dfrac{8\pi^2 L^3 E_{\mathrm{c}}^{\mathrm{ren}}}{A}$",
        labelpad=4,
    )
    _styled_legend(axis, loc="lower right")
    _save_figure(figure, output_path)


def _plot_ratio(
    alpha: np.ndarray,
    curves: dict[float, np.ndarray],
    output_path: Path,
) -> None:
    figure, axis = _paper_figure(
        pixel_size=(1183, 826),
        axes_box=(175, 27, 1147, 727),
    )
    _plot_curves(axis, alpha, curves)
    axis.axhline(1.0, color="black", linestyle=":", linewidth=1.3)
    axis.set_xlim(0.0, 25.0)
    axis.set_ylim(0.9, 5.0)
    axis.set_xticks(np.arange(5.0, 25.1, 5.0))
    axis.set_yticks(np.arange(1.0, 5.1, 0.5))
    axis.set_xlabel(r"$\alpha_0$")
    axis.set_ylabel(
        r"$\dfrac{E_0^{\mathrm{ren}}}{E_{\mathrm{L}}^{\mathrm{ren}}}$",
        labelpad=4,
    )
    _styled_legend(axis, loc="upper right")
    _save_figure(figure, output_path)


def _paper_figure(
    *,
    pixel_size: tuple[int, int],
    axes_box: tuple[int, int, int, int],
) -> tuple[plt.Figure, plt.Axes]:
    width, height = pixel_size
    left, top, right, bottom = axes_box
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 16,
            "axes.labelsize": 19,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "legend.fontsize": 13,
            "mathtext.fontset": "dejavusans",
            "axes.linewidth": 1.0,
        }
    )
    figure = plt.figure(figsize=(width / 150.0, height / 150.0), dpi=150)
    axis = figure.add_axes(
        [
            left / width,
            (height - bottom) / height,
            (right - left) / width,
            (bottom - top) / height,
        ]
    )
    axis.grid(True, which="major", linestyle=":", color="#bdbdbd", linewidth=0.7)
    axis.tick_params(
        which="major",
        direction="in",
        length=7,
        width=1.0,
        top=True,
        right=True,
    )
    axis.tick_params(
        which="minor",
        direction="in",
        length=3.5,
        width=0.9,
        top=True,
        right=True,
    )
    axis.xaxis.set_minor_locator(AutoMinorLocator(5))
    axis.yaxis.set_minor_locator(AutoMinorLocator(5))
    return figure, axis


def _plot_curves(
    axis: plt.Axes,
    alpha: np.ndarray,
    curves: dict[float, np.ndarray],
) -> None:
    for mass, color, style, width in zip(
        MASSES,
        COLORS,
        LINESTYLES,
        LINEWIDTHS,
        strict=True,
    ):
        axis.plot(
            alpha,
            curves[mass],
            color=color,
            linestyle=style,
            linewidth=width,
            label=rf"$m_0={_mass_label(mass)}$",
        )


def _styled_legend(axis: plt.Axes, *, loc: str) -> None:
    legend = axis.legend(
        loc=loc,
        frameon=True,
        framealpha=1.0,
        facecolor="white",
        edgecolor="black",
    )
    legend.get_frame().set_linewidth(1.0)


def _save_figure(figure: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = output_path.with_suffix(".pdf")
    figure.savefig(pdf_path, facecolor="white")
    plt.close(figure)
    subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-singlefile",
            "-r",
            "150",
            str(pdf_path),
            str(output_path.with_suffix("")),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def _mass_order_pass(curves: dict[float, np.ndarray]) -> bool:
    matrix = np.vstack([curves[mass] for mass in MASSES])
    return bool(np.all(np.diff(matrix, axis=0) >= -2.0e-11))


def _ratio_mass_order_pass(curves: dict[float, np.ndarray]) -> bool:
    matrix = np.vstack([curves[mass] for mass in MASSES])
    return bool(np.all(np.diff(matrix, axis=0) >= -2.0e-10))


def _assertion(
    assertion_id: str,
    passed: bool,
    claim: str,
    tier: str,
    evidence_key: str,
) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "tier": tier,
        "essential": True,
        "status": "passed" if passed else "failed",
        "evidence": f"outputs/checks/{assertion_id.split('_')[0]}_scientific_checks.json#{evidence_key}",
        "claim": claim,
    }


def _relative_error(observed: float, expected: float) -> float:
    scale = max(abs(expected), 1.0e-300)
    return abs(observed - expected) / scale


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _require_guard(target_id: str) -> None:
    guarded_target = os.environ.get("PRAGENT_GUARDED_TARGET_ID", "")
    guarded_stage = os.environ.get("PRAGENT_GUARDED_STAGE", "")
    if guarded_target != target_id:
        raise SystemExit(
            f"target authorization mismatch: requested={target_id}, guarded={guarded_target or '<missing>'}"
        )
    if guarded_stage != "final_reproduction":
        raise SystemExit(
            "this reader-facing runner requires PRAGENT_GUARDED_STAGE=final_reproduction"
        )


def _relative(path: Path) -> str:
    return str(path.relative_to(WORKSPACE))


def _format_float(value: float) -> str:
    if not math.isfinite(float(value)):
        raise ValueError("attempted to write non-finite numeric evidence")
    return f"{float(value):.12g}"


def _mass_key(mass: float) -> str:
    return f"m0={_mass_label(mass)}"


def _mass_label(mass: float) -> str:
    return f"{mass:g}"


def _series_id(panel: str, mass: float) -> str:
    mass_suffix = _mass_label(mass).replace(".", "P")
    return f"{panel}_M0_{mass_suffix}"


if __name__ == "__main__":
    raise SystemExit(main())
