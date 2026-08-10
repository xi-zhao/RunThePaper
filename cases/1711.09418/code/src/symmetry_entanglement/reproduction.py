"""Paper-exact, source-blind numerical runner for Figs. 2 and 3."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .model import (
    analytic_charge_curves,
    analytic_integrated_spectrum,
    correlation_eigenvalues,
    enumerate_many_body_spectrum,
    resolved_probability_and_entropy,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(config_path: Path) -> None:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    length = int(parameters["subsystem_length"])
    active_modes = int(parameters["active_correlation_modes"])
    sectors = tuple(int(value) for value in parameters["fig3_sectors"])

    eigenvalues = correlation_eigenvalues(length, active_modes)
    thermodynamics = resolved_probability_and_entropy(eigenvalues, subsystem_length=length)
    delta_values = np.arange(
        int(parameters["fig2_delta_min"]),
        int(parameters["fig2_delta_max"]) + 1,
        dtype=int,
    )
    wanted_particles = length // 2 + delta_values
    index = {int(number): offset for offset, number in enumerate(thermodynamics.particle_numbers)}
    numeric_probability = np.asarray([thermodynamics.probability[index[int(n)]] for n in wanted_particles])
    numeric_entropy = np.asarray([thermodynamics.entropy_contribution[index[int(n)]] for n in wanted_particles])
    analytic_probability, analytic_entropy, analytic_constants = analytic_charge_curves(delta_values, length)

    fig2_rows = []
    for offset, delta in enumerate(delta_values):
        fig2_rows.append(
            {
                "delta_n": int(delta),
                "particle_number": int(wanted_particles[offset]),
                "probability_numeric": format(float(numeric_probability[offset]), ".17g"),
                "entropy_numeric": format(float(numeric_entropy[offset]), ".17g"),
                "probability_analytic": format(float(analytic_probability[offset]), ".17g"),
                "entropy_analytic": format(float(analytic_entropy[offset]), ".17g"),
            }
        )
    fig2_path = Path("outputs/data/fig2_charge_resolved.csv")
    write_csv(
        fig2_path,
        [
            "delta_n",
            "particle_number",
            "probability_numeric",
            "entropy_numeric",
            "probability_analytic",
            "entropy_analytic",
        ],
        fig2_rows,
    )

    spectrum = enumerate_many_body_spectrum(
        eigenvalues,
        selected_modes=int(parameters["fig3_selected_modes"]),
        sectors=sectors,
        rank_max=int(parameters["fig3_rank_max"]),
        x_max=float(parameters["fig3_x_max"]),
    )
    numeric_rows: list[dict[str, object]] = []
    for sector, (x_values, ranks) in spectrum.curves.items():
        for x_value, rank in zip(x_values, ranks):
            numeric_rows.append(
                {"sector": sector, "x": format(float(x_value), ".17g"), "integrated_count": int(rank)}
            )
    fig3_numeric_path = Path("outputs/data/fig3_spectrum_numeric.csv")
    write_csv(fig3_numeric_path, ["sector", "x", "integrated_count"], numeric_rows)

    analytic_x = np.linspace(
        0.0,
        float(parameters["fig3_x_max"]),
        int(parameters["fig3_analytic_points"]),
        dtype=np.float64,
    )
    analytic_curves = analytic_integrated_spectrum(
        analytic_x,
        sectors,
        quadrature_nodes=int(parameters["quadrature_nodes"]),
    )
    analytic_rows: list[dict[str, object]] = []
    for sector, counts in analytic_curves.items():
        for x_value, count in zip(analytic_x, counts):
            analytic_rows.append(
                {"sector": sector, "x": format(float(x_value), ".17g"), "integrated_count": format(float(count), ".17g")}
            )
    fig3_analytic_path = Path("outputs/data/fig3_spectrum_analytic.csv")
    write_csv(fig3_analytic_path, ["sector", "x", "integrated_count"], analytic_rows)

    single_particle_path = Path("outputs/data/single_particle_spectrum.csv")
    safe = np.clip(eigenvalues, np.finfo(float).tiny, 1.0 - np.finfo(float).eps)
    energies = np.log1p(-safe) - np.log(safe)
    write_csv(
        single_particle_path,
        ["mode", "correlation_eigenvalue", "entanglement_energy"],
        [
            {
                "mode": offset,
                "correlation_eigenvalue": format(float(value), ".17g"),
                "entanglement_energy": format(float(energies[offset]), ".17g"),
            }
            for offset, value in enumerate(eigenvalues)
        ],
    )

    center = int(np.where(delta_values == 0)[0][0])
    entropy_from_modes = -float(
        np.sum(safe * np.log(safe) + (1.0 - safe) * np.log1p(-safe))
    )
    checks: dict[str, Any] = {
        "correlation_window_is_saturated": {
            "passed": bool(eigenvalues[0] < 1.0e-13 and eigenvalues[-1] > 1.0 - 1.0e-13),
            "lowest": float(eigenvalues[0]),
            "highest": float(eigenvalues[-1]),
        },
        "particle_hole_symmetry": {
            "passed": bool(np.max(np.abs(eigenvalues + eigenvalues[::-1] - 1.0)) < 5.0e-11),
            "max_abs_residual": float(np.max(np.abs(eigenvalues + eigenvalues[::-1] - 1.0))),
        },
        "resolved_probability_normalization": {
            "passed": bool(abs(float(thermodynamics.probability.sum()) - 1.0) < 1.0e-12),
            "sum": float(thermodynamics.probability.sum()),
        },
        "resolved_entropy_sum": {
            "passed": bool(abs(float(thermodynamics.entropy_contribution.sum()) - entropy_from_modes) < 1.0e-11),
            "resolved_sum": float(thermodynamics.entropy_contribution.sum()),
            "mode_entropy": entropy_from_modes,
        },
        "fig2_center_values": {
            "passed": bool(numeric_probability[center] > 0.3 and numeric_entropy[center] > 1.0),
            "probability": float(numeric_probability[center]),
            "entropy": float(numeric_entropy[center]),
        },
        "fig2_exact_symmetry": {
            "passed": bool(
                np.max(np.abs(numeric_probability - numeric_probability[::-1])) < 1.0e-11
                and np.max(np.abs(numeric_entropy - numeric_entropy[::-1])) < 1.0e-11
            ),
            "probability_residual": float(np.max(np.abs(numeric_probability - numeric_probability[::-1]))),
            "entropy_residual": float(np.max(np.abs(numeric_entropy - numeric_entropy[::-1]))),
        },
        "fig3_all_sector_identity": {
            "passed": bool(np.allclose(analytic_curves["all"], np.i0(analytic_x), rtol=1.0e-13, atol=1.0e-13)),
            "max_abs_residual": float(np.max(np.abs(analytic_curves["all"] - np.i0(analytic_x)))),
        },
        "fig3_selected_modes": {
            "passed": bool(spectrum.selected_entanglement_energies.size == int(parameters["fig3_selected_modes"])),
            "count": int(spectrum.selected_entanglement_energies.size),
            "central_log_lambda_max": spectrum.central_log_lambda_max,
        },
    }
    check_payload = {
        "schema_version": 1,
        "paper_id": "1711.09418",
        "status": "passed" if all(item["passed"] for item in checks.values()) else "failed",
        "parameters": parameters,
        "analytic_constants": analytic_constants,
        "checks": checks,
    }
    target_check_path = Path("outputs/checks/target_checks.json")
    write_json(target_check_path, check_payload)
    if check_payload["status"] != "passed":
        raise RuntimeError("scientific checks failed")

    artifacts = [fig2_path, fig3_numeric_path, fig3_analytic_path, single_particle_path, target_check_path]
    manifest = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": "1711.09418",
        "run_id": config["run_id"],
        "generated_data_provenance": "independent_formula_numerics",
        "source_pixels_read": False,
        "author_code_used": False,
        "author_arrays_used": False,
        "artifacts": [
            {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in artifacts
        ],
    }
    write_json(Path("outputs/checks/generated_data_manifest.json"), manifest)
