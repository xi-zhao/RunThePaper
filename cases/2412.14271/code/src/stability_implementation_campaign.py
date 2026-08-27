"""Focused clean-room implementation attestation for target T005.

The campaign reuses the printed-equation cumulant solver and evaluates the
normal, smallest-photon, and largest-photon stability spectra on a frozen
reduced coupling grid.  It intentionally preserves the existing scientific
discrepancy and does not turn successful execution into scientific coverage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .dicke import cumulant_jacobian, find_cumulant_solutions, physical_cumulant_state


TARGET_IDS = ("T005",)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _serialize(values: np.ndarray) -> list[dict[str, float]]:
    ordered = sorted(
        np.asarray(values, dtype=np.complex128),
        key=lambda value: (float(value.real), float(value.imag)),
    )
    return [
        {"real": float(value.real), "imag": float(value.imag)}
        for value in ordered
    ]


def stability_panel_records(params: dict[str, Any]) -> list[dict[str, Any]]:
    model = {
        "omega_c": float(params["omega_c"]),
        "omega_a": float(params["omega_a"]),
        "kappa1": float(params["kappa1"]),
        "kappa2": float(params["kappa2"]),
    }
    rows: list[dict[str, Any]] = []
    normal_state = physical_cumulant_state([0, 0, 0, 0, 0, 0])
    for coupling in params["couplings"]:
        coupling = float(coupling)
        normal_spectrum = np.linalg.eigvals(
            cumulant_jacobian(normal_state, coupling, **model)
        )
        solutions = find_cumulant_solutions(coupling, **model)
        if len(solutions) < int(params["minimum_nonzero_roots"]):
            raise RuntimeError(
                f"lambda={coupling}: expected at least "
                f"{params['minimum_nonzero_roots']} nonzero roots"
            )
        ordered = sorted(solutions, key=lambda row: float(row["photons"]))
        smallest = ordered[0]
        largest = ordered[-1]
        rows.append(
            {
                "lambda": coupling,
                "panel_a_normal": {
                    "eigenvalues": _serialize(normal_spectrum),
                    "largest_real_part": float(np.max(normal_spectrum.real)),
                },
                "panel_b_larger_superradiant": {
                    "photons_per_N": float(largest["photons"]),
                    "fixed_point_residual": float(largest["residual"]),
                    "largest_non_neutral_real_part": float(
                        largest["max_real_eigenvalue"]
                    ),
                    "eigenvalues": _serialize(np.asarray(largest["eigenvalues"])),
                },
                "panel_c_smaller_superradiant": {
                    "photons_per_N": float(smallest["photons"]),
                    "fixed_point_residual": float(smallest["residual"]),
                    "largest_non_neutral_real_part": float(
                        smallest["max_real_eigenvalue"]
                    ),
                    "eigenvalues": _serialize(np.asarray(smallest["eigenvalues"])),
                },
                "nonzero_root_count": len(ordered),
            }
        )
    return rows


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    declared = tuple(config.get("attestation_parameters", {}).get("target_ids", ()))
    if declared != TARGET_IDS:
        raise ValueError("campaign target list does not match T005")
    boundary = config.get("clean_room_boundary", {})
    for name in (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    ):
        if boundary.get(name) is not False:
            raise ValueError(f"clean-room boundary must set {name}=false")

    params = config["target"]
    rows = stability_panel_records(params)
    tolerance = float(params["residual_tolerance"])
    passed = all(
        len(row["panel_a_normal"]["eigenvalues"]) == 8
        and len(row["panel_b_larger_superradiant"]["eigenvalues"]) == 8
        and len(row["panel_c_smaller_superradiant"]["eigenvalues"]) == 8
        and row["panel_b_larger_superradiant"]["fixed_point_residual"] <= tolerance
        and row["panel_c_smaller_superradiant"]["fixed_point_residual"] <= tolerance
        for row in rows
    )
    result = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "target_id": "T005",
        "mode": "reduced_printed_equation_stability_attestation",
        "status": "passed" if passed else "failed",
        "panel_records": rows,
        "paper_discrepancy_preserved": True,
        "scientific_coverage_promoted": False,
        "acceptance_criteria": params["acceptance_criteria"],
    }
    data_path = output_root / "data" / "stability_implementation_closure" / "T005.json"
    check_path = output_root / "checks" / "stability_implementation_closure" / "T005.json"
    manifest_path = (
        output_root / "checks" / "stability_implementation_closure" / "manifest.json"
    )
    _write_json(data_path, result)
    _write_json(
        check_path,
        {
            "target_id": "T005",
            "status": result["status"],
            "mode": result["mode"],
            "paper_discrepancy_preserved": True,
            "scientific_coverage_promoted": False,
            "acceptance_criteria": params["acceptance_criteria"],
        },
    )
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_scale": config["campaign_scale"],
        "status": result["status"],
        "target_ids": ["T005"],
        "clean_room_boundary": boundary,
        "paper_discrepancy_preserved": True,
        "scientific_coverage_promoted": False,
    }
    _write_json(manifest_path, manifest)
    return manifest
