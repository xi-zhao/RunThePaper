#!/usr/bin/env python3
"""Generate the formula-derived arrays without importing the render stack."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.fermionic_phase_space import (  # noqa: E402
    covariance_determinants,
    crossing_points,
    entropy_lower_bound,
    fermi_dirac_occupation,
    phase_space_bodies,
    renyi_entropy,
    thermal_loss_output_occupation,
)


def _write_csv(path: Path, columns: list[str], arrays: list[np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for row in zip(*arrays, strict=True):
            writer.writerow([f"{float(value):.16g}" for value in row])


def run(config_path: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    grid = config["scientific_grid"]
    x = np.linspace(
        float(grid["fermi_x_min"]),
        float(grid["fermi_x_max"]),
        int(grid["fermi_points"]),
    )
    occupation = fermi_dirac_occupation(x)
    n = np.linspace(0.0, 1.0, int(grid["occupation_points"]))
    moments = covariance_determinants(n)
    entropies = {
        distribution: renyi_entropy(n, 1.0, distribution)
        for distribution in ("P", "W", "Q")
    }
    orders = tuple(float(value) for value in grid["renyi_orders"])
    renyi_curves = {order: renyi_entropy(n, order, "W") for order in orders}

    data_dir = WORKSPACE / "outputs" / "data"
    _write_csv(
        data_dir / "figure_1_fermi_dirac.csv",
        ["epsilon_over_T", "occupation"],
        [x, occupation],
    )
    _write_csv(
        data_dir / "figure_2_moments.csv",
        ["occupation", "det_gamma_P", "det_gamma_W", "det_gamma_Q"],
        [n, moments.glauber_p, moments.wigner_w, moments.husimi_q],
    )
    _write_csv(
        data_dir / "figure_2_entropies.csv",
        [
            "occupation",
            "S_P",
            "S_W",
            "S_Q",
            "S_W_r_1_4",
            "S_W_r_1_2",
            "S_W_r_1",
            "S_W_r_2",
            "S_W_r_4",
        ],
        [
            n,
            entropies["P"],
            entropies["W"],
            entropies["Q"],
            *[renyi_curves[order] for order in orders],
        ],
    )

    bodies = phase_space_bodies(n)
    crossings = crossing_points()
    thermal_output = thermal_loss_output_occupation(0.1, 0.6, 0.6)
    thermal_error = abs(
        float(renyi_entropy(thermal_output, 2.0, "W")) - float(np.log(2.5))
    )
    renyi_values = np.asarray(
        [float(renyi_entropy(0.2, order, "W")) for order in orders]
    )
    metrics = {
        "fermi_particle_hole_max_abs_error": float(
            np.max(np.abs(occupation + occupation[::-1] - 1.0))
        ),
        "body_spacing_p_to_w_max_abs_error": float(
            np.max(np.abs(bodies.wigner_w - bodies.glauber_p - 0.5))
        ),
        "body_spacing_w_to_q_max_abs_error": float(
            np.max(np.abs(bodies.husimi_q - bodies.wigner_w - 0.5))
        ),
        "moment_minima": {
            "P": float(np.min(moments.glauber_p)),
            "W": float(np.min(moments.wigner_w)),
            "Q": float(np.min(moments.husimi_q)),
        },
        "crossings": crossings,
        "wigner_entropy_bounds": {
            str(order): entropy_lower_bound(order, "W") for order in orders
        },
        "wigner_renyi_monotonic_min_step": float(np.min(np.diff(renyi_values))),
        "thermal_channel_absolute_error": thermal_error,
    }
    passed = (
        metrics["fermi_particle_hole_max_abs_error"] < 1e-14
        and metrics["body_spacing_p_to_w_max_abs_error"] < 1e-14
        and metrics["body_spacing_w_to_q_max_abs_error"] < 1e-14
        and metrics["moment_minima"] == {"P": -1.0, "W": -0.25, "Q": -1.0}
        and metrics["wigner_renyi_monotonic_min_step"] > 0.0
        and thermal_error < 1e-14
    )
    payload = {
        "schema_version": 1,
        "paper_id": "2401.08523",
        "target_ids": ["T001", "T002"],
        "status": "passed" if passed else "failed",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "author_arrays_used_in_generation": False,
        "config": grid,
        "metrics": metrics,
    }
    check_path = WORKSPACE / "outputs" / "checks" / "formula_implementation_validation.json"
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    payload = run(arguments.config)
    print(json.dumps({"status": payload["status"], "target_ids": payload["target_ids"]}))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
