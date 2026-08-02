#!/usr/bin/env python3
"""Generate Main Figure 2 from the canonical exceptional-point Hamiltonian."""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
CASE = CODE.parent
os.environ.setdefault("MPLCONFIGDIR", str(CASE / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


sys.path.insert(0, str(CODE / "src"))

from nonhermitian_topology import (  # noqa: E402
    energy_difference_vorticity,
    exceptional_eigenvalues,
    exceptional_point_hamiltonian,
    hybrid_eigenvalues,
    tracked_exceptional_loop,
    unordered_pair_error,
)


TARGET_ID = "T002"


def write_loop_csv(path: Path, loop: dict[str, np.ndarray]) -> None:
    fields = [
        "theta",
        "kx",
        "ky",
        "radicand_real",
        "radicand_imag",
        "e_plus_real",
        "e_plus_imag",
        "e_minus_real",
        "e_minus_imag",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index in range(len(loop["theta"])):
            writer.writerow(
                {
                    "theta": f"{loop['theta'][index]:.17g}",
                    "kx": f"{loop['kx'][index]:.17g}",
                    "ky": f"{loop['ky'][index]:.17g}",
                    "radicand_real": f"{loop['radicand'][index].real:.17g}",
                    "radicand_imag": f"{loop['radicand'][index].imag:.17g}",
                    "e_plus_real": f"{loop['e_plus'][index].real:.17g}",
                    "e_plus_imag": f"{loop['e_plus'][index].imag:.17g}",
                    "e_minus_real": f"{loop['e_minus'][index].real:.17g}",
                    "e_minus_imag": f"{loop['e_minus'][index].imag:.17g}",
                }
            )


def write_cut_csv(path: Path, ky: np.ndarray, plus: np.ndarray, minus: np.ndarray) -> None:
    fields = ["ky", "e_plus_real", "e_plus_imag", "e_minus_real", "e_minus_imag"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index in range(ky.size):
            writer.writerow(
                {
                    "ky": f"{ky[index]:.17g}",
                    "e_plus_real": f"{plus[index].real:.17g}",
                    "e_plus_imag": f"{plus[index].imag:.17g}",
                    "e_minus_real": f"{minus[index].real:.17g}",
                    "e_minus_imag": f"{minus[index].imag:.17g}",
                }
            )


def scientific_checks(loop: dict[str, np.ndarray]) -> dict[str, object]:
    sample_indices = np.linspace(0, len(loop["theta"]) - 1, 37, dtype=int)
    direct_errors = []
    for index in sample_indices:
        direct = np.linalg.eigvals(
            exceptional_point_hamiltonian(float(loop["kx"][index]), float(loop["ky"][index]))
        )
        direct_errors.append(
            unordered_pair_error([loop["e_plus"][index], loop["e_minus"][index]], direct)
        )

    plus = loop["e_plus"]
    endpoint_swap_error = float(abs(plus[-1] + plus[0]))
    vorticity_ccw = energy_difference_vorticity(2.0 * plus)
    vorticity_cw = energy_difference_vorticity(2.0 * plus[::-1])

    origin = exceptional_point_hamiltonian(0.0, 0.0)
    rank = int(np.linalg.matrix_rank(origin))
    nilpotency_error = float(np.linalg.norm(origin @ origin))
    origin_eigenvalue_error = float(np.max(np.abs(np.linalg.eigvals(origin))))

    scale = np.logspace(-8, -3, 160)
    cut_plus, _ = exceptional_eigenvalues(np.zeros_like(scale), scale)
    square_root_exponent = float(np.polyfit(np.log(scale), np.log(np.abs(cut_plus)), 1)[0])

    hybrid_x, _ = hybrid_eigenvalues(scale, np.zeros_like(scale))
    hybrid_y, _ = hybrid_eigenvalues(np.zeros_like(scale), scale)
    hybrid_x_exponent = float(np.polyfit(np.log(scale), np.log(np.abs(hybrid_x)), 1)[0])
    hybrid_y_exponent = float(np.polyfit(np.log(scale), np.log(np.abs(hybrid_y)), 1)[0])

    metrics = {
        "max_analytic_vs_direct_eigenvalue_error": float(max(direct_errors)),
        "endpoint_branch_swap_error": endpoint_swap_error,
        "vorticity_counter_clockwise": vorticity_ccw,
        "vorticity_clockwise": vorticity_cw,
        "vorticity_magnitude": abs(vorticity_ccw),
        "origin_matrix_rank": rank,
        "origin_nilpotency_error": nilpotency_error,
        "origin_eigenvalue_error": origin_eigenvalue_error,
        "local_square_root_exponent": square_root_exponent,
        "hybrid_x_exponent_supporting_check": hybrid_x_exponent,
        "hybrid_y_exponent_supporting_check": hybrid_y_exponent,
    }
    criteria = {
        "analytic_vs_direct": metrics["max_analytic_vs_direct_eigenvalue_error"] < 1e-10,
        "branch_swap": endpoint_swap_error < 1e-10,
        "half_vorticity": abs(abs(vorticity_ccw) - 0.5) < 1e-10,
        "orientation_reversal": abs(vorticity_ccw + vorticity_cw) < 1e-10,
        "defective_rank": rank == 1,
        "nilpotent": nilpotency_error < 1e-12 and origin_eigenvalue_error < 1e-12,
        "square_root_scaling": abs(square_root_exponent - 0.5) < 0.01,
    }
    return {
        "schema_version": 1,
        "paper_id": "1706.07435",
        "target_id": TARGET_ID,
        "status": "passed" if all(criteria.values()) else "failed",
        "generated_data_provenance": "analytic_reference",
        "source_pixels_used_in_generation": False,
        "loop_orientation": "counter_clockwise",
        "metrics": metrics,
        "criteria": criteria,
    }


def render_figure(
    path: Path,
    loop: dict[str, np.ndarray],
    surface: dict[str, np.ndarray],
    cut: dict[str, np.ndarray],
) -> None:
    plt.rcParams.update({"font.size": 10, "axes.linewidth": 0.8})
    figure = plt.figure(figsize=(12.0, 7.6))
    grid = figure.add_gridspec(2, 3, width_ratios=(1.18, 1.0, 1.0), height_ratios=(1.0, 0.82))

    axis_a = figure.add_subplot(grid[:, 0], projection="3d")
    z = loop["theta"]
    axis_a.plot(loop["e_plus"].real, loop["e_plus"].imag, z, color="#3786c5", lw=2.4)
    axis_a.plot(loop["e_minus"].real, loop["e_minus"].imag, z, color="#f2b66f", lw=2.4)
    axis_a.plot(loop["e_plus"].real, loop["e_plus"].imag, np.zeros_like(z), "--", color="#3786c5", lw=1.3)
    axis_a.plot(loop["e_minus"].real, loop["e_minus"].imag, np.zeros_like(z), "--", color="#f2b66f", lw=1.3)
    axis_a.set_xlabel("Re(E)", labelpad=6)
    axis_a.set_ylabel("Im(E)", labelpad=6)
    axis_a.set_zlabel(r"$\theta$", labelpad=4)
    axis_a.set_zticks([0.0, np.pi, 2.0 * np.pi], ["0", r"$\pi$", r"$2\pi$"])
    axis_a.view_init(elev=18, azim=-72)
    axis_a.set_title("(a) sheet exchange on the unit loop", loc="left", pad=8)

    x = surface["kx"]
    y = surface["ky"]
    stride = 5
    axis_b_re = figure.add_subplot(grid[0, 1], projection="3d")
    axis_b_im = figure.add_subplot(grid[0, 2], projection="3d")
    for values, axis, title, component in [
        (surface["e_plus"], axis_b_re, "Re(E)", np.real),
        (surface["e_plus"], axis_b_im, "Im(E)", np.imag),
    ]:
        z_plus = component(values)
        z_minus = -z_plus
        axis.plot_surface(x, y, z_plus, rstride=stride, cstride=stride, cmap="Oranges", alpha=0.86, linewidth=0)
        axis.plot_surface(x, y, z_minus, rstride=stride, cstride=stride, cmap="Oranges", alpha=0.72, linewidth=0)
        loop_height = component(loop["e_plus"])
        axis.plot(loop["kx"], loop["ky"], loop_height, color="#1696d2", lw=1.8)
        axis.set_xlabel(r"$k_x$", labelpad=-2)
        axis.set_ylabel(r"$k_y$", labelpad=-2)
        axis.set_zlabel(title, labelpad=1)
        axis.view_init(elev=24, azim=-58)
        axis.tick_params(labelsize=7, pad=0)
    axis_b_re.set_title("(b) real sheet", loc="left", pad=6)
    axis_b_im.set_title("imaginary sheet", loc="left", pad=6)

    axis_c = figure.add_subplot(grid[1, 1:])
    ky = cut["ky"]
    axis_c.plot(ky, cut["e_plus"].real, color="#3786c5", lw=2.3, label=r"Re $E_+$")
    axis_c.plot(ky, cut["e_minus"].real, color="#3786c5", lw=2.3, label=r"Re $E_-$")
    axis_c.plot(ky, cut["e_plus"].imag, color="#cb1f3b", lw=2.3, label=r"Im $E_+$")
    axis_c.plot(ky, cut["e_minus"].imag, color="#cb1f3b", lw=2.3, label=r"Im $E_-$")
    axis_c.axhline(0.0, color="black", lw=0.7)
    axis_c.axvline(0.0, color="black", lw=0.7)
    axis_c.set_xlabel(r"$k_y$ at $k_x=0$")
    axis_c.set_ylabel("E")
    axis_c.set_title("(c) square-root dispersion cut", loc="left")
    axis_c.spines[["top", "right"]].set_visible(False)
    handles, labels = axis_c.get_legend_handles_labels()
    axis_c.legend(handles[::2], labels[::2], frameon=False, loc="upper left", ncols=2)

    figure.suptitle("Formula-derived reproduction of Main Figure 2", fontsize=14)
    figure.subplots_adjust(left=0.04, right=0.98, bottom=0.08, top=0.90, wspace=0.30, hspace=0.33)
    figure.savefig(path, dpi=180, facecolor="white")
    plt.close(figure)


def main() -> int:
    started = time.perf_counter()

    data_dir = CASE / "outputs" / "data"
    figure_dir = CASE / "outputs" / "figures"
    check_dir = CASE / "outputs" / "checks"
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)

    theta = np.linspace(0.0, 2.0 * np.pi, 721)
    loop = tracked_exceptional_loop(theta, radius=1.0)

    grid_values = np.linspace(-1.5, 1.5, 181)
    kx, ky = np.meshgrid(grid_values, grid_values, indexing="xy")
    surface_plus, surface_minus = exceptional_eigenvalues(kx, ky)
    surface = {"kx": kx, "ky": ky, "e_plus": surface_plus, "e_minus": surface_minus}

    cut_ky = np.linspace(-2.0, 2.0, 801)
    cut_plus, cut_minus = exceptional_eigenvalues(np.zeros_like(cut_ky), cut_ky)
    cut = {"ky": cut_ky, "e_plus": cut_plus, "e_minus": cut_minus}

    loop_path = data_dir / "main_fig2_ep_loop.csv"
    surface_path = data_dir / "main_fig2_ep_surface.npz"
    cut_path = data_dir / "main_fig2_ep_cut.csv"
    check_path = check_dir / "t002_scientific_checks.json"
    figure_path = figure_dir / "main_fig2_reproduction.png"

    write_loop_csv(loop_path, loop)
    np.savez_compressed(surface_path, **surface)
    write_cut_csv(cut_path, cut_ky, cut_plus, cut_minus)

    checks = scientific_checks(loop)
    checks["runtime_seconds"] = time.perf_counter() - started
    check_path.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if checks["status"] != "passed":
        print(json.dumps(checks, indent=2))
        return 1

    render_figure(figure_path, loop, surface, cut)
    elapsed = time.perf_counter() - started
    print(
        json.dumps(
            {
                "status": "passed",
                "target_id": TARGET_ID,
                "runtime_seconds": elapsed,
                "outputs": [
                    str(loop_path.relative_to(CASE)),
                    str(surface_path.relative_to(CASE)),
                    str(cut_path.relative_to(CASE)),
                    str(check_path.relative_to(CASE)),
                    str(figure_path.relative_to(CASE)),
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
