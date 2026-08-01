#!/usr/bin/env python3
"""Independently reproduce main-text Fig. 2(d) from Eqs. (2), (10), and (11).

The finite OBC potential is evaluated directly as ``log|det(H_L-E)|/N`` by
sparse LU.  No author eigenvalue table, plotted curve, or source-figure pixel
is consumed.  The only source-release inputs retained as method parameters are
the paper's 101 x 101 energy grid, four 7 x 7 probe boxes, and documented
boundary-length range.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
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

from src.fig2_finite_size import (  # noqa: E402
    FIG2_GRID_SIZE,
    FIG2_GLOBAL_STRIDE,
    FIG2_IMAGINARY_WINDOW,
    FIG2_REAL_WINDOW,
    FIG2_REGION_NAMES,
    fig2_probe_groups,
    flatten_probe_groups,
)
from src.geometry_adaptive import (  # noqa: E402
    build_obc_hamiltonian,
    diamond_sites,
    full_spectrum,
    geometry_adaptive_potential,
    model_eq11,
    sparse_spectral_potential,
    sparse_spectral_potential_consensus,
    spectral_potential,
    square_sites,
)


SCALE_CONFIG = {
    "smoke": {
        "lengths": {"square": (9, 13, 17), "rhombus": (9, 13, 17)},
        "momentum_samples": 32,
        "tolerance": 2e-3,
        "workers": 4,
        "ordering_p95_tolerance": 5e-4,
        "ordering_max_tolerance": 5e-3,
    },
    "paper": {
        # Square follows the released L=10..120 range.  Rhombus uses odd L so
        # that |x|+|y| <= (L-1)/2 is an unambiguous integer cut; L=61 gives
        # exactly the N=1861 lattice used in formal Fig. 2(b, c).
        "lengths": {
            "square": (10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 50, 60, 80, 100, 120),
            "rhombus": (21, 25, 31, 41, 51, 61, 71, 81, 101, 121, 131, 141, 151),
        },
        "momentum_samples": 200,
        "tolerance": 1e-5,
        "workers": 8,
        "ordering_p95_tolerance": 5e-4,
        "ordering_max_tolerance": 5e-3,
    },
}

COLORS = {
    "red": "#e41a1c",
    "yellow": "#e6c700",
    "green": "#16a637",
    "cyan": "#00a9bd",
    "global_coarse": "#111111",
}


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "pragent-2407.01296-fig2d",
        }
    )


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _parallel_map(function: object, values: np.ndarray, workers: int) -> np.ndarray:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        result = list(pool.map(function, values.tolist()))
    return np.asarray(result, dtype=np.float64)


def _target_potential(
    basis: str,
    energies: np.ndarray,
    *,
    momentum_samples: int,
    tolerance: float,
    workers: int,
) -> np.ndarray:
    hoppings = model_eq11()

    def evaluate(energy: complex) -> float:
        return geometry_adaptive_potential(
            complex(energy),
            hoppings,
            basis=basis,
            momentum_samples=momentum_samples,
            tolerance=tolerance,
        ).potential

    return _parallel_map(evaluate, energies, workers)


def _sites(basis: str, length: int) -> tuple[tuple[int, int], ...]:
    if basis == "square":
        return square_sites(length)
    if length % 2 != 1:
        raise ValueError("rhombus boundary length must be odd")
    return diamond_sites((length - 1) // 2)


def _finite_potential(
    basis: str,
    length: int,
    energies: np.ndarray,
    *,
    audit_indices: np.ndarray,
    workers: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    sites = _sites(basis, length)
    hamiltonian = build_obc_hamiltonian(sites, model_eq11())

    def evaluate(energy: complex) -> float:
        return sparse_spectral_potential(hamiltonian, complex(energy))

    potential = _parallel_map(evaluate, energies, workers)

    def audit(energy: complex) -> float:
        consensus = sparse_spectral_potential_consensus(
            hamiltonian,
            complex(energy),
        )
        return consensus.ordering_spread

    with ThreadPoolExecutor(max_workers=workers) as pool:
        audited = list(pool.map(audit, energies[audit_indices].tolist()))
    spread = np.full(energies.size, np.nan, dtype=np.float64)
    spread[audit_indices] = np.asarray(audited, dtype=np.float64)
    return potential, spread, len(sites)


def _linear_metrics(inverse_length: np.ndarray, deviation: np.ndarray) -> dict[str, float]:
    coefficients = np.polyfit(inverse_length, deviation, 1)
    prediction = np.polyval(coefficients, inverse_length)
    total = float(np.sum((deviation - np.mean(deviation)) ** 2))
    residual = float(np.sum((deviation - prediction) ** 2))
    return {
        "slope": float(coefficients[0]),
        "intercept": float(coefficients[1]),
        "r_squared": 1.0 - residual / total if total > 0.0 else 1.0,
        "first_deviation": float(deviation[0]),
        "last_deviation": float(deviation[-1]),
        "last_over_first": float(deviation[-1] / deviation[0]),
    }


def compute(scale: str) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    config = SCALE_CONFIG[scale]
    groups = fig2_probe_groups()
    energies, slices = flatten_probe_groups(groups)
    audit_indices = np.unique(
        np.concatenate(
            [
                np.linspace(
                    selected.start or 0,
                    (selected.stop or 1) - 1,
                    5 if group.name in FIG2_REGION_NAMES else 9,
                    dtype=np.int64,
                )
                for group, selected in zip(groups, slices, strict=True)
            ]
        )
    )
    workers = int(config["workers"])
    started = time.perf_counter()
    samples: list[dict[str, object]] = []
    scaling: list[dict[str, object]] = []
    fits: dict[str, dict[str, dict[str, float]]] = {}
    determinant_crosscheck_error = 0.0
    geometry_runtimes: dict[str, float] = {}
    numerical_audit: dict[str, list[dict[str, object]]] = {}

    for basis in ("square", "rhombus"):
        geometry_started = time.perf_counter()
        target = _target_potential(
            basis,
            energies,
            momentum_samples=int(config["momentum_samples"]),
            tolerance=float(config["tolerance"]),
            workers=workers,
        )
        lengths = tuple(int(value) for value in config["lengths"][basis])
        numerical_audit[basis] = []
        reliable_prefix_open = True
        for length in lengths:
            finite, ordering_spread, site_count = _finite_potential(
                basis,
                length,
                energies,
                audit_indices=audit_indices,
                workers=workers,
            )
            audited_spread = ordering_spread[audit_indices]
            p95_spread = float(np.quantile(audited_spread, 0.95))
            maximum_spread = float(np.max(audited_spread))
            ordering_consistent = (
                p95_spread < float(config["ordering_p95_tolerance"])
                and maximum_spread < float(config["ordering_max_tolerance"])
            )
            numerically_reliable = reliable_prefix_open and ordering_consistent
            if not ordering_consistent:
                reliable_prefix_open = False
            numerical_audit[basis].append(
                {
                    "boundary_length": length,
                    "site_count": site_count,
                    "ordering_spread_median": float(np.median(audited_spread)),
                    "ordering_spread_p95": p95_spread,
                    "ordering_spread_maximum": maximum_spread,
                    "ordering_consistent": bool(ordering_consistent),
                    "in_reliable_prefix": bool(numerically_reliable),
                }
            )
            if length == lengths[0]:
                matrix = build_obc_hamiltonian(_sites(basis, length), model_eq11())
                eigenvalues = full_spectrum(matrix)
                for probe_index in (0, energies.size // 2, energies.size - 1):
                    determinant_crosscheck_error = max(
                        determinant_crosscheck_error,
                        abs(
                            finite[probe_index]
                            - spectral_potential(eigenvalues, complex(energies[probe_index]))
                        ),
                    )
            for group, selected in zip(groups, slices, strict=True):
                absolute = np.abs(finite[selected] - target[selected])
                scaling.append(
                    {
                        "basis": basis,
                        "region": group.name,
                        "boundary_length": length,
                        "inverse_length": 1.0 / length,
                        "site_count": site_count,
                        "mean_absolute_deviation": float(np.mean(absolute)),
                        "maximum_absolute_deviation": float(np.max(absolute)),
                        "numerically_reliable": bool(numerically_reliable),
                        "ordering_spread_p95": p95_spread,
                        "ordering_spread_maximum": maximum_spread,
                        "provenance": "independent_sparse_logdet_vs_equation_10",
                    }
                )
                for local_index, flat_index in enumerate(
                    range(selected.start or 0, selected.stop or 0)
                ):
                    samples.append(
                        {
                            "basis": basis,
                            "boundary_length": length,
                            "site_count": site_count,
                            "region": group.name,
                            "probe_index": local_index,
                            "real_energy": float(energies[flat_index].real),
                            "imaginary_energy": float(energies[flat_index].imag),
                            "finite_obc_potential": float(finite[flat_index]),
                            "geometry_adaptive_potential": float(target[flat_index]),
                            "absolute_deviation": float(absolute[local_index]),
                            "lu_ordering_spread": (
                                float(ordering_spread[flat_index])
                                if np.isfinite(ordering_spread[flat_index])
                                else ""
                            ),
                            "numerically_reliable": bool(numerically_reliable),
                        }
                    )
        geometry_runtimes[basis] = time.perf_counter() - geometry_started
        fits[basis] = {}
        for group in groups:
            selected_rows = [
                row
                for row in scaling
                if row["basis"] == basis and row["region"] == group.name
                and row["numerically_reliable"]
            ]
            selected_rows.sort(key=lambda row: int(row["boundary_length"]))
            fits[basis][group.name] = _linear_metrics(
                np.asarray([row["inverse_length"] for row in selected_rows], dtype=float),
                np.asarray(
                    [row["mean_absolute_deviation"] for row in selected_rows],
                    dtype=float,
                ),
            )

    paper_scale = scale == "paper"
    fit_values = [fit for basis in fits.values() for fit in basis.values()]
    reliable_lengths = {
        basis: [
            int(row["boundary_length"])
            for row in numerical_audit[basis]
            if row["in_reliable_prefix"]
        ]
        for basis in ("square", "rhombus")
    }
    unreliable_lengths = {
        basis: [
            int(row["boundary_length"])
            for row in numerical_audit[basis]
            if not row["in_reliable_prefix"]
        ]
        for basis in ("square", "rhombus")
    }
    acceptance = {
        "four_regions_have_exactly_49_points": all(
            group.energies.size == 49
            for group in groups
            if group.name in FIG2_REGION_NAMES
        ),
        "global_window_has_121_points": next(
            group.energies.size for group in groups if group.name == "global_coarse"
        )
        == 121,
        "paper_energy_window_and_grid_match": (
            FIG2_REAL_WINDOW == (-2.0, 4.0)
            and FIG2_IMAGINARY_WINDOW == (-3.0, 3.0)
            and FIG2_GRID_SIZE == 101
            and FIG2_GLOBAL_STRIDE == 10
        ),
        "all_potentials_are_finite": all(
            np.isfinite(float(row["finite_obc_potential"]))
            and np.isfinite(float(row["geometry_adaptive_potential"]))
            for row in samples
        ),
        "sparse_logdet_matches_direct_eigenspectrum": determinant_crosscheck_error < 1e-9,
        "every_verified_deviation_decreases_over_size_range": all(
            fit["last_deviation"] < fit["first_deviation"] for fit in fit_values
        ),
        "every_verified_finite_size_slope_is_positive": all(
            fit["slope"] > 0.0 for fit in fit_values
        ),
        "verified_linear_scaling_is_resolved": all(
            fit["r_squared"] > 0.98 for fit in fit_values
        ),
        "paper_scale_verified_intercepts_are_near_zero": (not paper_scale)
        or max(abs(fit["intercept"]) for fit in fit_values) < 0.002,
        "paper_scale_verified_final_errors_are_small": (not paper_scale)
        or max(fit["last_deviation"] for fit in fit_values) < 0.025,
        "paper_scale_reliable_prefix_is_large_enough": (not paper_scale)
        or (
            len(reliable_lengths["square"]) >= 10
            and len(reliable_lengths["rhombus"]) >= 7
            and max(reliable_lengths["square"]) >= 40
            and max(reliable_lengths["rhombus"]) >= 61
        ),
        "unstable_tail_is_retained_and_marked": (not paper_scale)
        or all(unreliable_lengths[basis] for basis in ("square", "rhombus")),
    }
    acceptance = {name: bool(value) for name, value in acceptance.items()}
    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T001",
        "figure_refs": ["Fig. 2(d)"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "artifact_stage": "final_reproduction" if paper_scale else "exploratory",
        "parameter_match": "paper_protocol" if paper_scale else "reduced_scale",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "author_eigenvalue_tables_consumed": False,
        "formula_refs": ["EQC001", "EQC002", "EQC003", "EQC006"],
        "method_ref": "METHOD008",
        "finite_potential_algorithm": "sparse_LU_log_abs_determinant_divided_by_site_count",
        "target_potential_algorithm": "Eq_10_geometry_adaptive_directional_minimum",
        "probe_protocol": {
            "energy_window": {
                "real": list(FIG2_REAL_WINDOW),
                "imaginary": list(FIG2_IMAGINARY_WINDOW),
            },
            "grid_size": FIG2_GRID_SIZE,
            "region_point_counts": {
                group.name: int(group.energies.size) for group in groups
            },
            "global_stride": FIG2_GLOBAL_STRIDE,
        },
        "lengths": {
            basis: list(config["lengths"][basis]) for basis in ("square", "rhombus")
        },
        "momentum_samples": int(config["momentum_samples"]),
        "minimizer_tolerance": float(config["tolerance"]),
        "workers": workers,
        "ordering_consensus_audit_probe_count": int(audit_indices.size),
        "lu_ordering_permutations": ["COLAMD", "MMD_AT_PLUS_A", "MMD_ATA"],
        "ordering_consensus_tolerances": {
            "p95": float(config["ordering_p95_tolerance"]),
            "maximum": float(config["ordering_max_tolerance"]),
        },
        "determinant_crosscheck_max_abs_error": determinant_crosscheck_error,
        "numerical_audit": numerical_audit,
        "reliable_length_prefix": reliable_lengths,
        "retained_unreliable_tail": unreliable_lengths,
        "fits": fits,
        "acceptance": acceptance,
        "geometry_runtime_seconds": geometry_runtimes,
        "runtime_seconds": time.perf_counter() - started,
    }
    return samples, scaling, check


def render(
    path: Path,
    scaling: list[dict[str, object]],
    check: dict[str, object],
) -> None:
    configure_matplotlib()
    figure, axes = plt.subplots(1, 2, figsize=(8.4, 3.35), constrained_layout=True)
    for axis, basis in zip(axes, ("square", "rhombus"), strict=True):
        for region in ("green", "global_coarse", "red", "cyan", "yellow"):
            rows = [
                row
                for row in scaling
                if row["basis"] == basis and row["region"] == region
            ]
            rows.sort(key=lambda row: float(row["inverse_length"]))
            reliable = [row for row in rows if row["numerically_reliable"]]
            unreliable = [row for row in rows if not row["numerically_reliable"]]
            x = np.asarray([row["inverse_length"] for row in reliable], dtype=float)
            y = np.asarray(
                [row["mean_absolute_deviation"] for row in reliable], dtype=float
            )
            fit = check["fits"][basis][region]
            line_x = np.linspace(0.0, float(x.max()) * 1.03, 160)
            axis.plot(
                line_x,
                float(fit["slope"]) * line_x + float(fit["intercept"]),
                color=COLORS[region],
                linewidth=0.85,
            )
            axis.scatter(
                x,
                y,
                color=COLORS[region],
                edgecolor="0.2",
                linewidth=0.2,
                s=11,
                zorder=3,
                label="full window" if region == "global_coarse" else region,
            )
            if unreliable:
                axis.scatter(
                    [row["inverse_length"] for row in unreliable],
                    [row["mean_absolute_deviation"] for row in unreliable],
                    marker="x",
                    color=COLORS[region],
                    linewidth=0.55,
                    s=12,
                    alpha=0.38,
                    zorder=2,
                )
        axis.set_xlim(left=0.0)
        axis.set_ylim(bottom=0.0)
        axis.set_xlabel(r"$1/L$")
        axis.set_ylabel(r"mean $|\phi_L(E)-\Phi(E)|$")
        axis.set_title(f"{'(i)' if basis == 'square' else '(ii)'} {basis}", loc="left")
    axes[1].legend(frameon=False, fontsize=6.5, ncol=2, loc="upper left")
    figure.suptitle("Fig. 2(d): independent finite-OBC convergence")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=240)
    figure.savefig(path.with_suffix(".pdf"), metadata={"CreationDate": None, "ModDate": None})
    svg_path = path.with_suffix(".svg")
    figure.savefig(svg_path, metadata={"Date": None})
    plt.close(figure)
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", choices=tuple(SCALE_CONFIG), default="smoke")
    args = parser.parse_args()
    samples, scaling, check = compute(args.scale)
    suffix = "" if args.scale == "paper" else f"_{args.scale}"
    data_dir = OUTPUT_ROOT / "outputs" / "data"
    check_dir = OUTPUT_ROOT / "outputs" / "checks"
    figure_dir = OUTPUT_ROOT / "outputs" / "figures"
    write_rows(data_dir / f"fig2d_potential_samples{suffix}.csv", samples)
    write_rows(data_dir / f"fig2d_finite_size_independent{suffix}.csv", scaling)
    render(figure_dir / f"fig2d_finite_size_independent{suffix}.png", scaling, check)
    check_dir.mkdir(parents=True, exist_ok=True)
    (check_dir / f"fig2d_finite_size_independent{suffix}.json").write_text(
        json.dumps(check, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(check, indent=2, ensure_ascii=False))
    return 0 if check["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
