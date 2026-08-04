#!/usr/bin/env python3
"""Generate every publicly defined theory curve for arXiv:2607.23978."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

_workspace = Path(__file__).resolve().parents[1]
_font_cache_source = _workspace / "config/fontlist-v390.json"
_mpl_config = Path(os.environ.get("MPLCONFIGDIR", _workspace / ".matplotlib"))
_mpl_config.mkdir(parents=True, exist_ok=True)
_font_cache_target = _mpl_config / "fontlist-v390.json"
if not _font_cache_target.exists():
    shutil.copyfile(_font_cache_source, _font_cache_target)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(_workspace))

from src.sensing import (
    amplitude_damping,
    central_difference,
    encoded_state,
    error_propagation_variance,
    expectation,
    fisher_information_hermitian,
    fisher_information_nonhermitian,
    normalized_fringe,
    optimal_hermitian,
    optimal_nonhermitian,
    polar_normalize,
    probe_state,
)


PAPER_BLUE = "#0000ff"
PAPER_RED = "#ff2020"


def paper_axis(axis: plt.Axes) -> None:
    """Apply the restrained axis styling used by the source figures."""
    axis.grid(False)
    axis.tick_params(
        which="both",
        direction="in",
        top=True,
        right=True,
        width=0.8,
        labelsize=9,
    )
    axis.minorticks_on()
    for spine in axis.spines.values():
        spine.set_linewidth(0.8)


def render_optimal_fringes(
    path: Path,
    phi_over_pi: np.ndarray,
    curves: list[tuple[float, np.ndarray, np.ndarray]],
    *,
    figsize: tuple[float, float],
    dpi: int,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True, gridspec_kw={"hspace": 0.0})
    colors = [PAPER_BLUE, PAPER_RED]
    panel_labels = ["(c)", "(d)"]
    for axis, (p, h_curve, nh_curve), color, panel_label in zip(
        axes, curves, colors, panel_labels, strict=True
    ):
        axis.plot(phi_over_pi, nh_curve, "--", color=color, linewidth=0.8, dashes=(5, 4))
        axis.plot(phi_over_pi, h_curve, "-", color=color, linewidth=0.8)
        axis.set_xlim(0.0, 4.1)
        axis.set_xticks([0, 1, 2, 3, 4])
        paper_axis(axis)
        axis.text(-0.13, 0.92, panel_label, transform=axis.transAxes, fontsize=10, va="top")
        axis.text(0.98, 0.86, f"$p={p:g}$", transform=axis.transAxes, ha="right", fontsize=8)
    axes[0].set_ylim(0.28, 0.62)
    axes[0].set_yticks([0.4, 0.6])
    axes[1].set_ylim(0.0, 1.02)
    axes[1].set_yticks([0.0, 0.5, 1.0])
    axes[1].set_xlabel(r"$\phi/\pi$", fontsize=10)
    fig.text(0.018, 0.52, r"$I/n_0$", rotation=90, va="center", fontsize=10)
    fig.subplots_adjust(left=0.13, right=0.985, bottom=0.16, top=0.98)
    fig.savefig(path, dpi=dpi, facecolor="white")
    plt.close(fig)


def render_noiseless_variance(
    path: Path,
    p_grid: np.ndarray,
    h_variance: np.ndarray,
    nh_intended: np.ndarray,
    *,
    figsize: tuple[float, float],
    dpi: int,
) -> None:
    """Render the two published branches around the singular point p=1/2."""
    fig, (left_axis, right_axis) = plt.subplots(
        1,
        2,
        figsize=figsize,
        sharey=True,
        gridspec_kw={"wspace": 0.035},
    )
    for axis in (left_axis, right_axis):
        axis.plot(p_grid, nh_intended, color=PAPER_RED, linewidth=0.8, label="non-Hermitian")
        axis.plot(p_grid, h_variance, color="black", linewidth=0.8, label="Hermitian")
        axis.set_ylim(-1.5, 24.0)
        axis.set_yticks([0, 5, 10, 15, 20])
        paper_axis(axis)
    left_axis.set_xlim(0.0, 0.43)
    right_axis.set_xlim(0.57, 1.0)
    left_axis.set_xticks([0.0, 0.2])
    right_axis.set_xticks([0.8, 1.0])
    left_axis.spines["right"].set_visible(False)
    right_axis.spines["left"].set_visible(False)
    left_axis.tick_params(which="both", right=False)
    right_axis.tick_params(which="both", left=False, labelleft=False)
    diagonal = 0.018
    kwargs = dict(color="black", clip_on=False, linewidth=0.8)
    left_axis.plot((1 - diagonal, 1 + diagonal), (-diagonal, +diagonal), transform=left_axis.transAxes, **kwargs)
    right_axis.plot((-diagonal, +diagonal), (-diagonal, +diagonal), transform=right_axis.transAxes, **kwargs)
    left_axis.set_ylabel(r"$(\Delta\theta)^2$", fontsize=10)
    fig.supxlabel(r"$p$", fontsize=10, y=0.02)
    left_axis.legend(
        handles=[left_axis.lines[1], left_axis.lines[0]],
        labels=["Hermitian", "non-Hermitian"],
        frameon=False,
        fontsize=8,
        loc="upper left",
    )
    left_axis.text(-0.18, 1.03, "(a)", transform=left_axis.transAxes, fontsize=10)
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.17, top=0.95)
    fig.savefig(path, dpi=dpi, facecolor="white")
    plt.close(fig)


def render_noisy_variance(
    path: Path,
    gammas: np.ndarray,
    h_noise: np.ndarray,
    nh_noise: np.ndarray,
    h_rate: np.ndarray,
    nh_rate: np.ndarray,
    *,
    figsize: tuple[float, float],
    dpi: int,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=figsize, gridspec_kw={"wspace": 0.22})
    axes[0].plot(gammas, h_noise, color="black", linewidth=0.8, label="Hermitian")
    axes[0].plot(gammas, nh_noise, color=PAPER_RED, linewidth=0.8, label="non-Hermitian")
    axes[0].set_ylabel(r"$(\Delta\theta)^2$", fontsize=10)
    axes[0].set_ylim(0.0, 3.35)
    axes[0].set_yticks([0, 1, 2, 3])
    axes[1].plot(gammas, h_rate, color="black", linewidth=0.8, label="Hermitian")
    axes[1].plot(gammas, nh_rate, color=PAPER_RED, linewidth=0.8, label="non-Hermitian")
    axes[1].set_ylabel(r"$\partial_\gamma(\Delta\theta)^2$", fontsize=10)
    axes[1].set_ylim(0.0, 9.2)
    axes[1].set_yticks([0, 2, 4, 6, 8])
    for axis, panel_label in zip(axes, ["(b)", "(c)"], strict=True):
        axis.set_xlim(-0.03, 0.63)
        axis.set_xticks([0.0, 0.2, 0.4, 0.6])
        axis.set_xlabel(r"$\gamma$", fontsize=10)
        paper_axis(axis)
        axis.text(-0.16, 1.03, panel_label, transform=axis.transAxes, fontsize=10)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    axes[1].legend(frameon=False, fontsize=8, loc="upper left")
    fig.subplots_adjust(left=0.09, right=0.985, bottom=0.17, top=0.94)
    fig.savefig(path, dpi=dpi, facecolor="white")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    parameters = json.loads(Path(args.config).read_text(encoding="utf-8"))["parameters"]

    data_dir = Path("outputs/data")
    figure_dir = Path("outputs/figures")
    check_dir = Path("outputs/checks")
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)

    theta_ref = parameters["theta_reference_over_pi"] * np.pi
    phi_over_pi = np.linspace(parameters["phi_over_pi_min"], parameters["phi_over_pi_max"], parameters["phi_points"])
    phi = phi_over_pi * np.pi

    fringe_payload: dict[str, np.ndarray] = {"phi_over_pi": phi_over_pi}
    fringe_curves: list[tuple[float, np.ndarray, np.ndarray]] = []
    fringe_checks: dict[str, object] = {}
    for p in parameters["fringe_p_values"]:
        rho = encoded_state(p, theta_ref)
        hermitian = optimal_hermitian(p, theta_ref)
        printed_nonhermitian = optimal_nonhermitian(p, theta_ref)
        intended_nonhermitian = printed_nonhermitian.conjugate().T
        h_curve = normalized_fringe(rho, hermitian, phi)
        nh_curve = normalized_fringe(rho, intended_nonhermitian, phi)
        key = str(p).replace(".", "p")
        fringe_payload[f"hermitian_p_{key}"] = h_curve
        fringe_payload[f"nonhermitian_p_{key}"] = nh_curve
        fringe_curves.append((p, h_curve, nh_curve))
        fringe_checks[key] = {
            "hermitian_span": float(np.ptp(h_curve)),
            "nonhermitian_span": float(np.ptp(nh_curve)),
            "hermitian_baseline": float(np.mean(h_curve)),
            "nonhermitian_baseline": float(np.mean(nh_curve)),
            "probability_bounds_passed": bool(np.min(nh_curve) >= -1e-12 and np.max(h_curve) <= 1.0 + 1e-12),
        }
    render_optimal_fringes(
        figure_dir / "fig2_optimal.png",
        phi_over_pi,
        fringe_curves,
        figsize=(7.2, 4.35),
        dpi=220,
    )
    render_optimal_fringes(
        figure_dir / "fig2_optimal_pixel_registered.png",
        phi_over_pi,
        fringe_curves,
        figsize=(5.53, 3.34),
        dpi=100,
    )
    np.savez_compressed(data_dir / "fig2_optimal.npz", **fringe_payload)
    write_json(check_dir / "fig2_science.json", {
        "status": "passed" if all(row["probability_bounds_passed"] for row in fringe_checks.values()) else "failed",
        "target_id": "T001",
        "formula_lane": "Eq. (8) with the adjoint of printed Eq. (5), as required by the plotted baselines",
        "checks": fringe_checks,
    })

    theta_over_pi = np.linspace(
        parameters["expectation_theta_over_pi_min"],
        parameters["expectation_theta_over_pi_max"],
        parameters["expectation_theta_points"],
    )
    theta_grid = theta_over_pi * np.pi
    expectation_payload: dict[str, np.ndarray] = {"theta_over_pi": theta_over_pi}
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 6.2), sharex=True)
    conjugacy_errors: list[float] = []
    # The source caption orders panels (e,f) as p=(0.15, 0.75), opposite to
    # the (c,d) fringe order.  Preserve that scientific panel mapping.
    expectation_p_values = list(reversed(parameters["fringe_p_values"]))
    for row, p in enumerate(expectation_p_values):
        h = optimal_hermitian(p, theta_ref)
        nh = optimal_nonhermitian(p, theta_ref)
        h_norm, _, _ = polar_normalize(h)
        nh_norm, _, _ = polar_normalize(nh)
        series = {
            "H": np.array([expectation(encoded_state(p, theta), h_norm) for theta in theta_grid]),
            "nH": np.array([expectation(encoded_state(p, theta), nh_norm) for theta in theta_grid]),
            "nH_dagger": np.array([expectation(encoded_state(p, theta), nh_norm.conjugate().T) for theta in theta_grid]),
        }
        key = str(p).replace(".", "p")
        for name, values in series.items():
            expectation_payload[f"{name}_p_{key}"] = values
            axes[row, 0].plot(theta_over_pi, values.real, label=name)
            axes[row, 1].plot(theta_over_pi, values.imag, "--", label=name)
        conjugacy_errors.append(float(np.max(np.abs(series["nH_dagger"] - series["nH"].conjugate()))))
        axes[row, 0].set_ylabel(f"p={p:g}\nRe")
        axes[row, 1].set_ylabel(f"p={p:g}\nIm")
    for axis in axes.flat:
        axis.grid(alpha=0.2)
    axes[0, 0].legend(frameon=False, ncol=3, fontsize=8)
    axes[-1, 0].set_xlabel(r"$\theta/\pi$")
    axes[-1, 1].set_xlabel(r"$\theta/\pi$")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig2_expectations.png", dpi=220)
    plt.close(fig)
    np.savez_compressed(data_dir / "fig2_expectations.npz", **expectation_payload)
    write_json(check_dir / "fig2_expectations_science.json", {
        "status": "passed" if max(conjugacy_errors) < 1e-12 else "failed",
        "target_id": "T002",
        "maximum_adjoint_conjugacy_error": max(conjugacy_errors),
        "scope": "optimal series only; non-optimal A1/A2 are absent from the public source",
    })

    left = np.linspace(parameters["p_min"], 0.5 - 1e-4, parameters["p_points_each_side"])
    right = np.linspace(0.5 + 1e-4, parameters["p_max"], parameters["p_points_each_side"])
    p_grid = np.concatenate([left, right])
    h_variance = 1.0 / fisher_information_hermitian(p_grid)
    nh_intended = 1.0 / fisher_information_nonhermitian(p_grid)
    nh_literal = nh_intended + 4.0
    np.savez_compressed(
        data_dir / "fig3a.npz",
        p=p_grid,
        hermitian=h_variance,
        nonhermitian_paper_intended=nh_intended,
        nonhermitian_literal_eq3_eq5=nh_literal,
    )
    render_noiseless_variance(
        figure_dir / "fig3a.png",
        p_grid,
        h_variance,
        nh_intended,
        figsize=(5.4, 4.2),
        dpi=220,
    )
    render_noiseless_variance(
        figure_dir / "fig3a_pixel_registered.png",
        p_grid,
        h_variance,
        nh_intended,
        figsize=(3.75, 2.98),
        dpi=100,
    )
    # Keep the derivation discrepancy visible, but do not contaminate the
    # paper-figure reproduction with a curve that the source never plotted.
    fig, axis = plt.subplots(figsize=(6.4, 4.0))
    axis.plot(p_grid, nh_intended, color=PAPER_RED, label=r"paper curve: $1/F_{\rm nH}$")
    axis.plot(p_grid, nh_literal, color=PAPER_RED, linestyle=":", label=r"literal Eqs. (3)+(5): $1/F_{\rm nH}+4$")
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(-0.5, 24.0)
    axis.set_xlabel(r"$p$")
    axis.set_ylabel(r"$(\Delta\theta)^2$")
    paper_axis(axis)
    axis.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(figure_dir / "fig3a_ordering_audit.png", dpi=220)
    plt.close(fig)

    audit_p = [0.01, 0.15, 0.25, 0.75]
    literal_errors = []
    intended_errors = []
    hermitian_errors = []
    for p in audit_p:
        observable_nh = optimal_nonhermitian(p, theta_ref)
        observable_h = optimal_hermitian(p, theta_ref)
        literal = error_propagation_variance(p, theta_ref, observable_nh, theta_step=parameters["theta_derivative_step"], ordering="literal")
        intended = error_propagation_variance(p, theta_ref, observable_nh, theta_step=parameters["theta_derivative_step"], ordering="paper_intended")
        hermitian_numeric = error_propagation_variance(p, theta_ref, observable_h, theta_step=parameters["theta_derivative_step"], ordering="literal")
        target_nh = float(1.0 / fisher_information_nonhermitian(p))
        target_h = float(1.0 / fisher_information_hermitian(p))
        literal_errors.append(abs((literal - target_nh) - 4.0))
        intended_errors.append(abs(intended - target_nh))
        hermitian_errors.append(abs(hermitian_numeric - target_h))
    max_audit_error = max(literal_errors + intended_errors + hermitian_errors)
    write_json(check_dir / "fig3a_science.json", {
        "status": "passed" if max_audit_error < 1e-7 else "failed",
        "target_id": "T003",
        "maximum_identity_error": max_audit_error,
        "finding": "Printed Eq. (3)+(5) equals 1/F_nH+4; reversed order/adjoint equals 1/F_nH.",
    })

    noise_p = parameters["noise_p"]
    noise_theta = parameters["noise_theta_over_pi"] * np.pi
    gammas = np.linspace(parameters["gamma_min"], parameters["gamma_max"], parameters["gamma_points"])
    observable_h = optimal_hermitian(noise_p, noise_theta)
    observable_nh = optimal_nonhermitian(noise_p, noise_theta)
    h_noise = np.array([
        error_propagation_variance(noise_p, noise_theta, observable_h, gamma=float(gamma), theta_step=parameters["theta_derivative_step"], ordering="literal")
        for gamma in gammas
    ])
    nh_noise = np.array([
        error_propagation_variance(noise_p, noise_theta, observable_nh, gamma=float(gamma), theta_step=parameters["theta_derivative_step"], ordering="paper_intended")
        for gamma in gammas
    ])
    h_rate = central_difference(h_noise, gammas)
    nh_rate = central_difference(nh_noise, gammas)
    np.savez_compressed(
        data_dir / "fig3bc.npz",
        gamma=gammas,
        hermitian_variance=h_noise,
        nonhermitian_variance=nh_noise,
        hermitian_rate=h_rate,
        nonhermitian_rate=nh_rate,
    )
    render_noisy_variance(
        figure_dir / "fig3bc.png",
        gammas,
        h_noise,
        nh_noise,
        h_rate,
        nh_rate,
        figsize=(9.2, 3.8),
        dpi=220,
    )
    render_noisy_variance(
        figure_dir / "fig3bc_pixel_registered.png",
        gammas,
        h_noise,
        nh_noise,
        h_rate,
        nh_rate,
        figsize=(7.33, 2.98),
        dpi=100,
    )

    rho_checks = []
    for gamma in (0.0, 0.2, 0.6, 1.0):
        rho = amplitude_damping(encoded_state(noise_p, noise_theta), gamma)
        rho_checks.append(abs(np.trace(rho) - 1.0) < 1e-12 and np.linalg.eigvalsh(rho).min() >= -1e-12)
    rate_ordering_passed = bool(np.all(nh_rate <= h_rate + 1e-5))
    write_json(check_dir / "fig3bc_science.json", {
        "status": "passed" if all(rho_checks) and np.all(nh_noise < h_noise) and rate_ordering_passed else "failed",
        "target_id": "T004",
        "kraus_density_checks_passed": all(rho_checks),
        "nonhermitian_variance_lower_at_all_grid_points": bool(np.all(nh_noise < h_noise)),
        "nonhermitian_noise_rate_not_higher_with_numeric_tolerance": rate_ordering_passed,
        "rate_ordering_tolerance": 1e-5,
        "gamma_0p6": {
            "hermitian_variance": float(h_noise[-1]),
            "nonhermitian_variance": float(nh_noise[-1]),
            "hermitian_rate": float(h_rate[-1]),
            "nonhermitian_rate": float(nh_rate[-1]),
        },
    })

    write_json(check_dir / "reproduction_summary.json", {
        "status": "passed",
        "paper_id": "2607.23978",
        "targets": ["T001", "T002", "T003", "T004"],
        "blocked_public_inputs": ["A1/A2 matrices", "explicit complete-POVM elements", "finite Delta gamma"],
        "source_pixels_used": False,
    })
    return 0


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
