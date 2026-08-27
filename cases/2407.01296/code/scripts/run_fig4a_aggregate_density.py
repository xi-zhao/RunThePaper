#!/usr/bin/env python3
"""Reproduce formal Fig. 4(a) from the complete N=6385 right eigensystem."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


WORKSPACE = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(REPOSITORY / "agent" / "harness"))

from rr_harness.comparison_board import build_board, structural_similarity  # noqa: E402
from src.geometry_adaptive import (  # noqa: E402
    aggregate_right_density,
    build_obc_hamiltonian,
    density_metrics,
    diamond_sites,
    eigensystem_residuals,
    full_right_eigensystem,
    model_eq15,
    reflection_symmetrized_density,
    rhombus_localization_metrics,
)


FORMAL_CROP = (0, 0, 322, 239)
CANVAS_PIXELS = (
    FORMAL_CROP[2] - FORMAL_CROP[0],
    FORMAL_CROP[3] - FORMAL_CROP[1],
)
RENDER_DPI = 300
PAPER_RADIUS = 56
PAPER_SITE_COUNT = 6385


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-data", action="store_true")
    return parser.parse_args()


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.42,
            "savefig.facecolor": "white",
            "savefig.edgecolor": "white",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def compute() -> tuple[
    tuple[tuple[int, int], ...],
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
]:
    sites = diamond_sites(PAPER_RADIUS)
    if len(sites) != PAPER_SITE_COUNT:
        raise ValueError(
            f"radius {PAPER_RADIUS} produced {len(sites)} rather than {PAPER_SITE_COUNT} sites"
        )
    hamiltonian = build_obc_hamiltonian(sites, model_eq15())
    started = time.perf_counter()
    eigensystem = full_right_eigensystem(hamiltonian)
    raw_density = aggregate_right_density(eigensystem.right_eigenvectors)
    residuals = eigensystem_residuals(hamiltonian, eigensystem, batch_size=128)
    symmetrized_density = reflection_symmetrized_density(sites, raw_density)
    runtime = time.perf_counter() - started
    return (
        sites,
        eigensystem.eigenvalues,
        residuals,
        raw_density,
        symmetrized_density,
        runtime,
    )


def write_spectrum(path: Path, eigenvalues: np.ndarray, residuals: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("real_E", "imag_E", "normalized_residual"))
        writer.writerows(
            (value.real, value.imag, residual)
            for value, residual in zip(eigenvalues, residuals, strict=True)
        )


def write_density(
    path: Path,
    sites: tuple[tuple[int, int], ...],
    raw_density: np.ndarray,
    symmetrized_density: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw_maximum = float(raw_density.max())
    symmetric_maximum = float(symmetrized_density.max())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            (
                "x",
                "y",
                "raw_aggregate_density",
                "raw_density_over_max",
                "reflection_symmetrized_density",
                "symmetrized_density_over_max",
            )
        )
        for (x, y), raw, symmetric in zip(
            sites, raw_density, symmetrized_density, strict=True
        ):
            writer.writerow(
                (x, y, raw, raw / raw_maximum, symmetric, symmetric / symmetric_maximum)
            )


def read_spectrum(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.genfromtxt(path, delimiter=",", names=True)
    eigenvalues = np.asarray(data["real_E"] + 1j * data["imag_E"])
    return eigenvalues, np.asarray(data["normalized_residual"], dtype=float)


def read_density(
    path: Path,
) -> tuple[tuple[tuple[int, int], ...], np.ndarray, np.ndarray]:
    data = np.genfromtxt(path, delimiter=",", names=True)
    sites = tuple(
        (int(x), int(y))
        for x, y in zip(data["x"], data["y"], strict=True)
    )
    return (
        sites,
        np.asarray(data["raw_aggregate_density"], dtype=float),
        np.asarray(data["reflection_symmetrized_density"], dtype=float),
    )


def edge_orientation_metrics(
    sites: tuple[tuple[int, int], ...], density: np.ndarray
) -> dict[str, object]:
    coordinates = np.asarray(sites, dtype=int)
    u = coordinates[:, 0] + coordinates[:, 1]
    v = -coordinates[:, 0] + coordinates[:, 1]
    radius = int(max(np.max(np.abs(u)), np.max(np.abs(v))))
    normalized = np.asarray(density, dtype=float) / np.sum(density)
    masses = {
        "u_negative": float(normalized[u == -radius].sum()),
        "u_positive": float(normalized[u == radius].sum()),
        "v_negative": float(normalized[v == -radius].sum()),
        "v_positive": float(normalized[v == radius].sum()),
    }
    values = np.asarray(list(masses.values()))
    return {
        "exact_edge_masses": masses,
        "coefficient_of_variation": float(np.std(values) / np.mean(values)),
    }


def render(
    png_path: Path,
    pdf_path: Path,
    svg_path: Path,
    sites: tuple[tuple[int, int], ...],
    density: np.ndarray,
) -> None:
    configure_matplotlib()
    width, height = CANVAS_PIXELS
    figure = plt.figure(
        figsize=((width + 0.5) / RENDER_DPI, (height + 0.5) / RENDER_DPI),
        dpi=RENDER_DPI,
        facecolor="white",
    )
    radius = PAPER_RADIUS
    coordinates = np.asarray(sites, dtype=int)
    field = np.full((2 * radius + 1, 2 * radius + 1), np.nan, dtype=float)
    field[coordinates[:, 1] + radius, coordinates[:, 0] + radius] = density / density.max()
    colormap = mpl.colormaps["Reds"].copy()
    colormap.set_bad("white")
    axis = figure.add_axes((64 / width, (height - 211) / height, 199 / width, 199 / height))
    image = axis.imshow(
        np.ma.masked_invalid(field),
        origin="lower",
        extent=(-radius - 0.5, radius + 0.5, -radius - 0.5, radius + 0.5),
        cmap=colormap,
        vmin=0.0,
        vmax=1.0,
        interpolation="bilinear",
        rasterized=True,
    )
    outline_x = np.asarray((0, radius, 0, -radius, 0), dtype=float)
    outline_y = np.asarray((radius, 0, -radius, 0, radius), dtype=float)
    axis.plot(outline_x, outline_y, color="black", linewidth=0.26)
    axis.set_xlim(-radius - 2, radius + 2)
    axis.set_ylim(-radius - 2, radius + 2)
    axis.set_aspect("equal")
    axis.axis("off")

    color_axis = figure.add_axes((282 / width, (height - 207) / height, 16 / width, 165 / height))
    colorbar = figure.colorbar(image, cax=color_axis)
    colorbar.set_ticks([0.0, 1.0], labels=[r"$0$", r"$1$"])
    colorbar.ax.tick_params(labelsize=4.5, length=1.5, width=0.38, pad=1.0)
    colorbar.outline.set_linewidth(0.38)
    figure.text(275 / width, (height - 20) / height, r"$|\psi|^2$", fontsize=5.3)
    figure.text(3 / width, (height - 5) / height, "(a)", fontsize=5.2, ha="left", va="top")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(png_path, dpi=RENDER_DPI)
    figure.savefig(pdf_path)
    figure.savefig(svg_path)
    plt.close(figure)
    rendered = Image.open(png_path).convert("RGB")
    if rendered.size != CANVAS_PIXELS:
        if any(
            abs(actual - expected) > 1
            for actual, expected in zip(rendered.size, CANVAS_PIXELS, strict=True)
        ):
            raise ValueError(f"unexpected Matplotlib canvas {rendered.size}")
        exact = Image.new("RGB", CANVAS_PIXELS, "white")
        exact.paste(rendered, (0, 0))
        exact.save(png_path)


def write_reference_crop(source: Path, target: Path) -> np.ndarray:
    crop = Image.open(source).convert("RGB").crop(FORMAL_CROP)
    target.parent.mkdir(parents=True, exist_ok=True)
    crop.save(target)
    return np.asarray(crop)


def main() -> int:
    args = parse_args()
    data_dir = WORKSPACE / "outputs" / "data"
    figure_dir = WORKSPACE / "outputs" / "figures"
    check_dir = WORKSPACE / "outputs" / "checks"
    spectrum_path = data_dir / "fig4a_complete_spectrum_paper.csv"
    density_path = data_dir / "fig4a_aggregate_density_paper.csv"
    check_path = check_dir / "fig4a_aggregate_density.json"
    prior_check = (
        json.loads(check_path.read_text(encoding="utf-8"))
        if check_path.exists()
        else {}
    )
    if args.reuse_data:
        eigenvalues, residuals = read_spectrum(spectrum_path)
        sites, raw_density, symmetric_density = read_density(density_path)
        runtime = prior_check.get("runtime_seconds")
        refresh_started = time.perf_counter()
    else:
        (
            sites,
            eigenvalues,
            residuals,
            raw_density,
            symmetric_density,
            runtime,
        ) = compute()
        write_spectrum(spectrum_path, eigenvalues, residuals)
        write_density(density_path, sites, raw_density, symmetric_density)
        refresh_started = time.perf_counter()

    raw_localization = rhombus_localization_metrics(sites, raw_density)
    symmetric_localization = rhombus_localization_metrics(sites, symmetric_density)
    raw_orientation = edge_orientation_metrics(sites, raw_density)
    symmetric_orientation = edge_orientation_metrics(sites, symmetric_density)
    reference_path = WORKSPACE / "references" / "formal_figures" / "fig4_a.png"
    output_path = figure_dir / "fig4a_pixel_registered.png"
    pdf_path = figure_dir / "fig4a_aggregate_density.pdf"
    svg_path = figure_dir / "fig4a_aggregate_density.svg"
    comparison_path = WORKSPACE / "docs" / "comparisons" / "fig4a_pixel_comparison.png"
    reference = write_reference_crop(
        WORKSPACE / "references" / "formal_figures" / "fig4.png",
        reference_path,
    )
    render(output_path, pdf_path, svg_path, sites, symmetric_density)
    artifact_refresh_runtime = time.perf_counter() - refresh_started
    generated = np.asarray(Image.open(output_path).convert("RGB"))
    if generated.shape != reference.shape:
        raise ValueError(f"generated shape {generated.shape} != reference {reference.shape}")
    ssim = structural_similarity(reference, generated)
    rgb_mae = float(
        np.mean(np.abs(reference.astype(np.float64) - generated.astype(np.float64))) / 255.0
    )
    board = build_board(
        reference_path,
        output_path,
        comparison_path,
        left_title="Formal paper Fig. 4(a)",
        right_title="Independent complete eigensystem",
    )

    acceptance = {
        "paper_site_count_exact": len(sites) == PAPER_SITE_COUNT,
        "complete_spectrum_and_density": len(eigenvalues) == len(sites) == len(raw_density),
        "all_eigenpair_residuals_small": float(np.max(residuals)) < 1e-9,
        "boundary_density_is_enriched": symmetric_localization["boundary_enrichment"] > 1.5,
        "localization_is_edge_not_corner_dominated": symmetric_localization[
            "corner_fraction_of_boundary_mass"
        ]
        < symmetric_localization["corner_fraction_of_boundary_sites"],
        "reflection_symmetrization_is_exact": symmetric_orientation[
            "coefficient_of_variation"
        ]
        < 1e-12,
    }
    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T002",
        "figure_refs": ["Fig. 4(a)"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "pixel_status": "pixel_registered_not_identical",
        "artifact_stage": "scientific_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "model": "Eq. (15)",
        "geometry": "equal rhombus |x|+|y|<=56",
        "site_count": len(sites),
        "runtime_seconds": runtime,
        "artifact_refresh_seconds": artifact_refresh_runtime,
        "eigenpair_residuals": {
            "maximum": float(np.max(residuals)),
            "median": float(np.median(residuals)),
            "p95": float(np.quantile(residuals, 0.95)),
        },
        "raw_density": {
            "summary": density_metrics(sites, raw_density),
            "localization": raw_localization,
            "edge_orientation": raw_orientation,
        },
        "reflection_symmetrized_density": {
            "reason": (
                "Eq. (15) and the equal rhombus have exact x/y reflection symmetries; "
                "averaging removes near-degenerate solver-basis orientation without "
                "changing total probability or the boundary-versus-corner claim."
            ),
            "summary": density_metrics(sites, symmetric_density),
            "localization": symmetric_localization,
            "edge_orientation": symmetric_orientation,
        },
        "display_transfer": "global linear normalization density/max",
        "right_eigenvectors_persisted": False,
        "right_eigenvectors_persistence_reason": (
            "The complete vectors are approximately 650 MB; the reproducible script, "
            "spectrum, residuals, and both aggregate densities are retained instead."
        ),
        "acceptance": acceptance,
        "canvas_pixels": list(CANVAS_PIXELS),
        "dimensions_exact": generated.shape == reference.shape,
        "full_ssim": ssim,
        "rgb_mae": rgb_mae,
        "strict_pixel_exact_threshold": 0.95,
        "strict_pixel_exact": ssim >= 0.95,
        "data": {
            "complete_spectrum_and_residuals": str(spectrum_path.relative_to(WORKSPACE)),
            "raw_and_symmetrized_density": str(density_path.relative_to(WORKSPACE)),
        },
        "figure": str(output_path.relative_to(WORKSPACE)),
        "editable_exports": [
            str(pdf_path.relative_to(WORKSPACE)),
            str(svg_path.relative_to(WORKSPACE)),
        ],
        "comparison_board": str(comparison_path.relative_to(WORKSPACE)),
        "board_full_ssim": board["full_ssim"],
    }
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(check, indent=2))
    return 0 if check["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
