#!/usr/bin/env python3
"""Guarded, one-target-at-a-time runner for the frozen Trial."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.try_model import (  # noqa: E402
    ModelParameters,
    compute_receiver,
    compute_response,
    finite_difference_scores,
    full_fisher,
    max_scaled_error,
    noise_weight,
    relative_l2,
    source_grid,
    weighted_inner,
    width_scan,
    zero_crossings,
)


PAPER_ID = "2605.02873"
TARGET_TO_ITEM = {
    "T-FIG001A": "FIG001A",
    "T-FIG001B": "FIG001B",
    "T-FIG001C": "FIG001C",
    "T-FIG001D": "FIG001D",
    "T-FIGS001": "FIGS001",
}
PAPER_FULL_FISHER = np.array(
    [
        [5.11999612e-11, -6.62496429e-13],
        [-6.62496429e-13, 7.99913250e-11],
    ]
)
PAPER_OPTIMIZED_FISHER = np.array(
    [
        [5.11939906e-11, -6.56482435e-13],
        [-6.56482435e-13, 7.99852673e-11],
    ]
)
PAPER_OPTIMIZED_RETENTION = np.array([0.99980958, 1.0])
PAPER_TOY_FISHER = np.array(
    [
        [4.5992e-12, 4.2067e-12],
        [4.2067e-12, 4.2061e-11],
    ]
)
PAPER_TOY_RETENTION = np.array([0.07988, 0.53729])
PAPER_WIDTH_RATIOS = np.array([1.75e-5, 2.99e-4, 7.93e-3, 1.76e-1, 1.56])


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_jsonable(payload), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _data_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check(
    check_id: str,
    passed: bool,
    observed: Any,
    threshold: str,
    claim: str,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "passed" if passed else "failed",
        "observed": _jsonable(observed),
        "threshold": threshold,
        "claim": claim,
    }


def _figure_modules():
    cache = Path(tempfile.gettempdir()) / "pragent-2605-02873-mpl"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _style_axis(axis, panel_label: str) -> None:
    axis.text(
        0.02,
        0.96,
        panel_label,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontweight="bold",
    )
    axis.tick_params(direction="in", width=0.8, labelsize=8)
    for spine in axis.spines.values():
        spine.set_linewidth(0.8)


def _save_figure(figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=300, facecolor="white", bbox_inches="tight")
    figure.clear()


def _common_convergence(
    parameters: ModelParameters, receiver
) -> tuple[dict[str, float], Any]:
    refined = compute_receiver(
        parameters,
        y_m=receiver.response.y_m,
        order=parameters.slit_quadrature_order * 2,
    )
    metrics = {
        "R0_max_scaled_error_order_doubling": max_scaled_error(
            receiver.response.R0, refined.response.R0
        ),
        "gt_max_scaled_error_order_doubling": max_scaled_error(
            receiver.response.gt, refined.response.gt
        ),
        "gf_max_scaled_error_order_doubling": max_scaled_error(
            receiver.response.gf, refined.response.gf
        ),
        "full_fisher_relative_l2_order_doubling": relative_l2(
            receiver.full_fisher, refined.full_fisher
        ),
    }
    return metrics, refined


def run_fig001a(parameters: ModelParameters) -> tuple[Path, Path, list[dict[str, Any]], dict[str, Any]]:
    receiver = compute_receiver(parameters)
    convergence, _ = _common_convergence(parameters, receiver)
    response = receiver.response
    data_path = WORKSPACE / "outputs/data/FIG001A.csv"
    rows = [
        {
            "series_id": "FIG001A_R0",
            "y_m": float(y),
            "y_mm": float(y * 1e3),
            "R0": float(value),
        }
        for y, value in zip(response.y_m, response.R0, strict=True)
    ]
    _write_csv(data_path, ["series_id", "y_m", "y_mm", "R0"], rows)
    checks = [
        _check(
            "FIG001A-NONNEGATIVE",
            float(np.min(response.R0)) >= -1e-20,
            float(np.min(response.R0)),
            "min(R0) >= -1e-20",
            "The generated intensity is nonnegative.",
        ),
        _check(
            "FIG001A-BOUND",
            float(np.max(response.R0)) <= (2.0 * parameters.a_m) ** 2 * (1.0 + 1e-10),
            float(np.max(response.R0)),
            "max(R0) <= (total open width)^2",
            "The coherent aperture-length bound is respected.",
        ),
        _check(
            "FIG001A-QUADRATURE",
            convergence["R0_max_scaled_error_order_doubling"] < 1e-10,
            convergence["R0_max_scaled_error_order_doubling"],
            "< 1e-10",
            "Baseline response is converged under doubled slit quadrature order.",
        ),
        _check(
            "FIG001A-FRINGES",
            zero_crossings(np.gradient(response.R0, response.y_m)) >= 8,
            zero_crossings(np.gradient(response.R0, response.y_m)),
            "at least 8 derivative sign changes",
            "The complete paper source window contains a resolved multi-fringe response.",
        ),
    ]
    plt = _figure_modules()
    figure, axis = plt.subplots(figsize=(3.35, 2.55))
    axis.plot(response.y_m * 1e3, response.R0, color="black", linewidth=1.2)
    axis.set_xlim(-1.5, 1.5)
    axis.set_xlabel("source coordinate $y$ (mm)", fontsize=8)
    axis.set_ylabel("baseline TRY response $R_0(y)$", fontsize=8)
    axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    _style_axis(axis, "(a)")
    figure.tight_layout(pad=0.7)
    figure_path = WORKSPACE / "outputs/figures/FIG001A.png"
    _save_figure(figure, figure_path)
    return data_path, figure_path, checks, {
        "convergence": convergence,
        "R0_min": float(np.min(response.R0)),
        "R0_max": float(np.max(response.R0)),
        "fringe_extrema_count": zero_crossings(
            np.gradient(response.R0, response.y_m)
        ),
    }


def run_fig001b(parameters: ModelParameters) -> tuple[Path, Path, list[dict[str, Any]], dict[str, Any]]:
    receiver = compute_receiver(parameters)
    convergence, _ = _common_convergence(parameters, receiver)
    response = receiver.response
    fd_gt, fd_gf = finite_difference_scores(
        parameters, response.y_m, epsilon=1e-6
    )
    gt_fd_error = max_scaled_error(response.gt, fd_gt)
    gf_fd_error = max_scaled_error(response.gf, fd_gf)
    data_path = WORKSPACE / "outputs/data/FIG001B.csv"
    rows = [
        {
            "y_m": float(y),
            "y_mm": float(y * 1e3),
            "gt": float(gt),
            "gf": float(gf),
            "gt_finite_difference": float(fd_t),
            "gf_finite_difference": float(fd_f),
        }
        for y, gt, gf, fd_t, fd_f in zip(
            response.y_m, response.gt, response.gf, fd_gt, fd_gf, strict=True
        )
    ]
    _write_csv(
        data_path,
        [
            "y_m",
            "y_mm",
            "gt",
            "gf",
            "gt_finite_difference",
            "gf_finite_difference",
        ],
        rows,
    )
    checks = [
        _check(
            "FIG001B-TILT-FD",
            gt_fd_error < 2e-7,
            gt_fd_error,
            "< 2e-7 max-scaled error",
            "The analytic tilt score matches an independent central derivative.",
        ),
        _check(
            "FIG001B-DEFOCUS-FD",
            gf_fd_error < 2e-7,
            gf_fd_error,
            "< 2e-7 max-scaled error",
            "The analytic defocus score matches an independent central derivative.",
        ),
        _check(
            "FIG001B-TILT-QUADRATURE",
            convergence["gt_max_scaled_error_order_doubling"] < 1e-10,
            convergence["gt_max_scaled_error_order_doubling"],
            "< 1e-10",
            "Tilt score is converged under doubled quadrature order.",
        ),
        _check(
            "FIG001B-DEFOCUS-QUADRATURE",
            convergence["gf_max_scaled_error_order_doubling"] < 1e-10,
            convergence["gf_max_scaled_error_order_doubling"],
            "< 1e-10",
            "Defocus score is converged under doubled quadrature order.",
        ),
        _check(
            "FIG001B-BOTH-NONZERO",
            float(np.max(np.abs(response.gt))) > 0.0
            and float(np.max(np.abs(response.gf))) > 0.0,
            {
                "max_abs_gt": float(np.max(np.abs(response.gt))),
                "max_abs_gf": float(np.max(np.abs(response.gf))),
            },
            "both maxima > 0",
            "Finite width makes both local channels observable.",
        ),
    ]
    plt = _figure_modules()
    figure, axis = plt.subplots(figsize=(3.35, 2.55))
    axis.plot(
        response.y_m * 1e3,
        response.gt,
        color="#0066cc",
        linewidth=1.1,
        label="$g_t(y)$",
    )
    axis.plot(
        response.y_m * 1e3,
        response.gf,
        color="#d62728",
        linewidth=1.1,
        linestyle="--",
        label="$g_f(y)$",
    )
    axis.set_xlim(-1.5, 1.5)
    axis.set_xlabel("source coordinate $y$ (mm)", fontsize=8)
    axis.set_ylabel("local response function", fontsize=8)
    axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    axis.legend(frameon=False, fontsize=7, loc="upper right")
    _style_axis(axis, "(b)")
    figure.tight_layout(pad=0.7)
    figure_path = WORKSPACE / "outputs/figures/FIG001B.png"
    _save_figure(figure, figure_path)
    return data_path, figure_path, checks, {
        "convergence": convergence,
        "finite_difference_epsilon": 1e-6,
        "gt_finite_difference_max_scaled_error": gt_fd_error,
        "gf_finite_difference_max_scaled_error": gf_fd_error,
        "max_abs_gt": float(np.max(np.abs(response.gt))),
        "max_abs_gf": float(np.max(np.abs(response.gf))),
    }


def run_fig001c(parameters: ModelParameters) -> tuple[Path, Path, list[dict[str, Any]], dict[str, Any]]:
    receiver = compute_receiver(parameters)
    y_m = receiver.response.y_m
    noise = receiver.noise
    optimized = receiver.optimized_codes
    toy = receiver.toy_codes
    constant = np.ones_like(y_m)
    residuals = {
        "optimized_t_constant": weighted_inner(
            y_m, noise, optimized[0], constant
        ),
        "optimized_f_constant": weighted_inner(
            y_m, noise, optimized[1], constant
        ),
        "optimized_cross": weighted_inner(
            y_m, noise, optimized[0], optimized[1]
        ),
        "optimized_t_norm_minus_one": weighted_inner(
            y_m, noise, optimized[0], optimized[0]
        )
        - 1.0,
        "optimized_f_norm_minus_one": weighted_inner(
            y_m, noise, optimized[1], optimized[1]
        )
        - 1.0,
        "toy_t_constant": weighted_inner(y_m, noise, toy[0], constant),
        "toy_f_constant": weighted_inner(y_m, noise, toy[1], constant),
        "toy_cross": weighted_inner(y_m, noise, toy[0], toy[1]),
    }
    max_residual = max(abs(value) for value in residuals.values())
    optimized_plot = optimized / np.max(np.abs(optimized), axis=1)[:, None]
    toy_plot = toy / np.max(np.abs(toy), axis=1)[:, None]
    data_path = WORKSPACE / "outputs/data/FIG001C.csv"
    rows = [
        {
            "y_m": float(y),
            "y_mm": float(y * 1e3),
            "optimized_wt": float(optimized[0, index]),
            "optimized_wf": float(optimized[1, index]),
            "toy_ht": float(toy[0, index]),
            "toy_hf": float(toy[1, index]),
            "optimized_wt_plot": float(optimized_plot[0, index]),
            "optimized_wf_plot": float(optimized_plot[1, index]),
            "toy_ht_plot": float(toy_plot[0, index]),
            "toy_hf_plot": float(toy_plot[1, index]),
        }
        for index, y in enumerate(y_m)
    ]
    _write_csv(
        data_path,
        [
            "y_m",
            "y_mm",
            "optimized_wt",
            "optimized_wf",
            "toy_ht",
            "toy_hf",
            "optimized_wt_plot",
            "optimized_wf_plot",
            "toy_ht_plot",
            "toy_hf_plot",
        ],
        rows,
    )
    optimized_crossings = [
        zero_crossings(optimized_plot[0]),
        zero_crossings(optimized_plot[1]),
    ]
    toy_crossings = [zero_crossings(toy_plot[0]), zero_crossings(toy_plot[1])]
    checks = [
        _check(
            "FIG001C-ORTHONORMALITY",
            max_residual < 1e-10,
            residuals,
            "all absolute residuals < 1e-10",
            "Optimized and toy code pairs satisfy the declared N-metric construction.",
        ),
        _check(
            "FIG001C-FRINGE-LOCKED",
            min(optimized_crossings) > max(toy_crossings),
            {
                "optimized_zero_crossings": optimized_crossings,
                "toy_zero_crossings": toy_crossings,
            },
            "each optimized code has more zero crossings than either toy code",
            "The physical codes are substantially more oscillatory than the smooth toy basis.",
        ),
        _check(
            "FIG001C-COVARIANCE",
            relative_l2(receiver.optimized_covariance, np.eye(2)) < 1e-10,
            receiver.optimized_covariance,
            "relative L2 distance from identity < 1e-10",
            "Normalized optimized codes have identity channel covariance.",
        ),
    ]
    plt = _figure_modules()
    figure, axis = plt.subplots(figsize=(3.35, 2.55))
    axis.plot(
        y_m * 1e3,
        optimized_plot[0],
        color="#0066cc",
        linewidth=1.0,
        label="optimal $w_t$",
    )
    axis.plot(
        y_m * 1e3,
        optimized_plot[1],
        color="#d62728",
        linewidth=1.0,
        linestyle="--",
        label="optimal $w_f$",
    )
    axis.plot(
        y_m * 1e3,
        toy_plot[0],
        color="0.45",
        linewidth=0.9,
        linestyle="-.",
        label="toy $h_t$",
    )
    axis.plot(
        y_m * 1e3,
        toy_plot[1],
        color="0.2",
        linewidth=0.9,
        linestyle=":",
        label="toy $h_f$",
    )
    axis.set_xlim(-1.5, 1.5)
    axis.set_ylim(-1.08, 1.08)
    axis.set_xlabel("source coordinate $y$ (mm)", fontsize=8)
    axis.set_ylabel("normalized source code", fontsize=8)
    axis.legend(frameon=False, fontsize=6.5, ncol=2, loc="lower left")
    _style_axis(axis, "(c)")
    figure.tight_layout(pad=0.7)
    figure_path = WORKSPACE / "outputs/figures/FIG001C.png"
    _save_figure(figure, figure_path)
    return data_path, figure_path, checks, {
        "orthogonality_residuals": residuals,
        "optimized_zero_crossings": optimized_crossings,
        "toy_zero_crossings": toy_crossings,
        "optimized_covariance": receiver.optimized_covariance,
        "toy_covariance": receiver.toy_covariance,
    }


def run_fig001d(parameters: ModelParameters) -> tuple[Path, Path, list[dict[str, Any]], dict[str, Any]]:
    receiver = compute_receiver(parameters)
    full_error = relative_l2(receiver.full_fisher, PAPER_FULL_FISHER)
    optimized_fisher_error = relative_l2(
        receiver.optimized_fisher, PAPER_OPTIMIZED_FISHER
    )
    optimized_retention_error = max_scaled_error(
        receiver.optimized_retention, PAPER_OPTIMIZED_RETENTION
    )
    toy_fisher_error = relative_l2(receiver.toy_fisher, PAPER_TOY_FISHER)
    toy_retention_error = max_scaled_error(
        receiver.toy_retention, PAPER_TOY_RETENTION
    )
    data_path = WORKSPACE / "outputs/data/FIG001D.csv"
    rows = [
        {
            "principal_mode": index + 1,
            "optimized_retention": float(receiver.optimized_retention[index]),
            "toy_retention": float(receiver.toy_retention[index]),
        }
        for index in range(2)
    ]
    _write_csv(
        data_path,
        ["principal_mode", "optimized_retention", "toy_retention"],
        rows,
    )
    checks = [
        _check(
            "FIG001D-FULL-FISHER",
            full_error < 5e-4,
            full_error,
            "< 5e-4 relative L2 error",
            "The independently integrated full Fisher matrix matches the printed paper matrix.",
        ),
        _check(
            "FIG001D-OPTIMIZED-FISHER",
            optimized_fisher_error < 5e-4,
            optimized_fisher_error,
            "< 5e-4 relative L2 error",
            "The optimized coded Fisher matrix matches the printed paper matrix.",
        ),
        _check(
            "FIG001D-OPTIMIZED-RETENTION",
            optimized_retention_error < 5e-4,
            optimized_retention_error,
            "< 5e-4 max-scaled error",
            "The optimized principal retention fractions match the printed values.",
        ),
        _check(
            "FIG001D-TOY-FISHER",
            toy_fisher_error < 2e-3,
            toy_fisher_error,
            "< 2e-3 relative L2 error",
            "The toy coded Fisher matrix matches the rounded supplementary matrix.",
        ),
        _check(
            "FIG001D-TOY-RETENTION",
            toy_retention_error < 2e-3,
            toy_retention_error,
            "< 2e-3 max-scaled error",
            "The toy principal retention fractions match the printed values.",
        ),
        _check(
            "FIG001D-PROJECTION-BOUND",
            float(np.min(receiver.optimized_retention)) >= -1e-10
            and float(np.max(receiver.optimized_retention)) <= 1.0 + 1e-10
            and float(np.min(receiver.toy_retention)) >= -1e-10
            and float(np.max(receiver.toy_retention)) <= 1.0 + 1e-10,
            {
                "optimized": receiver.optimized_retention,
                "toy": receiver.toy_retention,
            },
            "all eigenvalues in [0, 1] up to 1e-10",
            "Both coded receivers obey the Fisher projection bound.",
        ),
    ]
    plt = _figure_modules()
    figure, axis = plt.subplots(figsize=(3.35, 2.55))
    positions = np.arange(2)
    width = 0.34
    axis.bar(
        positions - width / 2,
        receiver.optimized_retention,
        width,
        color="#2f77b5",
        label="optimized codes",
    )
    axis.bar(
        positions + width / 2,
        receiver.toy_retention,
        width,
        color="0.75",
        edgecolor="0.35",
        linewidth=0.6,
        label="toy codes",
    )
    axis.set_xticks(positions, ["mode 1", "mode 2"])
    axis.set_ylim(0.0, 1.05)
    axis.set_ylabel("information retention", fontsize=8)
    axis.legend(frameon=False, fontsize=6.5, loc="upper left")
    _style_axis(axis, "(d)")
    figure.tight_layout(pad=0.7)
    figure_path = WORKSPACE / "outputs/figures/FIG001D.png"
    _save_figure(figure, figure_path)
    return data_path, figure_path, checks, {
        "generated": {
            "full_fisher": receiver.full_fisher,
            "optimized_fisher": receiver.optimized_fisher,
            "optimized_retention": receiver.optimized_retention,
            "toy_fisher": receiver.toy_fisher,
            "toy_retention": receiver.toy_retention,
        },
        "paper_analytic_reference": {
            "full_fisher": PAPER_FULL_FISHER,
            "optimized_fisher": PAPER_OPTIMIZED_FISHER,
            "optimized_retention": PAPER_OPTIMIZED_RETENTION,
            "toy_fisher": PAPER_TOY_FISHER,
            "toy_retention": PAPER_TOY_RETENTION,
        },
        "relative_errors": {
            "full_fisher": full_error,
            "optimized_fisher": optimized_fisher_error,
            "optimized_retention": optimized_retention_error,
            "toy_fisher": toy_fisher_error,
            "toy_retention": toy_retention_error,
        },
    }


def run_figs001(parameters: ModelParameters) -> tuple[Path, Path, list[dict[str, Any]], dict[str, Any]]:
    widths_um = [20.0, 40.0, 80.0, 150.0, 250.0]
    rows = width_scan(parameters, widths_um)
    generated_ratios = np.array(
        [row["rho_Fff_over_Ftt"] for row in rows], dtype=float
    )
    ratio_error = max_scaled_error(generated_ratios, PAPER_WIDTH_RATIOS)
    # Independent convergence at every width with doubled slit quadrature order.
    refined_parameters = ModelParameters(
        **{
            **parameters.to_dict(),
            "slit_quadrature_order": parameters.slit_quadrature_order * 2,
        }
    )
    refined_rows = width_scan(refined_parameters, widths_um)
    refined_ratios = np.array(
        [row["rho_Fff_over_Ftt"] for row in refined_rows], dtype=float
    )
    convergence_error = max_scaled_error(generated_ratios, refined_ratios)
    output_rows = []
    for row, reference, refined in zip(
        rows, PAPER_WIDTH_RATIOS, refined_ratios, strict=True
    ):
        output_rows.append(
            {
                **row,
                "rho_refined_quadrature": float(refined),
                "paper_rounded_analytic_reference": float(reference),
            }
        )
    data_path = WORKSPACE / "outputs/data/FIGS001.csv"
    _write_csv(
        data_path,
        [
            "slit_width_um",
            "Ftt",
            "Ftf",
            "Fff",
            "rho_Fff_over_Ftt",
            "rho_refined_quadrature",
            "paper_rounded_analytic_reference",
        ],
        output_rows,
    )
    checks = [
        _check(
            "FIGS001-PRINTED-VALUES",
            ratio_error < 5e-3,
            {
                "generated": generated_ratios,
                "paper_rounded": PAPER_WIDTH_RATIOS,
                "max_scaled_error": ratio_error,
            },
            "max-scaled error < 5e-3",
            "All five independently generated width ratios match the rounded paper values.",
        ),
        _check(
            "FIGS001-QUADRATURE",
            convergence_error < 1e-9,
            convergence_error,
            "< 1e-9 max-scaled error",
            "The complete width scan is converged under doubled slit quadrature order.",
        ),
        _check(
            "FIGS001-MONOTONIC",
            bool(np.all(np.diff(generated_ratios) > 0.0)),
            np.diff(generated_ratios),
            "all successive differences > 0",
            "Relative defocus information rises at every printed slit width.",
        ),
        _check(
            "FIGS001-NARROW-SLIT",
            float(generated_ratios[0]) < 1e-4,
            float(generated_ratios[0]),
            "< 1e-4 at 20 um",
            "The narrow-slit calculation suppresses first-order defocus information.",
        ),
    ]
    plt = _figure_modules()
    figure, axis = plt.subplots(figsize=(5.0, 3.85))
    axis.plot(
        widths_um,
        generated_ratios,
        color="#0072bd",
        linewidth=1.5,
        marker="o",
        markersize=4.5,
    )
    axis.set_xlim(0, 260)
    axis.set_ylim(0, 1.6)
    axis.set_xlabel("slit width $a$ ($\\mu$m)", fontsize=9)
    axis.set_ylabel("$F_{ff}^{\\mathrm{full}}/F_{tt}^{\\mathrm{full}}$", fontsize=9)
    axis.grid(True, color="0.88", linewidth=0.7)
    axis.tick_params(direction="out", labelsize=8)
    figure.tight_layout(pad=0.8)
    figure_path = WORKSPACE / "outputs/figures/FIGS001.png"
    _save_figure(figure, figure_path)
    return data_path, figure_path, checks, {
        "generated_ratios": generated_ratios,
        "refined_ratios": refined_ratios,
        "paper_rounded_analytic_reference": PAPER_WIDTH_RATIOS,
        "max_scaled_error_to_paper": ratio_error,
        "quadrature_convergence_max_scaled_error": convergence_error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=sorted(TARGET_TO_ITEM))
    args = parser.parse_args()

    guarded_target = os.environ.get("PRAGENT_GUARDED_TARGET_ID")
    guarded_stage = os.environ.get("PRAGENT_GUARDED_STAGE")
    if guarded_target != args.target:
        raise SystemExit(
            f"guard mismatch: requested {args.target}, environment authorizes {guarded_target!r}"
        )
    if guarded_stage != "final_reproduction":
        raise SystemExit(
            f"this frozen Trial runner requires final_reproduction, got {guarded_stage!r}"
        )

    parameters = ModelParameters()
    started = time.perf_counter()
    runners = {
        "T-FIG001A": run_fig001a,
        "T-FIG001B": run_fig001b,
        "T-FIG001C": run_fig001c,
        "T-FIG001D": run_fig001d,
        "T-FIGS001": run_figs001,
    }
    data_path, figure_path, checks, metrics = runners[args.target](parameters)
    calculation_seconds = time.perf_counter() - started
    status = "passed" if all(item["status"] == "passed" for item in checks) else "failed"
    item_id = TARGET_TO_ITEM[args.target]
    check_path = WORKSPACE / f"outputs/checks/{item_id}.json"
    payload = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "target_id": args.target,
        "figure_id": item_id,
        "artifact_stage": guarded_stage,
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics",
        "status": status,
        "calculation_seconds": calculation_seconds,
        "parameters": parameters.to_dict(),
        "artifacts": {
            "data": str(data_path.relative_to(WORKSPACE)),
            "figure": str(figure_path.relative_to(WORKSPACE)),
            "data_sha256": _data_hash(data_path),
            "figure_sha256": _data_hash(figure_path),
        },
        "scientific_checks": checks,
        "metrics": metrics,
    }
    _write_json(check_path, payload)
    print(json.dumps(_jsonable(payload), indent=2, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
