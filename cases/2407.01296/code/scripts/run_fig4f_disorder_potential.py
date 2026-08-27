#!/usr/bin/env python3
"""Reproduce formal Fig. 4(f) with checkpointed sparse spectral potentials."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import time

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import sparse


WORKSPACE = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(REPOSITORY / "agent" / "harness"))

from rr_harness.comparison_board import build_board, structural_similarity  # noqa: E402
from src.geometry_adaptive import (  # noqa: E402
    amoeba_potential,
    build_obc_hamiltonian,
    diamond_sites,
    geometry_adaptive_potential,
    linear_fit_with_confidence,
    model_eq15,
    sparse_spectral_potential_grid,
)


FORMAL_CROP = (317, 493, 660, 770)
CANVAS_PIXELS = (
    FORMAL_CROP[2] - FORMAL_CROP[0],
    FORMAL_CROP[3] - FORMAL_CROP[1],
)
RENDER_DPI = 300
RADII = (30, 34, 38, 42, 46, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100)
DELTAS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
DISORDER_REALIZATIONS = 3
BASE_SEED = 20260720
PROBE_REAL = np.linspace(-0.16, 0.16, 5)
PROBE_IMAGINARY = np.linspace(-0.14, 0.18, 5)
PROBE_GRID = PROBE_REAL[None, :] + 1j * PROBE_IMAGINARY[:, None]
PROBE_COUNT = int(PROBE_GRID.size)
THEORY_MOMENTUM_SAMPLES = 128
AMOEBA_MOMENTUM_SAMPLES = 96
COLORS = {
    0.0: "#0072B2",
    0.05: "#E5A50A",
    0.10: "#69A832",
    0.15: "#B2183B",
    0.20: "#D45A16",
    0.25: "#7A3294",
    0.30: "#46B2D9",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reuse-data",
        action="store_true",
        help="Require a complete checkpoint and rebuild only summaries/figures.",
    )
    return parser.parse_args()


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.42,
            "xtick.major.width": 0.42,
            "ytick.major.width": 0.42,
            "savefig.facecolor": "white",
            "savefig.edgecolor": "white",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def theory_rows() -> tuple[list[dict[str, object]], float]:
    rows: list[dict[str, object]] = []
    started = time.perf_counter()
    for index, energy in enumerate(PROBE_GRID.reshape(-1)):
        geometry = geometry_adaptive_potential(
            complex(energy),
            model_eq15(),
            basis="rhombus",
            momentum_samples=THEORY_MOMENTUM_SAMPLES,
            tolerance=5e-5,
        )
        amoeba = amoeba_potential(
            complex(energy),
            model_eq15(),
            momentum_samples=AMOEBA_MOMENTUM_SAMPLES,
            tolerance=2e-4,
        )
        rows.append(
            {
                "probe_index": index,
                "real_E": energy.real,
                "imag_E": energy.imag,
                "geometry_potential": geometry.potential,
                "amoeba_potential": amoeba.potential,
                "amoeba_minus_geometry": amoeba.potential - geometry.potential,
                "amoeba_deformation_x": amoeba.deformation_x,
                "amoeba_deformation_y": amoeba.deformation_y,
                "amoeba_evaluations": amoeba.evaluations,
            }
        )
    return rows, time.perf_counter() - started


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_numeric_rows(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {key: float(value) for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def condition_key(delta: float, radius: int, realization: int) -> tuple[float, int, int]:
    return round(float(delta), 8), int(radius), int(realization)


def seed_for(delta: float, radius: int, realization: int) -> int:
    sequence = np.random.SeedSequence(
        [BASE_SEED, int(round(delta * 100)), radius, realization]
    )
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def append_condition(
    path: Path,
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        if not exists:
            writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())


def compute_or_resume(
    checkpoint_path: Path,
    theory: list[dict[str, float]],
    *,
    require_complete: bool,
) -> tuple[list[dict[str, float]], float, int]:
    existing = read_numeric_rows(checkpoint_path) if checkpoint_path.exists() else []
    counts: dict[tuple[float, int, int], int] = {}
    for row in existing:
        key = condition_key(row["delta"], int(row["radius"]), int(row["realization"]))
        counts[key] = counts.get(key, 0) + 1
    completed = {key for key, count in counts.items() if count == PROBE_COUNT}
    expected = {
        condition_key(delta, radius, realization)
        for delta in DELTAS
        for radius in RADII
        for realization in range(1 if delta == 0.0 else DISORDER_REALIZATIONS)
    }
    missing = expected - completed
    if require_complete and missing:
        raise RuntimeError(f"checkpoint is incomplete: {len(missing)} conditions missing")

    theory_by_probe = {int(row["probe_index"]): row for row in theory}
    started = time.perf_counter()
    newly_computed = 0
    total = len(expected)
    for delta in DELTAS:
        for radius in RADII:
            realization_count = 1 if delta == 0.0 else DISORDER_REALIZATIONS
            for realization in range(realization_count):
                key = condition_key(delta, radius, realization)
                if key in completed:
                    continue
                seed = seed_for(delta, radius, realization)
                sites = diamond_sites(radius)
                hamiltonian = build_obc_hamiltonian(sites, model_eq15())
                if delta > 0.0:
                    random = np.random.default_rng(seed)
                    onsite = random.uniform(0.0, delta, len(sites))
                    hamiltonian = hamiltonian + sparse.diags(
                        onsite.astype(np.complex128), format="csr"
                    )
                condition_started = time.perf_counter()
                finite = sparse_spectral_potential_grid(hamiltonian, PROBE_GRID)
                condition_rows: list[dict[str, object]] = []
                for probe_index, (energy, phi) in enumerate(
                    zip(PROBE_GRID.reshape(-1), finite.reshape(-1), strict=True)
                ):
                    reference = theory_by_probe[probe_index]
                    difference = abs(phi - reference["geometry_potential"])
                    condition_rows.append(
                        {
                            "delta": delta,
                            "radius": radius,
                            "site_count": len(sites),
                            "inverse_boundary_length": 1.0 / radius,
                            "realization": realization,
                            "seed": seed,
                            "probe_index": probe_index,
                            "real_E": energy.real,
                            "imag_E": energy.imag,
                            "finite_potential": phi,
                            "geometry_potential": reference["geometry_potential"],
                            "amoeba_potential": reference["amoeba_potential"],
                            "absolute_difference": difference,
                        }
                    )
                append_condition(checkpoint_path, condition_rows)
                existing.extend(
                    {
                        key: float(value)
                        for key, value in row.items()
                    }
                    for row in condition_rows
                )
                completed.add(key)
                newly_computed += 1
                print(
                    f"checkpoint {len(completed)}/{total}: delta={delta:.2f}, "
                    f"L={radius}, realization={realization}, "
                    f"seconds={time.perf_counter() - condition_started:.3f}",
                    flush=True,
                )
    return existing, time.perf_counter() - started, newly_computed


def summarize(
    rows: list[dict[str, float]],
) -> tuple[list[dict[str, object]], dict[float, object]]:
    realization_means: dict[tuple[float, int, int], list[float]] = {}
    site_counts: dict[tuple[float, int], int] = {}
    for row in rows:
        delta = round(row["delta"], 8)
        radius = int(row["radius"])
        realization = int(row["realization"])
        realization_means.setdefault((delta, radius, realization), []).append(
            row["absolute_difference"]
        )
        site_counts[(delta, radius)] = int(row["site_count"])
    reduced = {
        key: float(np.mean(values)) for key, values in realization_means.items()
    }
    summary: list[dict[str, object]] = []
    fits: dict[float, object] = {}
    for delta in DELTAS:
        for radius in RADII:
            values = np.asarray(
                [
                    mean
                    for (row_delta, row_radius, _), mean in reduced.items()
                    if np.isclose(row_delta, delta) and row_radius == radius
                ],
                dtype=float,
            )
            standard_deviation = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
            summary.append(
                {
                    "delta": delta,
                    "radius": radius,
                    "site_count": site_counts[(round(delta, 8), radius)],
                    "inverse_boundary_length": 1.0 / radius,
                    "mean_absolute_difference": float(np.mean(values)),
                    "realization_standard_deviation": standard_deviation,
                    "realization_standard_error": standard_deviation / np.sqrt(values.size),
                    "realization_count": int(values.size),
                    "probe_count_per_realization": PROBE_COUNT,
                }
            )
        selected = [row for row in summary if np.isclose(row["delta"], delta)]
        fits[delta] = linear_fit_with_confidence(
            np.asarray([row["inverse_boundary_length"] for row in selected], dtype=float),
            np.asarray([row["mean_absolute_difference"] for row in selected], dtype=float),
        )
    return summary, fits


def render(
    png_path: Path,
    pdf_path: Path,
    svg_path: Path,
    summary: list[dict[str, object]],
    fits: dict[float, object],
    amoeba_reference: float,
) -> None:
    configure_matplotlib()
    width, height = CANVAS_PIXELS
    figure = plt.figure(
        figsize=((width + 0.5) / RENDER_DPI, (height + 0.5) / RENDER_DPI),
        dpi=RENDER_DPI,
        facecolor="white",
    )
    axis = figure.add_axes((72 / width, (height - 228) / height, 250 / width, 210 / height))
    line_x = np.linspace(0.0, 0.06, 220)
    handles = []
    labels = []
    for delta in DELTAS:
        selected = [row for row in summary if np.isclose(row["delta"], delta)]
        x = np.asarray([row["inverse_boundary_length"] for row in selected], dtype=float)
        y = np.asarray([row["mean_absolute_difference"] for row in selected], dtype=float)
        color = COLORS[delta]
        axis.plot(
            line_x,
            fits[delta].slope * line_x + fits[delta].intercept,
            color=color,
            linewidth=0.75,
            zorder=1,
        )
        points = axis.scatter(x, y, s=4.0, color=color, linewidths=0, zorder=3)
        handles.append(points)
        labels.append(rf"$\delta$={delta:g}")
    amoeba = axis.scatter(
        [0.0],
        [amoeba_reference],
        s=18.0,
        color="#0B0BEF",
        linewidths=0,
        zorder=4,
    )
    handles.append(amoeba)
    labels.append("Amoeba")
    axis.set_xlim(0.0, 0.06)
    axis.set_ylim(0.0, 0.30)
    axis.set_xticks([0.0, 0.06], labels=[r"$0$", r"$0.06$"])
    axis.set_yticks([0.0, 0.30], labels=[r"$0$", r"$0.3$"])
    axis.set_xlabel(r"$1/L$", fontsize=5.0, labelpad=-2.0)
    axis.set_ylabel(r"$|\phi(E)-\Phi(E)|$", fontsize=5.0, labelpad=-2.8)
    axis.tick_params(labelsize=4.3, length=1.7, width=0.42, pad=1.4)
    axis.legend(
        handles,
        labels,
        ncol=2,
        frameon=False,
        fontsize=3.05,
        handletextpad=0.25,
        columnspacing=0.5,
        borderaxespad=0.0,
        loc="upper right",
        markerscale=0.75,
    )
    for spine in axis.spines.values():
        spine.set_linewidth(0.42)
    figure.text(3 / width, (height - 5) / height, "(f)", fontsize=5.2, ha="left", va="top")
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
    check_path = check_dir / "fig4f_disorder_potential.json"
    prior_check = (
        json.loads(check_path.read_text(encoding="utf-8"))
        if check_path.exists()
        else {}
    )
    theory_path = data_dir / "fig4f_theory_probe_potentials.csv"
    checkpoint_path = data_dir / "fig4f_probe_potentials_paper.csv"
    summary_path = data_dir / "fig4f_disorder_scaling_paper.csv"
    if theory_path.exists():
        theory = read_numeric_rows(theory_path)
        theory_runtime = prior_check.get("theory", {}).get("runtime_seconds")
    else:
        theory, theory_runtime = theory_rows()
        write_rows(theory_path, theory)
    rows, campaign_runtime, newly_computed = compute_or_resume(
        checkpoint_path,
        theory,
        require_complete=args.reuse_data,
    )
    artifact_refresh_runtime = campaign_runtime if newly_computed == 0 else 0.0
    recorded_campaign_runtime = (
        float(prior_check.get("campaign_runtime_seconds", campaign_runtime))
        if newly_computed == 0
        else campaign_runtime
    )
    summary, fits = summarize(rows)
    write_rows(summary_path, summary)

    amoeba_reference = float(
        np.mean([row["amoeba_minus_geometry"] for row in theory])
    )
    reference_path = WORKSPACE / "references" / "formal_figures" / "fig4_f.png"
    output_path = figure_dir / "fig4f_pixel_registered.png"
    pdf_path = figure_dir / "fig4f_disorder_potential.pdf"
    svg_path = figure_dir / "fig4f_disorder_potential.svg"
    comparison_path = WORKSPACE / "docs" / "comparisons" / "fig4f_pixel_comparison.png"
    reference = write_reference_crop(
        WORKSPACE / "references" / "formal_figures" / "fig4.png",
        reference_path,
    )
    render(output_path, pdf_path, svg_path, summary, fits, amoeba_reference)
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
        left_title="Formal paper Fig. 4(f)",
        right_title="Independent sparse-potential scaling",
    )

    nonzero_intercepts = np.asarray(
        [fits[delta].intercept for delta in DELTAS if delta > 0.0], dtype=float
    )
    clean_intercept = float(fits[0.0].intercept)
    acceptance = {
        "all_conditions_checkpointed": newly_computed >= 0
        and len(rows)
        == PROBE_COUNT
        * len(RADII)
        * (1 + (len(DELTAS) - 1) * DISORDER_REALIZATIONS),
        "paper_disorder_strengths_covered": sorted({float(row["delta"]) for row in summary})
        == list(DELTAS),
        "boxed_region_has_dozen_scale_probe_count": PROBE_COUNT >= 20,
        "amoeba_potential_dominates_geometry_potential": min(
            float(row["amoeba_minus_geometry"]) for row in theory
        )
        >= -2e-3,
        "nonzero_disorder_extrapolates_to_amoeba": float(
            np.max(np.abs(nonzero_intercepts - amoeba_reference))
        )
        < 0.045,
        "clean_and_disordered_limits_are_distinct": float(
            np.min(nonzero_intercepts) - clean_intercept
        )
        > 0.10,
        "all_finite_size_trends_are_linear": min(
            fit.r_squared for fit in fits.values()
        )
        > 0.94,
        "all_curves_grow_toward_TDL": all(fit.slope < 0.0 for fit in fits.values()),
    }
    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T002",
        "figure_refs": ["Fig. 4(f)"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "pixel_status": "pixel_registered_not_identical",
        "artifact_stage": "scientific_reproduction",
        "parameter_match": "paper_subset_unreported_box_grid_and_seeds_reconstructed",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "method": "exact sparse-LU log|det(H-E)|/N on each finite disordered rhombus",
        "model": "Eq. (15)",
        "geometry": "equal rhombus |x|+|y|<=L",
        "radii": list(RADII),
        "disorder_strengths": list(DELTAS),
        "disorder_distribution": "uniform_[0,delta] onsite disorder",
        "disorder_realizations": DISORDER_REALIZATIONS,
        "base_seed": BASE_SEED,
        "probe_box": {
            "real_axis": PROBE_REAL.tolist(),
            "imaginary_axis": PROBE_IMAGINARY.tolist(),
            "count": PROBE_COUNT,
            "paper_exact_grid_reported": False,
        },
        "theory": {
            "geometry_momentum_samples": THEORY_MOMENTUM_SAMPLES,
            "amoeba_momentum_samples": AMOEBA_MOMENTUM_SAMPLES,
            "mean_amoeba_minus_geometry": amoeba_reference,
            "minimum_pointwise_amoeba_minus_geometry": min(
                float(row["amoeba_minus_geometry"]) for row in theory
            ),
            "runtime_seconds": theory_runtime,
        },
        "campaign_runtime_seconds": recorded_campaign_runtime,
        "artifact_refresh_seconds": artifact_refresh_runtime,
        "new_conditions_computed": newly_computed,
        "regressions": {
            f"delta_{delta:g}": asdict(fits[delta]) for delta in DELTAS
        },
        "limit_comparison": {
            "clean_intercept": clean_intercept,
            "nonzero_intercepts": nonzero_intercepts.tolist(),
            "amoeba_reference": amoeba_reference,
        },
        "acceptance": acceptance,
        "canvas_pixels": list(CANVAS_PIXELS),
        "dimensions_exact": generated.shape == reference.shape,
        "full_ssim": ssim,
        "rgb_mae": rgb_mae,
        "strict_pixel_exact_threshold": 0.95,
        "strict_pixel_exact": ssim >= 0.95,
        "data": {
            "theory_probes": str(theory_path.relative_to(WORKSPACE)),
            "checkpointed_probe_potentials": str(checkpoint_path.relative_to(WORKSPACE)),
            "scaling_summary": str(summary_path.relative_to(WORKSPACE)),
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
