#!/usr/bin/env python3
"""Generate Main Figure 3 from the Dirac degeneracy conditions."""

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
    dirac_radicand,
    energy_difference_vorticity,
    exceptional_trajectory,
)


TARGET_ID = "T003"
DELTA = 1.0
KAPPA_X = 1.0
KAPPA_Y = 0.0


def require_guard() -> None:
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID", "") != TARGET_ID:
        raise RuntimeError(
            "Run this target through PRAgent-workflow/scripts/run_target.py so the live formula gate is enforced."
        )


def write_trajectory_csv(path: Path, masses: np.ndarray, points: np.ndarray) -> None:
    fields = ["mass", "branch", "kx", "ky", "radicand_real", "radicand_imag"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for mass_index, mass in enumerate(masses):
            for branch_index, branch in enumerate(("plus", "minus")):
                kx, ky = points[mass_index, branch_index]
                radicand = dirac_radicand(
                    kx,
                    ky,
                    kappa_x=KAPPA_X,
                    kappa_y=KAPPA_Y,
                    mass=float(mass),
                    delta=DELTA,
                )
                writer.writerow(
                    {
                        "mass": f"{mass:.17g}",
                        "branch": branch,
                        "kx": f"{kx:.17g}",
                        "ky": f"{ky:.17g}",
                        "radicand_real": f"{radicand.real:.17g}",
                        "radicand_imag": f"{radicand.imag:.17g}",
                    }
                )


def local_ep_vorticity(point: np.ndarray, mass: float, radius: float = 0.02) -> float:
    theta = np.linspace(0.0, 2.0 * np.pi, 1001)
    kx = point[0] + radius * np.cos(theta)
    ky = point[1] + radius * np.sin(theta)
    radicand = dirac_radicand(
        kx,
        ky,
        kappa_x=KAPPA_X,
        kappa_y=KAPPA_Y,
        mass=mass,
        delta=DELTA,
    )
    phase = np.unwrap(np.angle(radicand))
    energy_difference = 2.0 * np.sqrt(np.abs(radicand)) * np.exp(0.5j * phase)
    return energy_difference_vorticity(energy_difference)


def scientific_checks(masses: np.ndarray, points: np.ndarray) -> dict[str, object]:
    residuals = []
    for mass_index, mass in enumerate(masses):
        for point in points[mass_index]:
            residuals.append(
                abs(
                    dirac_radicand(
                        point[0],
                        point[1],
                        kappa_x=KAPPA_X,
                        kappa_y=KAPPA_Y,
                        mass=float(mass),
                        delta=DELTA,
                    )
                )
            )

    # For kappa=(delta,0), eliminating mass gives kx^2 + ky^2/2 = 1.
    ellipse_residual = np.max(np.abs(points[..., 0] ** 2 + points[..., 1] ** 2 / 2.0 - 1.0))
    endpoint_pair_error = max(
        np.linalg.norm(points[0, 0] - points[0, 1]),
        np.linalg.norm(points[-1, 0] - points[-1, 1]),
    )
    midpoint_index = masses.size // 2
    charges = [
        local_ep_vorticity(points[midpoint_index, branch_index], float(masses[midpoint_index]))
        for branch_index in range(2)
    ]

    metrics = {
        "max_ep_radicand_residual": float(max(residuals)),
        "max_ellipse_identity_residual": float(ellipse_residual),
        "hybrid_endpoint_pair_separation": float(endpoint_pair_error),
        "midpoint_vorticities": [float(value) for value in charges],
        "vorticity_sum": float(sum(charges)),
        "trajectory_mass_range": [float(masses[0]), float(masses[-1])],
    }
    criteria = {
        "closed_form_points_are_degenerate": bool(
            metrics["max_ep_radicand_residual"] < 1e-12
        ),
        "trajectory_is_expected_ellipse": bool(
            metrics["max_ellipse_identity_residual"] < 1e-12
        ),
        "ep_pair_merges_at_both_hybrid_boundaries": bool(endpoint_pair_error < 1e-12),
        "opposite_half_charges": bool(
            all(abs(abs(value) - 0.5) < 1e-6 for value in charges)
            and abs(sum(charges)) < 1e-6
        ),
    }
    return {
        "schema_version": 1,
        "paper_id": "1706.07435",
        "target_id": TARGET_ID,
        "status": "passed" if all(criteria.values()) else "failed",
        "generated_data_provenance": "analytic_reference",
        "source_pixels_used_in_generation": False,
        "paper_parameters": {"delta": DELTA, "kappa": [KAPPA_X, KAPPA_Y]},
        "metrics": metrics,
        "criteria": criteria,
    }


def render_figure(path: Path, masses: np.ndarray, points: np.ndarray) -> None:
    plt.rcParams.update({"font.size": 15, "axes.linewidth": 1.3})
    figure, (axis_a, axis_b) = plt.subplots(1, 2, figsize=(11.6, 4.2))

    m_plot = np.linspace(-1.25, 1.25, 501)
    upper = np.full_like(m_plot, 1.25)
    inside = np.abs(m_plot) <= 1.25
    axis_a.fill_between(
        m_plot[inside], np.abs(m_plot[inside]), upper[inside], color="#9cc7e5", zorder=0
    )
    axis_a.plot([-1.25, 0.0], [1.25, 0.0], color="#f06c68", lw=4.0)
    axis_a.plot([0.0, 1.25], [0.0, 1.25], color="#f06c68", lw=4.0)
    axis_a.axhline(0.0, color="black", lw=1.5)
    dashed_kappa = 0.62
    axis_a.plot([-1.05, 0.96], [dashed_kappa, dashed_kappa], "--", color="#a01f68", lw=2.2)
    axis_a.annotate(
        "",
        xy=(1.03, dashed_kappa),
        xytext=(0.87, dashed_kappa),
        arrowprops={"arrowstyle": "-|>", "color": "#a01f68", "lw": 2.2},
    )
    axis_a.scatter([0.0], [0.0], s=90, color="#26487b", zorder=4)
    axis_a.annotate("HP", (-0.62, 0.62), xytext=(-0.93, 0.28), arrowprops={"arrowstyle": "->"})
    axis_a.annotate(
        r"DP ($\delta=0$)" + "\n" + r"EP Ring ($\delta\ne0$)",
        (0.06, 0.02),
        xytext=(0.35, 0.18),
        arrowprops={"arrowstyle": "->"},
        va="center",
    )
    axis_a.text(-0.04, 1.31, r"$\kappa$", fontsize=18)
    axis_a.text(1.29, -0.04, r"$m$", fontsize=18)
    axis_a.set_xlim(-1.38, 1.38)
    axis_a.set_ylim(-0.08, 1.38)
    axis_a.set_xticks([])
    axis_a.set_yticks([])
    axis_a.spines[["left", "right", "top"]].set_visible(False)
    axis_a.set_title("(a)", loc="left", fontsize=22)

    color = "#a51f67"
    for branch_index in range(2):
        axis_b.plot(points[:, branch_index, 1], points[:, branch_index, 0], color=color, lw=2.4)
    for branch_index, indices in ((0, (85, 250, 415)), (1, (85, 250, 415))):
        for index in indices:
            start = points[index, branch_index]
            end = points[index + 7, branch_index]
            axis_b.annotate(
                "",
                xy=(end[1], end[0]),
                xytext=(start[1], start[0]),
                arrowprops={"arrowstyle": "-|>", "color": color, "lw": 2.0, "mutation_scale": 18},
            )
    axis_b.axhline(0.0, color="black", lw=0.9)
    axis_b.axvline(0.0, color="black", lw=0.9)
    axis_b.text(0.50, 1.02, r"$\hat{n}$", transform=axis_b.transAxes, ha="center")
    axis_b.text(0.96, 0.53, r"$\hat{z}\!\times\!\hat{n}$", transform=axis_b.transAxes, va="center")
    axis_b.text(0.47, 0.93, r"$\delta$", transform=axis_b.transAxes, ha="right")
    axis_b.text(0.45, 0.04, r"$-\delta$", transform=axis_b.transAxes, ha="right")
    axis_b.text(0.73, 0.42, r"$\sqrt{\kappa^2+\delta^2}$", transform=axis_b.transAxes, ha="center")
    axis_b.text(0.27, 0.42, r"$-\sqrt{\kappa^2+\delta^2}$", transform=axis_b.transAxes, ha="center")
    axis_b.set_aspect("equal", adjustable="box")
    axis_b.set_xlim(-1.65, 1.65)
    axis_b.set_ylim(-1.15, 1.15)
    axis_b.set_xticks([])
    axis_b.set_yticks([])
    axis_b.spines[:].set_visible(False)
    axis_b.set_title("(b)", loc="left", fontsize=22)

    figure.subplots_adjust(left=0.03, right=0.97, bottom=0.06, top=0.94, wspace=0.18)
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

    masses = np.linspace(-1.0, 1.0, 501)
    points = exceptional_trajectory(
        masses, kappa_x=KAPPA_X, kappa_y=KAPPA_Y, delta=DELTA
    )

    trajectory_path = data_dir / "main_fig3_ep_trajectory.csv"
    phase_path = data_dir / "main_fig3_phase_grid.npz"
    check_path = check_dir / "t003_scientific_checks.json"
    figure_path = figure_dir / "main_fig3_reproduction.png"

    write_trajectory_csv(trajectory_path, masses, points)
    phase_m = np.linspace(-1.4, 1.4, 561)
    phase_kappa = np.linspace(0.0, 1.4, 281)
    mesh_m, mesh_kappa = np.meshgrid(phase_m, phase_kappa, indexing="xy")
    phase_code = np.where(mesh_kappa > np.abs(mesh_m), 1, 0).astype(np.int8)
    np.savez_compressed(
        phase_path,
        mass=mesh_m,
        kappa=mesh_kappa,
        phase_code=phase_code,
        phase_code_meaning=np.array(["separable", "exceptional_point_pair"]),
    )

    checks = scientific_checks(masses, points)
    checks["runtime_seconds"] = time.perf_counter() - started
    check_path.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if checks["status"] != "passed":
        print(json.dumps(checks, indent=2))
        return 1

    render_figure(figure_path, masses, points)
    print(
        json.dumps(
            {
                "status": "passed",
                "target_id": TARGET_ID,
                "runtime_seconds": time.perf_counter() - started,
                "outputs": [
                    str(trajectory_path.relative_to(WORKSPACE)),
                    str(phase_path.relative_to(WORKSPACE)),
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
