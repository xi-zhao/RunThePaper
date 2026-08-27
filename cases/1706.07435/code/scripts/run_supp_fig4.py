#!/usr/bin/env python3
"""Generate Supplement Figure 4 from the hybrid-point Hamiltonian."""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/pragent-1706-matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(WORKSPACE / "src"))

from nonhermitian_topology import (  # noqa: E402
    energy_difference_vorticity,
    hybrid_eigenvalues,
    hybrid_hamiltonian,
    tracked_hybrid_loop,
    unordered_pair_error,
)


TARGET_ID = "T006"
MASS = 1.0
DELTA = 1.0


def require_guard() -> None:
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID", "") != TARGET_ID:
        raise RuntimeError(
            "Run this target through PRAgent-workflow/scripts/run_target.py so the live formula gate is enforced."
        )


def write_cut_csv(
    path: Path,
    coordinate_name: str,
    coordinate: np.ndarray,
    plus: np.ndarray,
    minus: np.ndarray,
) -> None:
    fields = [coordinate_name, "e_plus_real", "e_plus_imag", "e_minus_real", "e_minus_imag"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index, value in enumerate(coordinate):
            writer.writerow(
                {
                    coordinate_name: f"{value:.17g}",
                    "e_plus_real": f"{plus[index].real:.17g}",
                    "e_plus_imag": f"{plus[index].imag:.17g}",
                    "e_minus_real": f"{minus[index].real:.17g}",
                    "e_minus_imag": f"{minus[index].imag:.17g}",
                }
            )


def scientific_checks(loop: dict[str, np.ndarray]) -> dict[str, object]:
    scale = np.logspace(-9, -4, 180)
    along_x, _ = hybrid_eigenvalues(scale, np.zeros_like(scale), mass=MASS, delta=DELTA)
    along_y, _ = hybrid_eigenvalues(np.zeros_like(scale), scale, mass=MASS, delta=DELTA)
    exponent_x = float(np.polyfit(np.log(scale), np.log(np.abs(along_x)), 1)[0])
    exponent_y = float(np.polyfit(np.log(scale), np.log(np.abs(along_y)), 1)[0])

    direct_errors = []
    for kx, ky in [(-1.1, -0.6), (-0.2, 0.8), (0.0, 0.0), (0.4, -0.7), (1.2, 0.3)]:
        plus, minus = hybrid_eigenvalues(kx, ky, mass=MASS, delta=DELTA)
        direct = np.linalg.eigvals(hybrid_hamiltonian(kx, ky, mass=MASS, delta=DELTA))
        direct_errors.append(unordered_pair_error([plus, minus], direct))

    origin = hybrid_hamiltonian(0.0, 0.0, mass=MASS, delta=DELTA)
    origin_rank = int(np.linalg.matrix_rank(origin))
    nilpotency_error = float(np.linalg.norm(origin @ origin))
    endpoint_return_error = float(abs(loop["e_plus"][-1] - loop["e_plus"][0]))
    vorticity = energy_difference_vorticity(2.0 * loop["e_plus"])

    metrics = {
        "max_analytic_vs_direct_eigenvalue_error": float(max(direct_errors)),
        "kx_direction_exponent": exponent_x,
        "ky_direction_exponent": exponent_y,
        "loop_endpoint_return_error": endpoint_return_error,
        "loop_vorticity": float(vorticity),
        "origin_matrix_rank": origin_rank,
        "origin_nilpotency_error": nilpotency_error,
    }
    criteria = {
        "analytic_vs_direct": metrics["max_analytic_vs_direct_eigenvalue_error"] < 1e-10,
        "square_root_along_kx": abs(exponent_x - 0.5) < 0.002,
        "linear_along_ky": abs(exponent_y - 1.0) < 1e-10,
        "no_sheet_exchange": endpoint_return_error < 1e-10,
        "zero_vorticity": abs(vorticity) < 1e-10,
        "defective_hybrid_point": origin_rank == 1 and nilpotency_error < 1e-12,
    }
    return {
        "schema_version": 1,
        "paper_id": "1706.07435",
        "target_id": TARGET_ID,
        "status": "passed" if all(criteria.values()) else "failed",
        "generated_data_provenance": "analytic_reference",
        "source_pixels_used_in_generation": False,
        "paper_parameters": {"mass": MASS, "delta": DELTA, "loop_radius": 1.0},
        "metrics": metrics,
        "criteria": criteria,
    }


def render_figure(
    path: Path,
    surface: dict[str, np.ndarray],
    loop: dict[str, np.ndarray],
    cut_x: dict[str, np.ndarray],
    cut_y: dict[str, np.ndarray],
) -> None:
    plt.rcParams.update({"font.size": 12, "axes.linewidth": 0.9})
    figure = plt.figure(figsize=(9.8, 7.3))
    grid = figure.add_gridspec(2, 2, width_ratios=(1.08, 1.0), wspace=0.04, hspace=0.16)

    kx = surface["kx"]
    ky = surface["ky"]
    plus = surface["e_plus"]
    for row, (component, label) in enumerate(((np.real, "Re(E)"), (np.imag, "Im(E)"))):
        axis = figure.add_subplot(grid[row, 0], projection="3d")
        z_plus = component(plus)
        z_minus = -z_plus
        axis.plot_surface(
            kx,
            ky,
            z_plus,
            rstride=4,
            cstride=4,
            color="#f27d45",
            alpha=0.88,
            linewidth=0.2,
            edgecolor="#8a4a31",
        )
        axis.plot_surface(
            kx,
            ky,
            z_minus,
            rstride=4,
            cstride=4,
            color="#f79a65",
            alpha=0.88,
            linewidth=0.2,
            edgecolor="#8a4a31",
        )
        axis.plot(
            loop["kx"],
            loop["ky"],
            component(loop["e_plus"]),
            color="#1f9de0",
            lw=2.0,
        )
        axis.set_xticks([])
        axis.set_yticks([])
        axis.set_zticks([])
        axis.set_xlabel(r"$k_x$", labelpad=-5)
        axis.set_ylabel(r"$k_y$", labelpad=-5)
        axis.set_zlabel(label, labelpad=-2)
        axis.view_init(elev=22, azim=-58)
        axis.set_box_aspect((1.0, 1.0, 0.68))

    colors = {"real": "#3896d3", "imag": "#d31332"}
    axis_x = figure.add_subplot(grid[0, 1])
    x = cut_x["coordinate"]
    for values, color in ((cut_x["plus"].real, colors["real"]), (cut_x["minus"].real, colors["real"]),
                          (cut_x["plus"].imag, colors["imag"]), (cut_x["minus"].imag, colors["imag"])):
        axis_x.plot(x, values, color=color, lw=2.1)
    axis_x.axhline(0.0, color="black", lw=0.8)
    axis_x.axvline(0.0, color="black", lw=0.8)
    axis_x.text(0.62, 0.80, "Re(E)", color=colors["real"], transform=axis_x.transAxes)
    axis_x.text(0.12, 0.66, "Im(E)", color=colors["imag"], transform=axis_x.transAxes)
    axis_x.set_xlabel(r"$k_x$", loc="right")
    axis_x.text(-0.03, 0.98, "E", transform=axis_x.transAxes, va="top")
    axis_x.set_xticks([])
    axis_x.set_yticks([])
    axis_x.spines[["left", "right", "top", "bottom"]].set_visible(False)

    axis_y = figure.add_subplot(grid[1, 1])
    y = cut_y["coordinate"]
    axis_y.plot(y, cut_y["plus"].real, color=colors["real"], lw=2.1)
    axis_y.plot(y, cut_y["minus"].real, color=colors["real"], lw=2.1)
    axis_y.plot(y, cut_y["plus"].imag, color=colors["imag"], lw=2.1)
    axis_y.plot(y, cut_y["minus"].imag, color=colors["imag"], lw=2.1)
    axis_y.axhline(0.0, color="black", lw=0.8)
    axis_y.axvline(0.0, color="black", lw=0.8)
    axis_y.set_xlabel(r"$k_y$", loc="right")
    axis_y.text(-0.03, 0.98, "E", transform=axis_y.transAxes, va="top")
    axis_y.set_xticks([])
    axis_y.set_yticks([])
    axis_y.spines[["left", "right", "top", "bottom"]].set_visible(False)

    figure.text(0.02, 0.965, "(a)", fontsize=17)
    figure.text(0.52, 0.965, "(b)", fontsize=17)
    figure.subplots_adjust(left=0.02, right=0.98, bottom=0.07, top=0.94)
    figure.savefig(path, dpi=200, facecolor="white")
    plt.close(figure)


def main() -> int:
    require_guard()
    started = time.perf_counter()
    data_dir = WORKSPACE / "outputs" / "data"
    figure_dir = WORKSPACE / "outputs" / "figures"
    check_dir = WORKSPACE / "outputs" / "checks"
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)

    coordinate = np.linspace(-1.5, 1.5, 161)
    kx, ky = np.meshgrid(coordinate, coordinate, indexing="xy")
    surface_plus, surface_minus = hybrid_eigenvalues(kx, ky, mass=MASS, delta=DELTA)
    surface = {"kx": kx, "ky": ky, "e_plus": surface_plus, "e_minus": surface_minus}

    cut_coordinate = np.linspace(-1.6, 1.6, 801)
    cut_x_plus, cut_x_minus = hybrid_eigenvalues(
        cut_coordinate, np.zeros_like(cut_coordinate), mass=MASS, delta=DELTA
    )
    cut_y_plus, cut_y_minus = hybrid_eigenvalues(
        np.zeros_like(cut_coordinate), cut_coordinate, mass=MASS, delta=DELTA
    )
    cut_x = {"coordinate": cut_coordinate, "plus": cut_x_plus, "minus": cut_x_minus}
    cut_y = {"coordinate": cut_coordinate, "plus": cut_y_plus, "minus": cut_y_minus}
    loop = tracked_hybrid_loop(
        np.linspace(0.0, 2.0 * np.pi, 721), radius=1.0, mass=MASS, delta=DELTA
    )

    surface_path = data_dir / "supp_fig4_hybrid_surface.npz"
    cut_x_path = data_dir / "supp_fig4_kx_cut.csv"
    cut_y_path = data_dir / "supp_fig4_ky_cut.csv"
    check_path = check_dir / "t006_scientific_checks.json"
    figure_path = figure_dir / "supp_fig4_reproduction.png"
    np.savez_compressed(surface_path, **surface)
    write_cut_csv(cut_x_path, "kx", cut_coordinate, cut_x_plus, cut_x_minus)
    write_cut_csv(cut_y_path, "ky", cut_coordinate, cut_y_plus, cut_y_minus)

    checks = scientific_checks(loop)
    checks["runtime_seconds"] = time.perf_counter() - started
    check_path.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if checks["status"] != "passed":
        print(json.dumps(checks, indent=2))
        return 1

    render_figure(figure_path, surface, loop, cut_x, cut_y)
    print(
        json.dumps(
            {
                "status": "passed",
                "target_id": TARGET_ID,
                "runtime_seconds": time.perf_counter() - started,
                "outputs": [
                    str(surface_path.relative_to(WORKSPACE)),
                    str(cut_x_path.relative_to(WORKSPACE)),
                    str(cut_y_path.relative_to(WORKSPACE)),
                    str(check_path.relative_to(WORKSPACE)),
                    str(figure_path.relative_to(WORKSPACE)),
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
