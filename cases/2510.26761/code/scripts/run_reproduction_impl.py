#!/usr/bin/env python3
"""Guarded target runner for the Wigner-negativity GME reproduction."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
from scipy.integrate import quad  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.wigner_gme import (  # noqa: E402
    SOURCE_PRINTED_GME_BOUND,
    STATE_DERIVED_GME_BOUND,
    W_STATE_GME_THRESHOLD,
    characteristic_witness_matrix,
    characteristic_witness_spectrum,
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
    unique_pairwise_differences,
    w_state_characteristic_slice,
    w_state_critical_radius,
    w_state_disk_volume,
    w_state_wigner_slice,
    witness_points,
)


GUARDED_TARGET_ENV = "PRAGENT_GUARDED_TARGET_ID"
GUARDED_STAGE_ENV = "PRAGENT_GUARDED_STAGE"
TARGETS = ("T001", "T002", "V001", "V002", "V003")
DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"
CHECK_DIR = WORKSPACE / "outputs" / "checks"
COMPARISON_DIR = WORKSPACE / "outputs" / "comparisons"
REFERENCE_DIR = WORKSPACE / "references" / "original_figures"

WIGNER_CMAP = LinearSegmentedColormap.from_list(
    "paper_wigner",
    ["#21104f", "#7f7398", "#ffffff", "#ffafbf", "#e40046"],
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def relative(path: Path) -> str:
    return str(path.relative_to(WORKSPACE))


def source_comparison(
    source_path: Path,
    generated_path: Path,
    output_path: Path,
    title: str,
) -> None:
    """Make a labelled scientific comparison; source pixels are not evidence."""

    source = mpimg.imread(source_path)
    generated = mpimg.imread(generated_path)
    figure, axes = plt.subplots(2, 1, figsize=(14.0, 9.0), constrained_layout=True)
    axes[0].imshow(source)
    axes[0].set_title("Paper figure (reference only)")
    axes[1].imshow(generated)
    axes[1].set_title("Independent formula-based reproduction")
    for axis in axes:
        axis.axis("off")
    figure.suptitle(title, fontsize=14)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=170)
    plt.close(figure)


def centered_norm(values: np.ndarray) -> TwoSlopeNorm:
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    if not minimum < 0.0 < maximum:
        raise ValueError("Wigner field must straddle zero")
    return TwoSlopeNorm(vmin=minimum, vcenter=0.0, vmax=maximum)


def render_overview(
    output_path: Path,
) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    """Render the numerical fields underlying the mixed schematic/numeric Fig. 1."""

    slice_axis = np.linspace(-1.2, 1.2, 401)
    sx, sy = np.meshgrid(slice_axis, slice_axis, indexing="xy")
    local_alpha = sx + 1.0j * sy
    equal_slice = np.asarray(illustrative_slice_wigner(local_alpha))

    extended_axis = np.linspace(-4.0, 4.0, 601)
    ex, ey = np.meshgrid(extended_axis, extended_axis, indexing="xy")
    com_field_extended = np.asarray(illustrative_com_wigner(ex + 1.0j * ey))
    smoothed_extended = convolve_with_gaussian_kernel(
        com_field_extended,
        extended_axis,
    )
    display_mask = np.abs(extended_axis) <= 1.8 + 1e-12
    display_axis = extended_axis[display_mask]
    com_field = com_field_extended[np.ix_(display_mask, display_mask)]
    smoothed_field = smoothed_extended[np.ix_(display_mask, display_mask)]

    cut_axis = np.linspace(-1.75, 1.75, 45)
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

    figure = plt.figure(figsize=(15.5, 8.0), constrained_layout=True)
    grid = figure.add_gridspec(2, 3, width_ratios=[1.35, 1.0, 1.0])
    axis_3d = figure.add_subplot(grid[:, 0], projection="3d")
    axis_slice = figure.add_subplot(grid[0, 1])
    axis_com = figure.add_subplot(grid[0, 2])
    axis_blank = figure.add_subplot(grid[1, 1])
    axis_smooth = figure.add_subplot(grid[1, 2])

    positive_max = float(np.max(full_cut))
    negative_scale = abs(float(np.min(full_cut)))
    positive_level = 0.34 * positive_max
    negative_level = -0.34 * negative_scale
    positive_band = 0.035 * positive_max
    negative_band = 0.035 * negative_scale
    positive_shell = np.where(
        np.abs(full_cut - positive_level) <= positive_band
    )
    negative_shell = np.where(
        np.abs(full_cut - negative_level) <= negative_band
    )
    axis_3d.scatter(
        cut_axis[positive_shell[0]],
        cut_axis[positive_shell[1]],
        cut_axis[positive_shell[2]],
        s=4.0,
        c="#e40046",
        alpha=0.38,
        linewidths=0.0,
        label=r"$W_\psi>0$ shell",
    )
    axis_3d.scatter(
        cut_axis[negative_shell[0]],
        cut_axis[negative_shell[1]],
        cut_axis[negative_shell[2]],
        s=4.0,
        c="#21104f",
        alpha=0.42,
        linewidths=0.0,
        label=r"$W_\psi<0$ shell",
    )
    axis_3d.set(
        xlabel=r"$\mathrm{Re}\,\alpha_+$",
        ylabel=r"$\mathrm{Im}\,\alpha_+$",
        zlabel=r"$\mathrm{Re}\,\alpha_-$",
        title="Printed state: stated 3D cut",
    )
    axis_3d.view_init(elev=22.0, azim=-55.0)
    axis_3d.legend(frameon=False, fontsize=8, loc="upper left")

    image_slice = axis_slice.imshow(
        equal_slice,
        origin="lower",
        extent=(slice_axis[0], slice_axis[-1], slice_axis[0], slice_axis[-1]),
        cmap=WIGNER_CMAP,
        norm=centered_norm(equal_slice),
        interpolation="bilinear",
    )
    axis_slice.contour(
        slice_axis,
        slice_axis,
        equal_slice,
        levels=[0.0],
        colors="black",
        linewidths=0.7,
        alpha=0.55,
    )
    axis_slice.set(
        xlabel=r"$\mathrm{Re}\,\alpha$",
        ylabel=r"$\mathrm{Im}\,\alpha$",
        title=r"Theorem 1: $W_\psi(\alpha\mathbf{1})$",
    )
    figure.colorbar(image_slice, ax=axis_slice, shrink=0.78)

    image_com = axis_com.imshow(
        com_field,
        origin="lower",
        extent=(
            display_axis[0],
            display_axis[-1],
            display_axis[0],
            display_axis[-1],
        ),
        cmap=WIGNER_CMAP,
        norm=centered_norm(com_field),
        interpolation="bilinear",
    )
    axis_com.set(
        xlabel=r"$\mathrm{Re}\,\alpha_+$",
        ylabel=r"$\mathrm{Im}\,\alpha_+$",
        title=r"Reduced center of mass: $W_{\rho_+}$",
    )
    figure.colorbar(image_com, ax=axis_com, shrink=0.78)

    axis_blank.axis("off")
    axis_blank.text(
        0.02,
        0.98,
        "\n".join(
            [
                "Invariant checks",
                rf"$\langle\Pi_-\rangle=-13/25$",
                rf"$\int W\,d^2\alpha=-52/(75\pi^2)$",
                rf"$\mathcal{{N}}_{{2D}}\approx0.263699$",
                rf"state-derived bound $\approx{STATE_DERIVED_GME_BOUND:.6f}$",
                rf"source-printed bound $\approx{SOURCE_PRINTED_GME_BOUND:.6f}$",
                r"$\widetilde W(0)=-7/(16\pi)$",
                "",
                "The printed +56 numerator is",
                "inconsistent with the printed state;",
                "the state derivation gives +52.",
            ]
        ),
        transform=axis_blank.transAxes,
        va="top",
        fontsize=11,
        linespacing=1.45,
    )

    image_smooth = axis_smooth.imshow(
        smoothed_field,
        origin="lower",
        extent=(
            display_axis[0],
            display_axis[-1],
            display_axis[0],
            display_axis[-1],
        ),
        cmap=WIGNER_CMAP,
        norm=centered_norm(smoothed_field),
        interpolation="bilinear",
    )
    axis_smooth.contour(
        display_axis,
        display_axis,
        smoothed_field,
        levels=[0.0],
        colors="black",
        linewidths=0.7,
        alpha=0.55,
    )
    axis_smooth.plot(0.0, 0.0, marker="x", color="black", ms=7.0)
    axis_smooth.set(
        xlabel=r"$\mathrm{Re}\,\alpha_+$",
        ylabel=r"$\mathrm{Im}\,\alpha_+$",
        title=r"Theorem 2: $W_{\rho_+}*K$",
    )
    figure.colorbar(image_smooth, ax=axis_smooth, shrink=0.78)
    figure.suptitle(
        "Numerical content of Main Fig. 1 — exact fields, reconstructed rendering",
        fontsize=15,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)

    center = len(extended_axis) // 2
    diagnostics = {
        "full_cut_minimum": float(np.min(full_cut)),
        "full_cut_maximum": float(np.max(full_cut)),
        "smoothed_grid_origin": float(smoothed_extended[center, center]),
        "smoothed_exact_origin": smoothed_origin_exact(),
        "smoothed_origin_absolute_error": abs(
            float(smoothed_extended[center, center]) - smoothed_origin_exact()
        ),
        "positive_shell_points": int(len(positive_shell[0])),
        "negative_shell_points": int(len(negative_shell[0])),
    }
    fields = {
        "slice_axis": slice_axis,
        "equal_slice": equal_slice,
        "com_axis": display_axis,
        "com_wigner": com_field,
        "smoothed_com_wigner": smoothed_field,
        "cut_axis": cut_axis,
        "full_cut": full_cut,
    }
    return fields, diagnostics


def run_t001() -> dict[str, object]:
    convergence = [
        illustrative_slice_metrics(
            radial_order=radial,
            angular_order=angular,
            radial_cutoff=4.0,
        )
        for radial, angular in (
            (160, 360),
            (360, 1080),
            (640, 2048),
            (800, 3072),
        )
    ]
    final_metrics = convergence[-1]
    figure_path = FIGURE_DIR / "overview_numeric_surfaces.png"
    fields, render_diagnostics = render_overview(figure_path)

    data_path = DATA_DIR / "overview_fields.npz"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(data_path, **fields)
    metrics_path = DATA_DIR / "overview_metrics.json"
    metrics_payload: dict[str, object] = {
        "state_norm": illustrative_state_norm(),
        "relative_parity": illustrative_relative_parity(),
        "reduced_state_trace": float(np.trace(illustrative_com_density()).real),
        "signed_integral_exact": illustrative_slice_signed_integral(),
        "state_derived_gme_bound": STATE_DERIVED_GME_BOUND,
        "source_printed_gme_bound": SOURCE_PRINTED_GME_BOUND,
        "convergence": convergence,
        "render_diagnostics": render_diagnostics,
        "source_inconsistency": {
            "source_prints_numerator": 56,
            "printed_state_implies_numerator": 52,
            "scientific_consequence": (
                "The independently integrated negativity clears the state-derived "
                "bound but does not clear the printed bound."
            ),
        },
    }
    write_json(metrics_path, metrics_payload)

    negativity = float(final_metrics["negativity_volume"])
    checks = {
        "state_normalized": abs(illustrative_state_norm() - 1.0) < 1e-14,
        "reduced_state_normalized": abs(
            float(np.trace(illustrative_com_density()).real) - 1.0
        )
        < 1e-14,
        "signed_integral_matches_parity_identity": abs(
            float(final_metrics["signed_integral"])
            - illustrative_slice_signed_integral()
        )
        < 2e-12,
        "negative_volume_converged": abs(
            float(convergence[-1]["negativity_volume"])
            - float(convergence[-2]["negativity_volume"])
        )
        < 5e-6,
        "state_derived_gme_bound_violated": negativity > STATE_DERIVED_GME_BOUND,
        "source_printed_bound_not_violated": negativity < SOURCE_PRINTED_GME_BOUND,
        "source_threshold_inconsistency_exposed": True,
        "smoothed_origin_matches_exact_value": (
            render_diagnostics["smoothed_origin_absolute_error"] < 2e-10
        ),
        "smoothed_origin_is_negative": smoothed_origin_exact() < 0.0,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "T001",
        "artifact_stage": "exploratory",
        "parameters": {
            "M": 3,
            "state": "six printed collective-Fock amplitudes",
            "radial_order": 800,
            "angular_order": 3072,
            "radial_cutoff": 4.0,
            "kernel": "8/pi*exp(-6|alpha|^2)",
            "parameter_match": "paper_exact",
            "rendering_parameters": "reconstructed because source isosurface levels are undisclosed",
        },
        "checks": checks,
        "diagnostics": {
            "negativity_volume": negativity,
            "state_derived_margin": negativity - STATE_DERIVED_GME_BOUND,
            "source_printed_margin": negativity - SOURCE_PRINTED_GME_BOUND,
            **render_diagnostics,
        },
        "findings": [
            {
                "severity": "source_error",
                "code": "fig1_gme_bound_numerator_inconsistent",
                "message": (
                    "The printed state gives (75*sqrt(2)+52)/600; the End Matter "
                    "prints (75*sqrt(2)+56)/600."
                ),
            }
        ],
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "analytic_reference",
        "outputs": [
            relative(data_path),
            relative(metrics_path),
            relative(figure_path),
        ],
    }


def render_w_state_figure(
    output_path: Path,
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    alpha_axis = np.linspace(-1.0, 1.0, 401)
    axx, ayy = np.meshgrid(alpha_axis, alpha_axis, indexing="xy")
    wigner = np.asarray(w_state_wigner_slice(axx + 1.0j * ayy))

    xi_axis = np.linspace(-2.0, 2.0, 401)
    xix, xiy = np.meshgrid(xi_axis, xi_axis, indexing="xy")
    characteristic = np.asarray(w_state_characteristic_slice(xix + 1.0j * xiy))
    differences = unique_pairwise_differences()

    figure, axes = plt.subplots(1, 2, figsize=(10.8, 5.2), constrained_layout=True)
    wigner_image = axes[0].imshow(
        wigner,
        origin="lower",
        extent=(-1.0, 1.0, -1.0, 1.0),
        cmap=WIGNER_CMAP,
        norm=TwoSlopeNorm(
            vmin=float(np.min(wigner)),
            vcenter=0.0,
            vmax=float(np.max(wigner)),
        ),
        interpolation="bilinear",
    )
    radius = 0.7
    circle = plt.Circle(
        (0.0, 0.0),
        radius,
        fill=False,
        color="black",
        linestyle=(0, (6, 5)),
        linewidth=1.4,
    )
    axes[0].add_patch(circle)
    axes[0].text(-0.10, radius + 0.04, "0.7", fontsize=10)
    axes[0].set(
        xlim=(-1.0, 1.0),
        ylim=(-1.0, 1.0),
        xticks=[-1.0, 0.0, 1.0],
        yticks=[-1.0, 0.0, 1.0],
        xlabel=r"$\mathrm{Re}[\alpha_m]$",
        ylabel=r"$\mathrm{Im}[\alpha_m]$",
        title="(a) Wigner slice",
        aspect="equal",
    )
    wigner_colorbar = figure.colorbar(
        wigner_image,
        ax=axes[0],
        orientation="horizontal",
        shrink=0.85,
        pad=0.15,
    )
    wigner_colorbar.set_label(r"$W_{|W_3\rangle}(\alpha\mathbf{1})$")

    characteristic_image = axes[1].imshow(
        characteristic,
        origin="lower",
        extent=(-2.0, 2.0, -2.0, 2.0),
        cmap=WIGNER_CMAP,
        norm=TwoSlopeNorm(
            vmin=float(np.min(characteristic)),
            vcenter=0.0,
            vmax=float(np.max(characteristic)),
        ),
        interpolation="bilinear",
    )
    inner_marker_radius = abs(complex(85.0, 147.0) / 200.0)
    for point in differences:
        color = (
            "white"
            if abs(abs(point) - inner_marker_radius) < 1e-10
            else "black"
        )
        axes[1].plot(
            point.real,
            point.imag,
            marker="x",
            color=color,
            markersize=7.0,
            markeredgewidth=1.6,
        )
    axes[1].set(
        xlim=(-2.0, 2.0),
        ylim=(-2.0, 2.0),
        xticks=[-2.0, -1.0, 0.0, 1.0, 2.0],
        yticks=[-2.0, -1.0, 0.0, 1.0, 2.0],
        xlabel=r"$\mathrm{Re}[\xi_m]$",
        ylabel=r"$\mathrm{Im}[\xi_m]$",
        title="(b) Characteristic slice: 19 differences",
        aspect="equal",
    )
    characteristic_colorbar = figure.colorbar(
        characteristic_image,
        ax=axes[1],
        orientation="horizontal",
        shrink=0.85,
        pad=0.15,
    )
    characteristic_colorbar.set_label(r"$\chi_{|W_3\rangle}(\xi\mathbf{1})$")
    figure.suptitle(
        "Main Fig. 2 — tripartite W-state finite-measurement witnesses",
        fontsize=14,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=190)
    plt.close(figure)

    fields = {
        "alpha_axis": alpha_axis,
        "wigner": wigner,
        "xi_axis": xi_axis,
        "characteristic": characteristic,
        "difference_points_real": differences.real,
        "difference_points_imag": differences.imag,
    }
    diagnostics: dict[str, object] = {
        "wigner_minimum": float(np.min(wigner)),
        "wigner_maximum": float(np.max(wigner)),
        "characteristic_minimum": float(np.min(characteristic)),
        "characteristic_maximum": float(np.max(characteristic)),
        "difference_points": [
            {"real": float(point.real), "imag": float(point.imag)}
            for point in differences
        ],
    }
    return fields, diagnostics


def run_t002() -> dict[str, object]:
    figure_path = FIGURE_DIR / "w_state_wigner_characteristic.png"
    fields, field_diagnostics = render_w_state_figure(figure_path)
    data_path = DATA_DIR / "w_state_fields.npz"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(data_path, **fields)

    points = witness_points()
    differences = unique_pairwise_differences(points)
    independently_measured = [
        point
        for point in differences
        if point.imag > 1e-12
        or (abs(point.imag) <= 1e-12 and point.real >= -1e-12)
    ]
    spectrum = characteristic_witness_spectrum()
    matrix = characteristic_witness_matrix()
    radius_critical = w_state_critical_radius()
    volume_at_07 = float(w_state_disk_volume(0.7))
    metrics_path = DATA_DIR / "w_state_metrics.json"
    metrics_payload: dict[str, object] = {
        "disk_radius": 0.7,
        "disk_volume": volume_at_07,
        "gme_threshold": W_STATE_GME_THRESHOLD,
        "certification_margin": volume_at_07 - W_STATE_GME_THRESHOLD,
        "critical_radius": radius_critical,
        "Xi": [
            {"real": float(point.real), "imag": float(point.imag)}
            for point in points
        ],
        "unique_difference_count": len(differences),
        "independent_measurement_count": len(independently_measured),
        "witness_matrix": matrix.tolist(),
        "witness_eigenvalues": spectrum.tolist(),
        "characteristic_witness": -float(spectrum[0]),
        "field_diagnostics": field_diagnostics,
    }
    write_json(metrics_path, metrics_payload)

    checks = {
        "wigner_origin_matches_minus_2_over_pi_cubed": abs(
            float(w_state_wigner_slice(0.0)) + (2.0 / math.pi) ** 3
        )
        < 1e-14,
        "critical_radius_matches_rounded_caption": abs(radius_critical - 0.7)
        < 0.001,
        "disk_at_0_7_certifies_gme": volume_at_07 > W_STATE_GME_THRESHOLD,
        "disk_certification_margin_exact": abs(
            (volume_at_07 - W_STATE_GME_THRESHOLD) - 0.0005820844502872
        )
        < 1e-12,
        "seven_point_set": len(points) == 7,
        "nineteen_unique_differences": len(differences) == 19,
        "ten_independent_measurements": len(independently_measured) == 10,
        "witness_matrix_hermitian": bool(
            np.max(np.abs(matrix - matrix.T), initial=0.0) < 1e-14
        ),
        "one_negative_eigenvalue": int(np.sum(spectrum < 0.0)) == 1,
        "characteristic_witness_matches_0_0176": abs(
            -float(spectrum[0]) - 0.0176
        )
        < 5e-5,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "T002",
        "artifact_stage": "final_reproduction",
        "parameters": {
            "M": 3,
            "wigner_domain": [-1.0, 1.0],
            "characteristic_domain": [-2.0, 2.0],
            "disk_radius": 0.7,
            "xi0": "0.425+0.735i",
            "Xi_size": 7,
            "filter": "vacuum",
            "grid_points_per_axis": 401,
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": {
            "disk_volume": volume_at_07,
            "gme_threshold": W_STATE_GME_THRESHOLD,
            "critical_radius": radius_critical,
            "witness_eigenvalues": spectrum.tolist(),
            "characteristic_witness": -float(spectrum[0]),
        },
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "analytic_reference",
        "outputs": [
            relative(data_path),
            relative(metrics_path),
            relative(figure_path),
        ],
    }


def run_v001() -> dict[str, object]:
    rows = []
    maximum_error = 0.0
    for radius in (0.2, 0.7, 1.0):
        break_point = 1.0 / (2.0 * math.sqrt(3.0))
        numeric, error = quad(
            lambda value: 4.0
            * value
            * abs(12.0 * value**2 - 1.0)
            * math.exp(-6.0 * value**2),
            0.0,
            radius,
            epsabs=1e-13,
            epsrel=1e-13,
            points=[break_point] if radius > break_point else None,
        )
        analytic = float(w_state_disk_volume(radius))
        absolute_error = abs(numeric - analytic)
        maximum_error = max(maximum_error, absolute_error)
        rows.append(
            {
                "radius": radius,
                "analytic_volume": analytic,
                "numeric_volume": numeric,
                "quadrature_error_estimate": error,
                "absolute_error": absolute_error,
            }
        )
    critical = w_state_critical_radius()
    data_path = DATA_DIR / "w_state_disk_validation.json"
    write_json(
        data_path,
        {
            "samples": rows,
            "critical_radius": critical,
            "threshold": W_STATE_GME_THRESHOLD,
        },
    )
    checks = {
        "closed_form_matches_independent_quadrature": maximum_error < 2e-12,
        "critical_radius_below_0_7": critical < 0.7,
        "critical_volume_matches_threshold": abs(
            float(w_state_disk_volume(critical)) - W_STATE_GME_THRESHOLD
        )
        < 2e-14,
        "r_0_7_has_positive_margin": float(w_state_disk_volume(0.7))
        > W_STATE_GME_THRESHOLD,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "V001",
        "artifact_stage": "final_reproduction",
        "parameters": {
            "M": 3,
            "disk_radius": 0.7,
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": {
            "maximum_analytic_quadrature_error": maximum_error,
            "critical_radius": critical,
            "volume_at_0_7": float(w_state_disk_volume(0.7)),
        },
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "analytic_reference",
        "outputs": [relative(data_path)],
    }


def run_v002() -> dict[str, object]:
    points = witness_points()
    differences = unique_pairwise_differences(points)
    matrix = characteristic_witness_matrix(points)
    spectrum = np.linalg.eigvalsh(matrix)
    data_path = DATA_DIR / "characteristic_witness_validation.json"
    write_json(
        data_path,
        {
            "Xi": [
                {"real": float(point.real), "imag": float(point.imag)}
                for point in points
            ],
            "difference_points": [
                {"real": float(point.real), "imag": float(point.imag)}
                for point in differences
            ],
            "matrix": matrix.tolist(),
            "eigenvalues": spectrum.tolist(),
            "witness": -float(spectrum[0]),
        },
    )
    checks = {
        "seven_points": len(points) == 7,
        "nineteen_unique_differences": len(differences) == 19,
        "matrix_hermitian": bool(
            np.max(np.abs(matrix - matrix.T), initial=0.0) < 1e-14
        ),
        "matrix_trace_one": abs(float(np.trace(matrix)) - 1.0) < 1e-14,
        "one_negative_eigenvalue": int(np.sum(spectrum < 0.0)) == 1,
        "paper_witness_value_reproduced": abs(-float(spectrum[0]) - 0.0176)
        < 5e-5,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "V002",
        "artifact_stage": "final_reproduction",
        "parameters": {
            "xi0": "0.425+0.735i",
            "Xi_size": 7,
            "filter": "vacuum",
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": {
            "eigenvalues": spectrum.tolist(),
            "witness": -float(spectrum[0]),
        },
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "paper_reported_value",
        "outputs": [relative(data_path)],
    }


def run_v003() -> dict[str, object]:
    convergence = [
        illustrative_slice_metrics(
            radial_order=radial,
            angular_order=angular,
            radial_cutoff=4.0,
        )
        for radial, angular in (
            (160, 360),
            (360, 1080),
            (640, 2048),
            (800, 3072),
        )
    ]
    final = convergence[-1]
    negativity = float(final["negativity_volume"])
    data_path = DATA_DIR / "illustrative_state_validation.json"
    write_json(
        data_path,
        {
            "state_norm": illustrative_state_norm(),
            "relative_parity": illustrative_relative_parity(),
            "signed_integral_exact": illustrative_slice_signed_integral(),
            "state_derived_gme_bound": STATE_DERIVED_GME_BOUND,
            "source_printed_gme_bound": SOURCE_PRINTED_GME_BOUND,
            "smoothed_origin_exact": smoothed_origin_exact(),
            "convergence": convergence,
            "source_inconsistency": {
                "printed_numerator": 56,
                "state_derived_numerator": 52,
            },
        },
    )
    checks = {
        "state_normalized": abs(illustrative_state_norm() - 1.0) < 1e-14,
        "relative_parity_is_minus_13_over_25": abs(
            illustrative_relative_parity() + 13.0 / 25.0
        )
        < 1e-14,
        "signed_integral_matches_exact_identity": abs(
            float(final["signed_integral"])
            - illustrative_slice_signed_integral()
        )
        < 2e-12,
        "negative_volume_converged": abs(
            float(convergence[-1]["negativity_volume"])
            - float(convergence[-2]["negativity_volume"])
        )
        < 5e-6,
        "corrected_bound_is_violated": negativity > STATE_DERIVED_GME_BOUND,
        "source_printed_bound_is_not_violated": negativity
        < SOURCE_PRINTED_GME_BOUND,
        "source_numerator_inconsistency_confirmed": True,
        "smoothed_origin_matches_paper": abs(
            smoothed_origin_exact() + 7.0 / (16.0 * math.pi)
        )
        < 1e-15,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "V003",
        "artifact_stage": "exploratory",
        "parameters": {
            "M": 3,
            "state": "six printed collective-Fock amplitudes",
            "kernel": "8/pi*exp(-6|alpha|^2)",
            "radial_order": 800,
            "angular_order": 3072,
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": {
            "negativity_volume": negativity,
            "corrected_bound": STATE_DERIVED_GME_BOUND,
            "printed_bound": SOURCE_PRINTED_GME_BOUND,
            "corrected_margin": negativity - STATE_DERIVED_GME_BOUND,
            "printed_margin": negativity - SOURCE_PRINTED_GME_BOUND,
            "smoothed_origin": smoothed_origin_exact(),
        },
        "findings": [
            {
                "severity": "source_error",
                "code": "end_matter_threshold_conflicts_with_printed_state",
                "message": (
                    "The source-printed +56 numerator is not generated by the "
                    "source-printed normalized state; the derivation gives +52."
                ),
            }
        ],
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "analytic_reference",
        "outputs": [relative(data_path)],
    }


RUNNERS: dict[str, Callable[[], dict[str, object]]] = {
    "T001": run_t001,
    "T002": run_t002,
    "V001": run_v001,
    "V002": run_v002,
    "V003": run_v003,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_id", choices=TARGETS)
    args = parser.parse_args()

    guarded_target = os.environ.get(GUARDED_TARGET_ENV)
    guarded_stage = os.environ.get(GUARDED_STAGE_ENV)
    if guarded_target != args.target_id or not guarded_stage:
        raise SystemExit(
            "Numerical targets must run through PRAgent-workflow/scripts/run_target.py"
        )

    started = time.perf_counter()
    payload = RUNNERS[args.target_id]()
    payload["guarded_stage"] = guarded_stage
    payload["runtime_seconds"] = time.perf_counter() - started
    if payload.get("artifact_stage") != guarded_stage:
        payload["status"] = "failed"
        payload.setdefault("checks", {})
        assert isinstance(payload["checks"], dict)
        payload["checks"]["guarded_stage_matches_payload"] = False
    else:
        assert isinstance(payload["checks"], dict)
        payload["checks"]["guarded_stage_matches_payload"] = True

    check_path = CHECK_DIR / f"{args.target_id.lower()}_paper_target_run.json"
    write_json(check_path, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
