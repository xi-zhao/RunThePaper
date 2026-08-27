#!/usr/bin/env python3
"""Reproduce formal Fig. 4(b) from target-state Gaussian finite-size scaling."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
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
    build_obc_hamiltonian,
    diamond_sites,
    fit_gaussian_profile,
    linear_fit_with_confidence,
    model_eq15,
    rhombus_edge_profile,
    target_right_eigenstate,
)


FORMAL_CROP = (322, 0, 660, 239)
CANVAS_PIXELS = (
    FORMAL_CROP[2] - FORMAL_CROP[0],
    FORMAL_CROP[3] - FORMAL_CROP[1],
)
RENDER_DPI = 300
TARGETS = {
    "lower": 1.3 + 0.4j,
    "main": 1.5 + 0.5j,
    "upper": 1.7 + 0.6j,
}
RADII = {
    "smoke": (20, 24, 28, 32, 36, 40),
    "paper": (40, 42, 45, 48, 52, 56, 60, 65, 70, 75, 80, 85, 90, 95, 100),
}
INSET_RADII = (40, 52, 65, 80, 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", choices=tuple(RADII), default="paper")
    parser.add_argument("--reuse-data", action="store_true")
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


def compute_campaign(
    scale: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], float]:
    scaling_rows: list[dict[str, object]] = []
    profile_rows: list[dict[str, object]] = []
    started = time.perf_counter()
    for track, target_energy in TARGETS.items():
        for radius in RADII[scale]:
            sites = diamond_sites(radius)
            hamiltonian = build_obc_hamiltonian(sites, model_eq15())
            state = target_right_eigenstate(hamiltonian, target_energy)
            coordinate, probability, boundary_length = rhombus_edge_profile(
                sites,
                state.right_eigenvector,
                edge="v_positive",
            )
            fit = fit_gaussian_profile(coordinate, probability)
            normalized_probability = probability / probability.max()
            fitted_probability = fit.evaluate(coordinate)
            scaling_rows.append(
                {
                    "track": track,
                    "target_real": target_energy.real,
                    "target_imag": target_energy.imag,
                    "radius": radius,
                    "site_count": len(sites),
                    "boundary_length": boundary_length,
                    "inverse_boundary_length": 1.0 / boundary_length,
                    "eigenvalue_real": state.eigenvalue.real,
                    "eigenvalue_imag": state.eigenvalue.imag,
                    "target_distance": abs(state.eigenvalue - target_energy),
                    "normalized_residual": state.normalized_residual,
                    "gaussian_amplitude": fit.amplitude,
                    "gaussian_center": fit.center,
                    "gaussian_sigma": fit.sigma,
                    "kappa": fit.kappa,
                    "gaussian_r_squared": fit.r_squared,
                    "fit_point_count": fit.point_count,
                }
            )
            if track == "main":
                for x, value, fitted in zip(
                    coordinate,
                    normalized_probability,
                    fitted_probability,
                    strict=True,
                ):
                    profile_rows.append(
                        {
                            "radius": radius,
                            "site_count": len(sites),
                            "edge_coordinate": x,
                            "x_over_L": (x - fit.center) / (2.0 * boundary_length),
                            "probability_over_max": value,
                            "gaussian_fit": fitted,
                        }
                    )
    return scaling_rows, profile_rows, time.perf_counter() - started


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    converted: list[dict[str, object]] = []
    for row in rows:
        converted.append(
            {
                key: value if key == "track" else float(value)
                for key, value in row.items()
            }
        )
    return converted


def regression_by_track(scaling_rows: list[dict[str, object]]) -> dict[str, object]:
    regressions: dict[str, object] = {}
    for track in TARGETS:
        rows = [row for row in scaling_rows if row["track"] == track]
        fit = linear_fit_with_confidence(
            np.asarray([row["inverse_boundary_length"] for row in rows], dtype=float),
            np.asarray([row["kappa"] for row in rows], dtype=float),
        )
        regressions[track] = fit
    return regressions


def render(
    png_path: Path,
    pdf_path: Path,
    svg_path: Path,
    scaling_rows: list[dict[str, object]],
    profile_rows: list[dict[str, object]],
    main_fit: object,
) -> None:
    configure_matplotlib()
    width, height = CANVAS_PIXELS
    figure = plt.figure(
        figsize=((width + 0.5) / RENDER_DPI, (height + 0.5) / RENDER_DPI),
        dpi=RENDER_DPI,
        facecolor="white",
    )
    axis = figure.add_axes((54 / width, (height - 224) / height, 279 / width, 208 / height))
    rows = [row for row in scaling_rows if row["track"] == "main"]
    inverse_length = np.asarray([row["inverse_boundary_length"] for row in rows], dtype=float)
    kappa = np.asarray([row["kappa"] for row in rows], dtype=float)
    axis.scatter(inverse_length, kappa, s=5.2, color="black", linewidths=0, zorder=3)
    line_x = np.linspace(0.0, 0.04, 200)
    axis.plot(
        line_x,
        main_fit.slope * line_x + main_fit.intercept,
        color="0.52",
        linewidth=1.05,
        zorder=2,
    )
    axis.set_xlim(0.0, 0.04)
    axis.set_ylim(0.0, 0.055)
    axis.set_xticks([0.0, 0.04], labels=[r"$0$", r"$0.04$"])
    axis.set_yticks([0.0, 0.05], labels=[r"$0$", r"$0.05$"])
    axis.set_xlabel(r"$1/L$", fontsize=5.1, labelpad=-2.0)
    axis.set_ylabel(r"$\kappa$", fontsize=5.3, labelpad=-3.0)
    axis.tick_params(labelsize=4.5, length=1.8, width=0.42, pad=1.5)
    for spine in axis.spines.values():
        spine.set_linewidth(0.42)

    inset = figure.add_axes((96 / width, (height - 136) / height, 153 / width, 84 / height))
    colors = ("#e6ab02", "#66a61e", "#1f77b4", "#7b3294", "#d73027")
    available_radii = sorted({int(float(row["radius"])) for row in profile_rows})
    chosen = [radius for radius in INSET_RADII if radius in available_radii]
    if not chosen:
        chosen = available_radii[:: max(1, len(available_radii) // 5)][:5]
    for color, radius in zip(colors, chosen, strict=False):
        selected = [row for row in profile_rows if int(float(row["radius"])) == radius]
        x = np.asarray([row["x_over_L"] for row in selected], dtype=float)
        probability = np.asarray([row["probability_over_max"] for row in selected], dtype=float)
        order = np.argsort(x)
        inset.plot(
            x[order],
            probability[order],
            color=color,
            linewidth=0.62,
            marker=".",
            markersize=1.35,
        )
    inset.set_xlim(-0.5, 0.5)
    inset.set_ylim(0.0, 1.02)
    inset.set_xticks([-0.5, 0.5], labels=[r"$-0.5$", r"$0.5$"])
    inset.set_yticks([0.0, 1.0], labels=[r"$0$", r"$1$"])
    inset.set_xlabel(r"$x/L$", fontsize=3.9, labelpad=-2.2)
    inset.set_ylabel(r"$|\psi|^2$", fontsize=4.0, labelpad=-2.5)
    inset.tick_params(labelsize=3.45, length=1.25, width=0.35, pad=0.8)
    for spine in inset.spines.values():
        spine.set_linewidth(0.35)

    figure.text(3 / width, (height - 5) / height, "(b)", fontsize=5.2, ha="left", va="top")
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
    scaling_path = data_dir / f"fig4b_scale_free_{args.scale}.csv"
    profile_path = data_dir / f"fig4b_edge_profiles_{args.scale}.csv"
    if args.reuse_data:
        scaling_rows = read_rows(scaling_path)
        profile_rows = read_rows(profile_path)
        runtime: float | None = None
    else:
        scaling_rows, profile_rows, runtime = compute_campaign(args.scale)
        write_rows(scaling_path, scaling_rows)
        write_rows(profile_path, profile_rows)

    regressions = regression_by_track(scaling_rows)
    main_fit = regressions["main"]
    reference_path = WORKSPACE / "references" / "formal_figures" / "fig4_b.png"
    output_path = figure_dir / "fig4b_pixel_registered.png"
    pdf_path = figure_dir / "fig4b_scale_free.pdf"
    svg_path = figure_dir / "fig4b_scale_free.svg"
    comparison_path = WORKSPACE / "docs" / "comparisons" / "fig4b_pixel_comparison.png"
    reference = write_reference_crop(
        WORKSPACE / "references" / "formal_figures" / "fig4.png",
        reference_path,
    )
    render(output_path, pdf_path, svg_path, scaling_rows, profile_rows, main_fit)
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
        left_title="Formal paper Fig. 4(b)",
        right_title="Independent Gaussian scaling",
    )

    main_rows = [row for row in scaling_rows if row["track"] == "main"]
    intercept_interval = main_fit.intercept_confidence_interval
    acceptance = {
        "paper_inverse_length_range_covered": args.scale != "paper"
        or min(float(row["inverse_boundary_length"]) for row in main_rows) <= 0.01,
        "all_shift_invert_residuals_small": max(
            float(row["normalized_residual"]) for row in scaling_rows
        )
        < 1e-9,
        "all_main_profiles_are_gaussian": min(
            float(row["gaussian_r_squared"]) for row in main_rows
        )
        > 0.95,
        "kappa_has_positive_inverse_length_slope": main_fit.slope > 0.0,
        "main_scaling_is_linear": main_fit.r_squared > 0.99,
        "thermodynamic_intercept_is_zero_compatible": intercept_interval[0]
        <= 0.0
        <= intercept_interval[1],
        "neighboring_energy_tracks_preserve_scaling": all(
            regressions[track].slope > 0.0
            and regressions[track].r_squared > 0.97
            and abs(regressions[track].intercept) < 0.003
            for track in ("lower", "upper")
        ),
    }
    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T002",
        "figure_refs": ["Fig. 4(b)"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "pixel_status": "pixel_registered_not_identical",
        "artifact_stage": "scientific_reproduction",
        "parameter_match": "paper_subset_unreported_state_sequence_reconstructed",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "model": "Eq. (15)",
        "geometry": "equal rhombus |x|+|y|<=L",
        "state_selection": {
            "main_target_energy": [TARGETS["main"].real, TARGETS["main"].imag],
            "rule": "right eigenstate closest to fixed target energy by deterministic shift-invert",
            "paper_state_sequence_reported": False,
            "sensitivity_targets": {
                track: [value.real, value.imag]
                for track, value in TARGETS.items()
                if track != "main"
            },
        },
        "gaussian_definition": "|psi(u)|^2=A exp[-kappa (u-u0)^2] on one v=+L edge",
        "scale": args.scale,
        "radii": list(RADII[args.scale]),
        "runtime_seconds": runtime,
        "track_regressions": {
            track: asdict(fit) for track, fit in regressions.items()
        },
        "profile_fit_r_squared": {
            "minimum": min(float(row["gaussian_r_squared"]) for row in main_rows),
            "median": float(
                np.median([float(row["gaussian_r_squared"]) for row in main_rows])
            ),
        },
        "maximum_normalized_eigen_residual": max(
            float(row["normalized_residual"]) for row in scaling_rows
        ),
        "acceptance": acceptance,
        "canvas_pixels": list(CANVAS_PIXELS),
        "dimensions_exact": generated.shape == reference.shape,
        "full_ssim": ssim,
        "rgb_mae": rgb_mae,
        "strict_pixel_exact_threshold": 0.95,
        "strict_pixel_exact": ssim >= 0.95,
        "data": {
            "scaling": str(scaling_path.relative_to(WORKSPACE)),
            "profiles": str(profile_path.relative_to(WORKSPACE)),
        },
        "figure": str(output_path.relative_to(WORKSPACE)),
        "editable_exports": [
            str(pdf_path.relative_to(WORKSPACE)),
            str(svg_path.relative_to(WORKSPACE)),
        ],
        "comparison_board": str(comparison_path.relative_to(WORKSPACE)),
        "board_full_ssim": board["full_ssim"],
    }
    check_path = check_dir / "fig4b_scale_free.json"
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(check, indent=2))
    return 0 if check["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
