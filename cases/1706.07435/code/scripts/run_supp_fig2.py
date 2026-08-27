#!/usr/bin/env python3
"""Generate Supplement Figure 2 from the domain-wall matching equations."""

from __future__ import annotations

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
from scipy.optimize import root  # noqa: E402

sys.path.insert(0, str(WORKSPACE / "src"))

from nonhermitian_topology import (  # noqa: E402
    DiracDomain,
    solve_domain_wall_edge,
    symmetric_domain_wall_energy,
)


TARGET_ID = "T004"
MASS_SCALE = 1.0
KAPPA_SAMPLES = 121


def require_guard() -> None:
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID", "") != TARGET_ID:
        raise RuntimeError(
            "Run this target through PRAgent-workflow/scripts/run_target.py so the live formula gate is enforced."
        )


def matching_root_residual(values: np.ndarray, kappa_left: float, kappa_right: float) -> np.ndarray:
    energy = values[0] + 1.0j * values[1]
    inverse_left = values[2] + 1.0j * values[3]
    inverse_right = values[4] + 1.0j * values[5]
    mass_left = -MASS_SCALE
    mass_right = MASS_SCALE
    momentum_left = 1.0j * kappa_left
    momentum_right = 1.0j * kappa_right
    equations = np.array(
        [
            energy**2 - (mass_left**2 + momentum_left**2 - inverse_left**2),
            energy**2 - (mass_right**2 + momentum_right**2 - inverse_right**2),
            (mass_left + energy) * (momentum_right - inverse_right)
            - (mass_right + energy) * (momentum_left - inverse_left),
        ],
        dtype=np.complex128,
    )
    return np.column_stack((equations.real, equations.imag)).ravel()


def scientific_checks() -> dict[str, object]:
    pairs = [(-0.8, -0.25), (-0.65, 0.35), (-0.2, 0.75), (0.25, -0.55), (0.6, 0.85)]
    formula_errors = []
    equation_residuals = []
    localization_margins = []
    nonlinear_errors = []
    nonlinear_residuals = []
    nonlinear_success = []

    for kappa_left, kappa_right in pairs:
        left = DiracDomain(0.0, kappa_left, -MASS_SCALE, 0.0)
        right = DiracDomain(0.0, kappa_right, MASS_SCALE, 0.0)
        solution = solve_domain_wall_edge(0.0, left, right)
        formula = symmetric_domain_wall_energy(
            kappa_left, kappa_right, mass_scale=MASS_SCALE
        ).item()
        formula_errors.append(abs(solution.energy - formula))
        equation_residuals.append(solution.equation_residual)
        localization_margins.append(solution.localization_margin)

        initial = np.array(
            [
                solution.energy.real,
                solution.energy.imag,
                solution.inverse_length_left.real,
                solution.inverse_length_left.imag,
                solution.inverse_length_right.real,
                solution.inverse_length_right.imag,
            ]
        )
        nonlinear = root(matching_root_residual, initial, args=(kappa_left, kappa_right), method="hybr")
        nonlinear_energy = nonlinear.x[0] + 1.0j * nonlinear.x[1]
        nonlinear_success.append(bool(nonlinear.success))
        nonlinear_errors.append(abs(nonlinear_energy - formula))
        nonlinear_residuals.append(float(np.max(np.abs(matching_root_residual(nonlinear.x, kappa_left, kappa_right)))))

    diagonal = np.linspace(-0.95, 0.95, 301)
    equal_line = symmetric_domain_wall_energy(diagonal, diagonal, mass_scale=MASS_SCALE)
    zero_line = symmetric_domain_wall_energy(diagonal, -diagonal, mass_scale=MASS_SCALE)
    odd_left, odd_right = np.meshgrid(
        np.linspace(-0.85, 0.85, 41), np.linspace(-0.85, 0.85, 41), indexing="xy"
    )
    odd_surface = symmetric_domain_wall_energy(odd_left, odd_right, mass_scale=MASS_SCALE)
    reflected_surface = symmetric_domain_wall_energy(-odd_left, -odd_right, mass_scale=MASS_SCALE)

    metrics = {
        "max_closed_form_vs_full_matching_error": float(max(formula_errors)),
        "max_matching_equation_residual": float(max(equation_residuals)),
        "minimum_localization_margin": float(min(localization_margins)),
        "max_nonlinear_root_energy_error": float(max(nonlinear_errors)),
        "max_nonlinear_root_residual": float(max(nonlinear_residuals)),
        "all_nonlinear_roots_converged": bool(all(nonlinear_success)),
        "max_equal_kappa_identity_error": float(np.max(np.abs(equal_line - 1.0j * diagonal))),
        "max_zero_plane_error": float(np.max(np.abs(zero_line))),
        "max_odd_symmetry_error": float(np.max(np.abs(odd_surface + reflected_surface))),
    }
    criteria = {
        "closed_form_matches_full_matching": metrics["max_closed_form_vs_full_matching_error"] < 1e-12,
        "matching_equations": metrics["max_matching_equation_residual"] < 2e-12,
        "localized_solutions": metrics["minimum_localization_margin"] > 0.35,
        "independent_nonlinear_roots": (
            metrics["all_nonlinear_roots_converged"]
            and metrics["max_nonlinear_root_energy_error"] < 1e-10
            and metrics["max_nonlinear_root_residual"] < 1e-10
        ),
        "equal_kappa_limit": metrics["max_equal_kappa_identity_error"] < 1e-12,
        "zero_plane_kappa_sum": metrics["max_zero_plane_error"] < 1e-12,
        "gain_loss_odd_symmetry": metrics["max_odd_symmetry_error"] < 1e-12,
    }
    return {
        "schema_version": 1,
        "paper_id": "1706.07435",
        "target_id": TARGET_ID,
        "status": "passed" if all(criteria.values()) else "failed",
        "generated_data_provenance": "analytic_reference",
        "source_pixels_used_in_generation": False,
        "paper_parameters": {
            "mass_left": -MASS_SCALE,
            "mass_right": MASS_SCALE,
            "ky": 0.0,
            "kappa_x": [0.0, 0.0],
            "delta": [0.0, 0.0],
        },
        "metrics": metrics,
        "criteria": criteria,
    }


