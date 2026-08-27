#!/usr/bin/env python3
"""Generate all numerical targets without access to source figures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from src.bem import (
    coupled_rounded_hexagon_mesh,
    far_field,
    reconstruct_field,
    resonance_boundary_state,
    resolution_metric,
    scan_cross_section,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        parameters = json.load(handle)["parameters"]

    started = time.monotonic()
    n_inside = float(parameters["n_inside"])
    quadrature_order = int(parameters["quadrature_order"])
    mesh = coupled_rounded_hexagon_mesh(
        int(parameters["side_elements"]),
        int(parameters["corner_elements"]),
        float(parameters["corner_radius_R"]),
    )

    scan_config = parameters["scan"]
    coarse = np.linspace(
        scan_config["coarse_start"],
        scan_config["coarse_stop"],
        int(scan_config["coarse_count"]),
    )
    fine = np.linspace(
        scan_config["fine_start"],
        scan_config["fine_stop"],
        int(scan_config["fine_count"]),
    )
    wave_numbers = np.unique(np.round(np.concatenate((coarse, fine)), 10))
    scan_started = time.monotonic()
    scan = scan_cross_section(
        mesh,
        wave_numbers,
        incidence_angle=np.deg2rad(parameters["incidence_angle_degrees"]),
        angular_samples=int(scan_config["angular_samples"]),
        n_inside=n_inside,
        quadrature_order=quadrature_order,
    )
    scan_runtime = time.monotonic() - scan_started

    resonance_pair = parameters["reported_resonance_kR"]
    resonance_k = complex(float(resonance_pair[0]), float(resonance_pair[1]))
    convergence: list[dict[str, float | int]] = []
    for side_elements, corner_elements in parameters["mesh_convergence"]:
        trial_mesh = coupled_rounded_hexagon_mesh(
            int(side_elements),
            int(corner_elements),
            float(parameters["corner_radius_R"]),
        )
        state = resonance_boundary_state(
            trial_mesh,
            resonance_k,
            n_inside=n_inside,
            quadrature_order=quadrature_order,
        )
        convergence.append(
            {
                "side_elements": int(side_elements),
                "corner_elements": int(corner_elements),
                "boundary_elements": trial_mesh.size,
                "resolution_b": resolution_metric(trial_mesh, resonance_k, n_inside),
                "smallest_singular": float(state["smallest_singular"]),
            }
        )

    resonance_state = resonance_boundary_state(
        mesh,
        resonance_k,
        n_inside=n_inside,
        quadrature_order=quadrature_order,
    )
    field_config = parameters["near_field"]
    x = np.linspace(field_config["x_min"], field_config["x_max"], int(field_config["x_count"]))
    y = np.linspace(field_config["y_min"], field_config["y_max"], int(field_config["y_count"]))
    xx, yy = np.meshgrid(x, y)
    field = reconstruct_field(
        mesh,
        resonance_k,
        resonance_state["phi"],
        resonance_state["psi"],
        np.column_stack((xx.ravel(), yy.ravel())),
        n_inside=n_inside,
        quadrature_order=quadrature_order,
    ).reshape(yy.shape)
    near_intensity = np.abs(field) ** 2
    near_intensity /= max(float(np.nanmax(near_intensity)), np.finfo(float).tiny)

    far_angles = np.linspace(
        0, 2 * np.pi, int(parameters["far_field_angular_samples"]), endpoint=False
    )
    far_amplitude = far_field(
        mesh,
        resonance_k,
        resonance_state["phi"],
        resonance_state["psi"],
        far_angles,
        quadrature_order=quadrature_order,
    )
    far_intensity = np.abs(far_amplitude) ** 2
    far_intensity /= max(float(np.max(far_intensity)), np.finfo(float).tiny)

    output_dir = Path("outputs/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_dir / "bem_reproduction.npz",
        scan_k=scan["k"],
        scan_sigma=scan["sigma"],
        scan_sigma_optical=scan["sigma_optical"],
        scan_optical_relative_error=scan["optical_relative_error"],
        scan_linear_residual=scan["linear_residual"],
        resonance_k=np.array([resonance_k.real, resonance_k.imag]),
        mesh_start=mesh.start,
        mesh_end=mesh.end,
        mesh_midpoint=mesh.midpoint,
        mesh_normal=mesh.normal,
        mesh_cavity=mesh.cavity,
        boundary_phi=resonance_state["phi"],
        boundary_psi=resonance_state["psi"],
        near_x=x,
        near_y=y,
        near_intensity=near_intensity,
        far_angle=far_angles,
        far_intensity=far_intensity,
    )

    peak_indices = np.argsort(scan["sigma"])[-8:][::-1]
    summary = {
        "schema_version": 1,
        "paper_id": "physics-0206018",
        "method": "constant-element TM BEM with declared circular fillets",
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_data_used": False,
        "parameters": parameters,
        "runtime_seconds": time.monotonic() - started,
        "scan_runtime_seconds": scan_runtime,
        "matrix_dimension": 2 * mesh.size,
        "boundary_elements": mesh.size,
        "resolution_b_at_reported_resonance": resolution_metric(mesh, resonance_k, n_inside),
        "corner_radius_over_min_element": float(parameters["corner_radius_R"] / np.min(mesh.length)),
        "linear_residual_max": float(np.max(scan["linear_residual"])),
        "optical_theorem_relative_error_median": float(np.median(scan["optical_relative_error"])),
        "optical_theorem_relative_error_max": float(np.max(scan["optical_relative_error"])),
        "largest_scan_peaks": [
            {"kR": float(scan["k"][index]), "sigma_over_R": float(scan["sigma"][index])}
            for index in peak_indices
        ],
        "reported_resonance": {
            "kR_real": resonance_k.real,
            "kR_imag": resonance_k.imag,
            "smallest_singular": float(resonance_state["smallest_singular"]),
            "boundary_relative_residual": float(resonance_state["relative_residual"]),
            "selection": "value printed in paper; independently challenged by mesh singular-value convergence"
        },
        "mesh_convergence": convergence,
        "fidelity": {
            "level": "feature_reproduced_candidate",
            "paper_exact": False,
            "reason": "the paper omits the exact corner-rounding curve and nonuniform mesh; this run declares circular fillets and 432 rather than 1600 boundary elements"
        }
    }
    with (output_dir / "bem_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
