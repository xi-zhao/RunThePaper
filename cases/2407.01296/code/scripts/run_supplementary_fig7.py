#!/usr/bin/env python3
"""Independently reproduce Supplementary Fig. S7 from Eq. (S29).

The generated curves use fresh deterministic disorder samples and clean-system
biorthogonal perturbation theory.  Released author CSVs and paper pixels are
not read by this runner.
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
from pathlib import Path
import sys
import time

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


CODE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = CODE_ROOT.parent if CODE_ROOT.name == "code" else CODE_ROOT
sys.path.insert(0, str(CODE_ROOT))

from src.geometry_adaptive import (  # noqa: E402
    build_obc_hamiltonian,
    diamond_sites,
    model_eq11,
    model_eq15,
    square_sites,
)
from src.supplementary_models import (  # noqa: E402
    biorthogonal_diagonal_response,
    mean_absolute_first_order_shift,
)


CONFIGS = {
    "smoke": {
        "normal_lengths": (6, 8, 10),
        "critical_bounding_lengths": (9, 13, 17),
        "realizations": 12,
    },
    "paper": {
        "normal_lengths": (20, 30, 40),
        "critical_bounding_lengths": (29, 43, 57),
        "realizations": 100,
    },
}
DELTAS = np.linspace(0.01, 0.2, 20)
BASE_SEED = 240701296


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


def response_curve(
    *,
    geometry: str,
    linear_size: int,
    realizations: int,
    seed: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if geometry == "normal_square":
        sites = square_sites(linear_size)
        hoppings = model_eq11()
    elif geometry == "critical_rhombus":
        if linear_size % 2 != 1:
            raise ValueError("critical rhombus bounding length must be odd")
        sites = diamond_sites((linear_size - 1) // 2)
        hoppings = model_eq15()
    else:
        raise ValueError(f"unsupported geometry: {geometry}")

    started = time.perf_counter()
    hamiltonian = build_obc_hamiltonian(sites, hoppings)
    response = biorthogonal_diagonal_response(hamiltonian)
    unit_disorder = np.random.default_rng(seed).random((realizations, len(sites)))
    unit_slope = mean_absolute_first_order_shift(response, unit_disorder)
    rows = [
        {
            "geometry": geometry,
            "linear_size": linear_size,
            "site_count": len(sites),
            "delta": float(delta),
            "mean_absolute_energy_shift": float(delta * unit_slope),
            "response_per_delta": unit_slope,
            "realizations": realizations,
            "seed": seed,
        }
        for delta in DELTAS
    ]
    diagnostic = {
        "geometry": geometry,
        "linear_size": linear_size,
        "site_count": len(sites),
        "response_per_delta": unit_slope,
        "realizations": realizations,
        "seed": seed,
        "maximum_uniform_shift_error": response.maximum_uniform_shift_error,
        "minimum_left_right_overlap": response.minimum_left_right_overlap,
        "maximum_sampled_eigenpair_residual": (
            response.maximum_sampled_eigenpair_residual
        ),
        "runtime_seconds": time.perf_counter() - started,
    }
    del response, unit_disorder, hamiltonian
    gc.collect()
    return rows, diagnostic


def compute(
    scale: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    config = CONFIGS[scale]
    started = time.perf_counter()
    rows: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []

    for index, length in enumerate(config["normal_lengths"]):
        generated, diagnostic = response_curve(
            geometry="normal_square",
            linear_size=int(length),
            realizations=int(config["realizations"]),
            seed=BASE_SEED + 1000 + index,
        )
        rows.extend(generated)
        diagnostics.append(diagnostic)

    for index, length in enumerate(config["critical_bounding_lengths"]):
        generated, diagnostic = response_curve(
            geometry="critical_rhombus",
            linear_size=int(length),
            realizations=int(config["realizations"]),
            seed=BASE_SEED + 2000 + index,
        )
        rows.extend(generated)
        diagnostics.append(diagnostic)

    normal = [
        float(item["response_per_delta"])
        for item in diagnostics
        if item["geometry"] == "normal_square"
    ]
    critical = [
        float(item["response_per_delta"])
        for item in diagnostics
        if item["geometry"] == "critical_rhombus"
    ]
    linearity_errors = []
    for item in diagnostics:
        selected = [
            row
            for row in rows
            if row["geometry"] == item["geometry"]
            and row["linear_size"] == item["linear_size"]
        ]
        linearity_errors.extend(
            abs(
                float(row["mean_absolute_energy_shift"])
                / float(row["delta"])
                - float(item["response_per_delta"])
            )
            for row in selected
        )

    expected_normal_counts = (
        [400, 900, 1600]
        if scale == "paper"
        else [int(length) ** 2 for length in config["normal_lengths"]]
    )
    expected_critical_counts = (
        [421, 925, 1625]
        if scale == "paper"
        else [
            len(diamond_sites((int(length) - 1) // 2))
            for length in config["critical_bounding_lengths"]
        ]
    )
    actual_normal_counts = [
        int(item["site_count"])
        for item in diagnostics
        if item["geometry"] == "normal_square"
    ]
    actual_critical_counts = [
        int(item["site_count"])
        for item in diagnostics
        if item["geometry"] == "critical_rhombus"
    ]
    normal_cv = float(np.std(normal) / np.mean(normal))
    acceptance: dict[str, bool] = {
        "normal_site_counts_match_model_geometry": (
            actual_normal_counts == expected_normal_counts
        ),
        "critical_site_counts_match_model_geometry": (
            actual_critical_counts == expected_critical_counts
        ),
        "common_random_number_linearity_exact": max(linearity_errors) < 1e-12,
        "uniform_shift_identity_holds": max(
            float(item["maximum_uniform_shift_error"]) for item in diagnostics
        )
        < 1e-7,
        "sampled_eigenpairs_have_small_residual": max(
            float(item["maximum_sampled_eigenpair_residual"])
            for item in diagnostics
        )
        < 1e-10,
    }
    if scale == "paper":
        acceptance.update(
            {
                "normal_response_is_size_stable": normal_cv < 0.05,
                "critical_response_grows_with_size": bool(
                    np.all(np.diff(critical) > 0.0)
                ),
                "critical_large_system_is_over_100x_more_sensitive": (
                    critical[-1] > 100.0 * max(normal)
                ),
            }
        )
    else:
        acceptance["smoke_responses_are_finite_positive"] = bool(
            np.all(np.isfinite((*normal, *critical)))
            and min((*normal, *critical)) > 0.0
        )
    status = "passed" if all(acceptance.values()) else "failed"
    source_discrepancies: list[dict[str, object]] = []
    if scale == "paper" and actual_critical_counts[1] == 925:
        source_discrepancies.append(
            {
                "source_ref": "Supplementary Fig. S7 caption",
                "reported_site_count": 935,
                "model_geometry_site_count": 925,
                "author_runner_bounding_length": 43,
                "assessment": (
                    "The printed middle count is inconsistent with the exact "
                    "diamond lattice and the released r=43 runner; 925 is used."
                ),
            }
        )
        if status == "passed":
            status = "passed_with_source_discrepancy"

    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T006",
        "figure_refs": ["Supplementary Fig. S7(a)", "Supplementary Fig. S7(b)"],
        "status": status,
        "artifact_stage": "scientific_reproduction",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "source_curves_used_as_generated_inputs": False,
        "formula_refs": ["EQC010"],
        "formula_interpretation": (
            "Mean absolute biorthogonal first-order shift, matching the released "
            "operational implementation; fresh common random numbers are reused "
            "across delta because Eq. (S29) is exactly linear in disorder strength."
        ),
        "scale": scale,
        "deltas": DELTAS.tolist(),
        "diagnostics": diagnostics,
        "normal_response_coefficient_of_variation": normal_cv,
        "largest_critical_to_normal_response_ratio": critical[-1] / max(normal),
        "acceptance": acceptance,
        "source_discrepancies": source_discrepancies,
        "runtime_seconds": time.perf_counter() - started,
    }
    return rows, check


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def render(path: Path, rows: list[dict[str, object]], scale: str) -> None:
    configure_matplotlib()
    figure, axes = plt.subplots(1, 2, figsize=(7.4, 3.1), constrained_layout=True)
    settings = (
        (axes[0], "normal_square", "(a) Eq. (11), square", "#0072B2"),
        (axes[1], "critical_rhombus", "(b) Eq. (15), rhombus", "#D55E00"),
    )
    markers = ("o", "s", "^")
    for axis, geometry, title, color in settings:
        sizes = sorted(
            {
                (int(row["linear_size"]), int(row["site_count"]))
                for row in rows
                if row["geometry"] == geometry
            }
        )
        for marker, (linear_size, site_count) in zip(markers, sizes, strict=True):
            selected = [
                row
                for row in rows
                if row["geometry"] == geometry
                and int(row["linear_size"]) == linear_size
            ]
            axis.plot(
                [row["delta"] for row in selected],
                [row["mean_absolute_energy_shift"] for row in selected],
                marker=marker,
                markersize=3.0,
                linewidth=0.9,
                color=color,
                alpha=0.75 + 0.1 * sizes.index((linear_size, site_count)),
                label=f"N={site_count}",
            )
        axis.set_xlabel(r"disorder strength $\delta$")
        axis.set_ylabel(r"mean $|\Delta E|$")
        axis.set_title(title, loc="left", fontsize=9.5)
        axis.set_xlim(0.0, 0.205)
        axis.set_ylim(bottom=0.0)
        axis.legend(frameon=False, fontsize=7)
    if scale == "paper":
        axes[1].text(
            0.02,
            0.98,
            "caption says N=935; model gives 925",
            transform=axes[1].transAxes,
            ha="left",
            va="top",
            fontsize=6.5,
        )
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
    rows, check = compute(args.scale)
    suffix = "" if args.scale == "paper" else f"_{args.scale}"
    data_path = (
        OUTPUT_ROOT
        / "outputs"
        / "data"
        / f"supp_fig_s7_instability{suffix}.csv"
    )
    figure_path = (
        OUTPUT_ROOT
        / "outputs"
        / "figures"
        / f"supp_fig_s7_reproduction{suffix}.png"
    )
    check_path = (
        OUTPUT_ROOT / "outputs" / "checks" / f"supp_fig_s7{suffix}.json"
    )
    write_rows(data_path, rows)
    render(figure_path, rows, args.scale)
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(
        json.dumps(check, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(check, indent=2, ensure_ascii=False))
    return 0 if str(check["status"]).startswith("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