def render_figure(path: Path, kappa_left: np.ndarray, kappa_right: np.ndarray, energy: np.ndarray) -> None:
    plt.rcParams.update({"font.size": 11, "axes.linewidth": 0.7})
    figure = plt.figure(figsize=(7.2, 5.8))
    axis = figure.add_subplot(111, projection="3d")
    axis.plot_surface(
        kappa_left,
        kappa_right,
        energy.imag,
        rstride=4,
        cstride=4,
        color="#ef7b50",
        alpha=0.86,
        edgecolor="#633c30",
        linewidth=0.25,
    )
    axis.plot_surface(
        kappa_left,
        kappa_right,
        np.zeros_like(kappa_left),
        rstride=8,
        cstride=8,
        color="#86c9ca",
        alpha=0.45,
        edgecolor="#497f80",
        linewidth=0.3,
    )
    axis.set_xlabel(r"$\kappa_{y,1}$", labelpad=7)
    axis.set_ylabel(r"$\kappa_{y,2}$", labelpad=7)
    axis.set_zlabel("Im(E)", labelpad=5)
    axis.set_xlim(-1.0, 1.0)
    axis.set_ylim(-1.0, 1.0)
    axis.set_zlim(-1.0, 1.0)
    axis.set_xticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    axis.set_yticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    axis.set_zticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    axis.view_init(elev=24, azim=-58)
    axis.set_box_aspect((1.15, 1.0, 0.68))
    figure.subplots_adjust(left=0.01, right=0.97, bottom=0.02, top=0.98)
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

    kappa_values = np.linspace(-0.99, 0.99, KAPPA_SAMPLES)
    kappa_left, kappa_right = np.meshgrid(kappa_values, kappa_values, indexing="xy")
    energy = symmetric_domain_wall_energy(
        kappa_left,
        kappa_right,
        mass_scale=MASS_SCALE,
    )

    data_path = data_dir / "supp_fig2_domain_wall_surface.npz"
    check_path = check_dir / "t004_scientific_checks.json"
    figure_path = figure_dir / "supp_fig2_reproduction.png"
    np.savez_compressed(
        data_path,
        kappa_left_y=kappa_left,
        kappa_right_y=kappa_right,
        edge_energy=energy,
    )

    checks = scientific_checks()
    checks["runtime_seconds"] = time.perf_counter() - started
    check_path.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if checks["status"] != "passed":
        print(json.dumps(checks, indent=2))
        return 1

    render_figure(figure_path, kappa_left, kappa_right, energy)
    print(
        json.dumps(
            {
                "status": "passed",
                "target_id": TARGET_ID,
                "runtime_seconds": time.perf_counter() - started,
                "outputs": [
                    str(data_path.relative_to(WORKSPACE)),
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
