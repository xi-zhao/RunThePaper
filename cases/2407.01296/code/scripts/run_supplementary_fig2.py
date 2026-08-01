#!/usr/bin/env python3
"""Independently reproduce every numerical panel of Supplementary Fig. S2.

All generated quantities come from Supplementary Eqs. (S17)-(S22): finite
open-boundary eigenvalues, the exact hierarchical potential, the Amoeba
potential, and characteristic-polynomial zero loci.  Released author arrays
and source-figure pixels are deliberately absent from this runner.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import csv
import json
from pathlib import Path
import sys
import time

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from scipy.spatial import cKDTree


CODE_ROOT = Path(__file__).resolve().parents[1]
# The public projection places this runner under ``code/scripts``. Numerical
# outputs then belong beside ``code``; in the master case they belong directly
# beside the scripts and source directories.
OUTPUT_ROOT = CODE_ROOT.parent if CODE_ROOT.name == "code" else CODE_ROOT
sys.path.insert(0, str(CODE_ROOT))

from src.geometry_adaptive import (  # noqa: E402
    spectral_density_from_potential,
    spectral_potential,
)
from src.supplementary_exact_model import (  # noqa: E402
    AmoebaRaster,
    amoeba_potential_grid,
    classify_amoeba_holes,
    exact_tdl_potential,
    separable_square_spectrum,
)


CONFIGS = {
    "smoke": {
        "length": 15,
        "real_points": 81,
        "imaginary_points": 25,
        "exact_quadrature": 64,
        "amoeba_momentum": 48,
        "amoeba_coarse": 25,
        "amoeba_refinement": 12,
        "hole_raster": 201,
        "hole_momentum": 512,
        "hole_tolerance": 0.06,
        "minimum_hole_cells": 4,
    },
    "paper": {
        "length": 75,
        "real_points": 241,
        "imaginary_points": 61,
        "exact_quadrature": 192,
        "amoeba_momentum": 128,
        "amoeba_coarse": 49,
        "amoeba_refinement": 22,
        "hole_raster": 281,
        "hole_momentum": 768,
        "hole_tolerance": 0.045,
        "minimum_hole_cells": 5,
    },
}
ENERGY_1 = 2.2 + 0.03j
ENERGY_2 = 6.0 - 0.3j


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=tuple(CONFIGS), default="paper")
    return parser.parse_args()


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "pragent-2407.01296",
        }
    )


def _hole_raster(energy: complex, config: dict[str, int | float]) -> AmoebaRaster:
    return classify_amoeba_holes(
        energy,
        raster_samples=int(config["hole_raster"]),
        momentum_samples=int(config["hole_momentum"]),
        zero_locus_tolerance=float(config["hole_tolerance"]),
        minimum_hole_cells=int(config["minimum_hole_cells"]),
    )


def compute(scale: str) -> dict[str, object]:
    config = CONFIGS[scale]
    started = time.perf_counter()
    real_axis = np.linspace(-5.0, 7.0, int(config["real_points"]))
    imaginary_axis = np.linspace(-0.4, 0.4, int(config["imaginary_points"]))
    grid_real, grid_imaginary = np.meshgrid(real_axis, imaginary_axis)
    energy_grid = grid_real + 1j * grid_imaginary
    real_step = float(real_axis[1] - real_axis[0])
    imaginary_step = float(imaginary_axis[1] - imaginary_axis[0])

    spectrum_result = separable_square_spectrum(int(config["length"]))
    exact_potential = exact_tdl_potential(
        energy_grid,
        quadrature_samples=int(config["exact_quadrature"]),
    )
    amoeba_result = amoeba_potential_grid(
        energy_grid,
        momentum_samples=int(config["amoeba_momentum"]),
        coarse_samples=int(config["amoeba_coarse"]),
        refinement_steps=int(config["amoeba_refinement"]),
    )
    exact_density = spectral_density_from_potential(
        exact_potential,
        real_step=real_step,
        imaginary_step=imaginary_step,
    )
    amoeba_density = spectral_density_from_potential(
        amoeba_result.potential,
        real_step=real_step,
        imaginary_step=imaginary_step,
    )
    first_amoeba = _hole_raster(ENERGY_1, config)
    second_amoeba = _hole_raster(ENERGY_2, config)

    convergence_probes = np.asarray(
        (-4.0 + 0.55j, -1.0 - 0.55j, 0.5 + 0.6j, 3.0 - 0.55j, 5.5 + 0.55j)
    )
    quadrature = int(config["exact_quadrature"])
    converged = exact_tdl_potential(
        convergence_probes,
        quadrature_samples=quadrature,
    )
    coarse = exact_tdl_potential(
        convergence_probes,
        quadrature_samples=max(16, quadrature // 2),
    )
    finite = np.asarray(
        [spectral_potential(spectrum_result.eigenvalues, value) for value in convergence_probes]
    )
    y_indices = np.arange(1, int(config["length"]) + 1, dtype=np.float64)
    analytic_y = np.sqrt(6.0) * np.cos(
        y_indices * np.pi / (int(config["length"]) + 1)
    )
    y_error = float(
        np.max(
            np.abs(
                np.sort(spectrum_result.y_eigenvalues.real) - np.sort(analytic_y)
            )
        )
    )

    positive_exact = np.clip(exact_density, 0.0, None)
    positive_amoeba = np.clip(amoeba_density, 0.0, None)
    exact_mass = float(np.sum(positive_exact) * real_step * imaginary_step)
    amoeba_mass = float(np.sum(positive_amoeba) * real_step * imaginary_step)
    potential_gap = amoeba_result.potential - exact_potential
    central_first = [hole for hole in first_amoeba.holes if hole.is_central]
    central_second = [hole for hole in second_amoeba.holes if hole.is_central]

    support_threshold = 0.03 * float(np.max(positive_exact))
    support_y, support_x = np.nonzero(positive_exact >= support_threshold)
    support_points = np.column_stack(
        (real_axis[support_x], imaginary_axis[support_y])
    )
    spectrum_points = np.column_stack(
        (spectrum_result.eigenvalues.real, spectrum_result.eigenvalues.imag)
    )
    support_distances = cKDTree(support_points).query(spectrum_points)[0]

    diagnostics = {
        "finite_square_length": int(config["length"]),
        "finite_square_site_count": int(spectrum_result.eigenvalues.size),
        "finite_spectrum_bounds": {
            "real_min": float(np.min(spectrum_result.eigenvalues.real)),
            "real_max": float(np.max(spectrum_result.eigenvalues.real)),
            "imaginary_min": float(np.min(spectrum_result.eigenvalues.imag)),
            "imaginary_max": float(np.max(spectrum_result.eigenvalues.imag)),
        },
        "y_gbz_analytic_max_error": y_error,
        "quadrature_probe_max_abs_change": float(np.max(np.abs(converged - coarse))),
        "finite_to_tdl_probe_max_abs_difference": float(
            np.max(np.abs(finite - converged))
        ),
        "amoeba_minus_exact_potential_minimum": float(np.min(potential_gap)),
        "amoeba_minus_exact_potential_median": float(np.median(potential_gap)),
        "amoeba_optimizer_boundary_hits": amoeba_result.boundary_hits,
        "exact_positive_density_mass_in_plot_window": exact_mass,
        "amoeba_positive_density_mass_in_plot_window": amoeba_mass,
        "finite_spectrum_to_exact_density_support_median_distance": float(
            np.median(support_distances)
        ),
        "finite_spectrum_to_exact_density_support_max_distance": float(
            np.max(support_distances)
        ),
        "energy_1_holes": [asdict(hole) | {"is_central": hole.is_central} for hole in first_amoeba.holes],
        "energy_2_holes": [asdict(hole) | {"is_central": hole.is_central} for hole in second_amoeba.holes],
    }
    acceptance = {
        "all_four_numeric_subfigures_generated": True,
        "finite_square_has_declared_number_of_states": (
            spectrum_result.eigenvalues.size == int(config["length"]) ** 2
        ),
        "analytic_y_gbz_identity_holds": y_error < 1e-9,
        "exact_potential_quadrature_converged": (
            diagnostics["quadrature_probe_max_abs_change"] < 0.01
        ),
        "finite_spectrum_converges_to_exact_tdl_potential": (
            diagnostics["finite_to_tdl_probe_max_abs_difference"] < 0.08
        ),
        "amoeba_potential_obeys_equation_s16": (
            diagnostics["amoeba_minus_exact_potential_minimum"] > -0.02
        ),
        "amoeba_optimizer_stays_inside_search_bounds": (
            amoeba_result.boundary_hits == 0
        ),
        "energy_1_has_only_noncentral_bounded_holes": (
            bool(first_amoeba.holes) and not central_first
        ),
        "energy_2_has_a_central_hole": bool(central_second),
        "densities_are_finite": bool(
            np.all(np.isfinite(exact_density))
            and np.all(np.isfinite(amoeba_density))
        ),
        "finite_spectrum_tracks_exact_density_support": (
            diagnostics["finite_spectrum_to_exact_density_support_median_distance"]
            < 0.15
        ),
    }
    status = "passed" if all(acceptance.values()) else "failed"
    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T007",
        "figure_refs": [
            "Supplementary Fig. S2(a)",
            "Supplementary Fig. S2(b)",
            "Supplementary Fig. S2(c)",
            "Supplementary Fig. S2(d)",
        ],
        "status": status,
        "artifact_stage": "scientific_reproduction",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "source_curves_used_as_generated_inputs": False,
        "formula_refs": ["EQC011", "EQC012", "EQC013"],
        "formula_interpretation": (
            "Eq. (S17) is separated as Eq. (S18); Eqs. (S19)-(S22) are "
            "evaluated by quartic roots and arcsine quadrature. Eq. (S15) is "
            "minimized independently after an exact Jensen reduction of the "
            "inner y integral. Amoeba holes are classified by integer torus winding."
        ),
        "scale": scale,
        "grid": {
            "real_min": float(real_axis[0]),
            "real_max": float(real_axis[-1]),
            "real_points": int(real_axis.size),
            "imaginary_min": float(imaginary_axis[0]),
            "imaginary_max": float(imaginary_axis[-1]),
            "imaginary_points": int(imaginary_axis.size),
        },
        "config": config,
        "diagnostics": diagnostics,
        "acceptance": acceptance,
        "runtime_seconds": time.perf_counter() - started,
    }
    return {
        "real_axis": real_axis,
        "imaginary_axis": imaginary_axis,
        "spectrum": spectrum_result.eigenvalues,
        "exact_potential": exact_potential,
        "exact_density": exact_density,
        "amoeba_potential": amoeba_result.potential,
        "amoeba_density": amoeba_density,
        "amoeba_deformation_x": amoeba_result.deformation_x,
        "amoeba_deformation_y": amoeba_result.deformation_y,
        "first_amoeba": first_amoeba,
        "second_amoeba": second_amoeba,
        "check": check,
    }


def write_spectrum(path: Path, spectrum: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("state_index", "real_energy", "imaginary_energy"))
        for index, value in enumerate(spectrum):
            writer.writerow((index, float(value.real), float(value.imag)))


def write_density_grid(path: Path, result: dict[str, object]) -> None:
    real_axis = np.asarray(result["real_axis"])
    imaginary_axis = np.asarray(result["imaginary_axis"])
    arrays = [
        np.asarray(result[name])
        for name in (
            "exact_potential",
            "exact_density",
            "amoeba_potential",
            "amoeba_density",
            "amoeba_deformation_x",
            "amoeba_deformation_y",
        )
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            (
                "real_energy",
                "imaginary_energy",
                "exact_potential",
                "exact_density",
                "amoeba_potential",
                "amoeba_density",
                "amoeba_deformation_x",
                "amoeba_deformation_y",
            )
        )
        for y_index, imaginary in enumerate(imaginary_axis):
            for x_index, real in enumerate(real_axis):
                writer.writerow(
                    (real, imaginary, *(array[y_index, x_index] for array in arrays))
                )


def _density_vmax(density: np.ndarray) -> float:
    positive = np.asarray(density)[np.asarray(density) > 0.0]
    return float(np.quantile(positive, 0.995)) if positive.size else 1.0


def _plot_amoeba_raster(
    axis: plt.Axes,
    raster: AmoebaRaster,
    *,
    title: str,
    panel_label: str | None,
) -> None:
    axis.pcolormesh(
        raster.deformation_x,
        raster.deformation_y,
        raster.zero_locus_mask,
        shading="auto",
        cmap=mpl.colors.ListedColormap(("white", "#858585")),
        vmin=0,
        vmax=1,
        rasterized=True,
    )
    for hole in raster.holes:
        marker = "o" if hole.is_central else "s"
        color = "#D55E00" if hole.is_central else "white"
        axis.scatter(
            hole.center_x,
            hole.center_y,
            s=18,
            marker=marker,
            facecolor=color,
            edgecolor="black",
            linewidth=0.45,
            zorder=4,
        )
        if hole.is_central:
            half_width = max(0.12, 1.5 * hole.clearance)
            axis.add_patch(
                Rectangle(
                    (hole.center_x - half_width, hole.center_y - half_width),
                    2.0 * half_width,
                    2.0 * half_width,
                    fill=False,
                    edgecolor="#D55E00",
                    linewidth=0.8,
                    zorder=3,
                )
            )
    axis.set_xlim(-1.5, 2.0)
    axis.set_ylim(-4.0, 3.0)
    axis.set_xlabel(r"$\mu_x$")
    if panel_label:
        axis.set_ylabel(r"$\mu_y$")
        axis.set_title(f"{panel_label} {title}", loc="left", fontsize=9)
    else:
        axis.set_yticklabels([])
        axis.set_title(title, loc="left", fontsize=9)


def render(path: Path, result: dict[str, object]) -> None:
    configure_matplotlib()
    real_axis = np.asarray(result["real_axis"])
    imaginary_axis = np.asarray(result["imaginary_axis"])
    spectrum = np.asarray(result["spectrum"])
    exact_density = np.clip(np.asarray(result["exact_density"]), 0.0, None)
    amoeba_density = np.clip(np.asarray(result["amoeba_density"]), 0.0, None)
    figure = plt.figure(figsize=(9.2, 6.4))
    grid = figure.add_gridspec(
        2,
        2,
        left=0.08,
        right=0.97,
        bottom=0.09,
        top=0.94,
        wspace=0.42,
        hspace=0.40,
    )
    axis_a = figure.add_subplot(grid[0, 0])
    axis_b = figure.add_subplot(grid[0, 1])
    axis_c = figure.add_subplot(grid[1, 0])
    d_grid = grid[1, 1].subgridspec(1, 2, wspace=0.04)
    axis_d1 = figure.add_subplot(d_grid[0, 0])
    axis_d2 = figure.add_subplot(d_grid[0, 1])

    axis_a.scatter(
        spectrum.real,
        spectrum.imag,
        s=1.2,
        color="#737373",
        alpha=0.48,
        linewidths=0,
        rasterized=True,
    )
    axis_a.set_title(
        f"(a) exact OBC, N={spectrum.size}", loc="left", fontsize=9
    )
    axis_a.set_xlabel(r"$\mathrm{Re}\,E$")
    axis_a.set_ylabel(r"$\mathrm{Im}\,E$")

    image_b = axis_b.pcolormesh(
        real_axis,
        imaginary_axis,
        exact_density,
        shading="auto",
        cmap="inferno",
        vmin=0.0,
        vmax=_density_vmax(exact_density),
        rasterized=True,
    )
    figure.colorbar(
        image_b,
        ax=axis_b,
        label=r"$\rho(E)$",
        shrink=0.78,
        fraction=0.046,
        pad=0.025,
    )
    axis_b.set_title("(b) Eqs. (S19)-(S22)", loc="left", fontsize=9)
    axis_b.set_xlabel(r"$\mathrm{Re}\,E$")
    axis_b.set_ylabel(r"$\mathrm{Im}\,E$")

    image_c = axis_c.pcolormesh(
        real_axis,
        imaginary_axis,
        amoeba_density,
        shading="auto",
        cmap="inferno",
        vmin=0.0,
        vmax=_density_vmax(amoeba_density),
        rasterized=True,
    )
    figure.colorbar(
        image_c,
        ax=axis_c,
        label=r"$\rho(E)$",
        shrink=0.78,
        fraction=0.046,
        pad=0.025,
    )
    for label_text, energy in (("1", ENERGY_1), ("2", ENERGY_2)):
        axis_c.scatter(
            energy.real,
            energy.imag,
            s=17,
            facecolor="white",
            edgecolor="#333333",
            linewidth=0.45,
            zorder=4,
        )
        axis_c.text(energy.real + 0.18, energy.imag + 0.025, label_text, fontsize=8)
    axis_c.set_title("(c) Amoeba potential, Eq. (S15)", loc="left", fontsize=9)
    axis_c.set_xlabel(r"$\mathrm{Re}\,E$")
    axis_c.set_ylabel(r"$\mathrm{Im}\,E$")

    _plot_amoeba_raster(
        axis_d1,
        result["first_amoeba"],
        title=r"$E_1=2.2+0.03i$",
        panel_label="(d)",
    )
    _plot_amoeba_raster(
        axis_d2,
        result["second_amoeba"],
        title=r"$E_2=6-0.3i$",
        panel_label=None,
    )

    for axis in (axis_a, axis_b, axis_c):
        axis.set_xlim(-5.0, 7.0)
        axis.set_ylim(-0.4, 0.4)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=240)
    figure.savefig(
        path.with_suffix(".pdf"),
        metadata={"CreationDate": None, "ModDate": None},
    )
    svg_path = path.with_suffix(".svg")
    figure.savefig(svg_path, metadata={"Date": None})
    plt.close(figure)
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    result = compute(args.scale)
    suffix = "" if args.scale == "paper" else f"_{args.scale}"
    data_dir = OUTPUT_ROOT / "outputs" / "data"
    figure_path = (
        OUTPUT_ROOT
        / "outputs"
        / "figures"
        / f"supp_fig_s2_reproduction{suffix}.png"
    )
    check_path = (
        OUTPUT_ROOT / "outputs" / "checks" / f"supp_fig_s2{suffix}.json"
    )
    write_spectrum(
        data_dir / f"supp_fig_s2_spectrum{suffix}.csv",
        np.asarray(result["spectrum"]),
    )
    write_density_grid(
        data_dir / f"supp_fig_s2_density{suffix}.csv",
        result,
    )
    np.savez_compressed(
        data_dir / f"supp_fig_s2_arrays{suffix}.npz",
        real_axis=result["real_axis"],
        imaginary_axis=result["imaginary_axis"],
        spectrum=result["spectrum"],
        exact_potential=result["exact_potential"],
        exact_density=result["exact_density"],
        amoeba_potential=result["amoeba_potential"],
        amoeba_density=result["amoeba_density"],
        amoeba_deformation_x=result["amoeba_deformation_x"],
        amoeba_deformation_y=result["amoeba_deformation_y"],
        energy_1_zero_locus_mask=result["first_amoeba"].zero_locus_mask,
        energy_2_zero_locus_mask=result["second_amoeba"].zero_locus_mask,
    )
    render(figure_path, result)
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(
        json.dumps(result["check"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["check"], indent=2, ensure_ascii=False))
    return 0 if result["check"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
