"""Clean-room implementation contract for the two T004 spectrum panels.

The campaign evaluates the printed one-photon mean-field fixed points and
Bogoliubov matrix on a frozen coupling grid.  Runtime inputs contain only the
paper parameters and numerical acceptance tolerances; paper files, source
figures, author code, author arrays, and prior outputs are not numerical inputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .dicke import critical_coupling, one_photon_stability_scan


TARGET_ID = "T004"
ITEM_IDS = (
    "Formal Fig. S1 / arXiv v1 Fig. 5(a)",
    "Formal Fig. S1 / arXiv v1 Fig. 5(b)",
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _serialized_spectrum(values: np.ndarray) -> list[dict[str, float]]:
    ordered = sorted(
        np.asarray(values, dtype=np.complex128),
        key=lambda value: (float(value.real), float(value.imag)),
    )
    return [{"real": float(value.real), "imag": float(value.imag)} for value in ordered]


def _validate_boundary(config: dict[str, Any]) -> None:
    declared = tuple(config.get("attestation_parameters", {}).get("target_ids", ()))
    if declared != (TARGET_ID,):
        raise ValueError("campaign target_ids must contain exactly T004")
    items = tuple(config.get("target", {}).get("item_ids", ()))
    if items != ITEM_IDS:
        raise ValueError("T004 must map the two frozen Fig. S1 denominator items exactly once")
    boundary = config.get("clean_room_boundary")
    if not isinstance(boundary, dict):
        raise ValueError("clean_room_boundary must be an object")
    for name in (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
        "prior_outputs_used_as_numeric_inputs",
    ):
        if boundary.get(name) is not False:
            raise ValueError(f"clean-room boundary must set {name}=false")


def spectrum_records(target: dict[str, Any]) -> dict[str, Any]:
    """Evaluate both T004 panels directly from the frozen equations."""

    model = target.get("model")
    grid = target.get("coupling_grid")
    acceptance = target.get("acceptance")
    if not all(isinstance(value, dict) for value in (model, grid, acceptance)):
        raise ValueError("target.model, coupling_grid, and acceptance must be objects")
    omega_c = float(model["omega_c"])
    omega_a = float(model["omega_a"])
    kappa1 = float(model["kappa1"])
    start = float(grid["start"])
    stop = float(grid["stop"])
    points = int(grid["points"])
    if not all(np.isfinite(value) and value > 0.0 for value in (omega_c, omega_a, kappa1)):
        raise ValueError("omega_c, omega_a, and kappa1 must be finite and positive")
    if not np.isfinite(start) or not np.isfinite(stop) or start >= stop or points < 3:
        raise ValueError("coupling_grid must have finite start < stop and at least three points")

    couplings = np.linspace(start, stop, points)
    result = one_photon_stability_scan(
        couplings,
        omega_c=omega_c,
        omega_a=omega_a,
        kappa1=kappa1,
    )
    zero_tolerance = float(acceptance["zero_mode_tolerance"])
    normal_tolerance = float(acceptance["normal_real_tolerance"])
    super_minimum = float(acceptance["superradiant_min_positive_real"])
    rows: list[dict[str, Any]] = []
    normal_nonexpanding = True
    superradiant_positive = True
    superradiant_points = 0
    for index, coupling in enumerate(couplings):
        normal = np.asarray(result["normal"][index], dtype=np.complex128)
        normal_nonneutral = normal[np.abs(normal) > zero_tolerance]
        normal_largest = float(np.max(normal_nonneutral.real, initial=-np.inf))
        superradiant = np.asarray(result["superradiant"][index], dtype=np.complex128)
        superradiant_exists = bool(np.all(np.isfinite(superradiant)))
        superradiant_largest: float | None = None
        superradiant_spectrum: list[dict[str, float]] | None = None
        if superradiant_exists:
            superradiant_points += 1
            superradiant_largest = float(np.max(superradiant.real))
            superradiant_spectrum = _serialized_spectrum(superradiant)
            superradiant_positive &= superradiant_largest >= super_minimum
        normal_nonexpanding &= normal_largest <= normal_tolerance
        rows.append(
            {
                "lambda": float(coupling),
                "panel_a_normal": {
                    "largest_non_neutral_real_part": normal_largest,
                    "eigenvalues": _serialized_spectrum(normal),
                },
                "panel_b_superradiant": {
                    "exists": superradiant_exists,
                    "largest_real_part": superradiant_largest,
                    "eigenvalues": superradiant_spectrum,
                },
            }
        )

    threshold = critical_coupling(omega_c, kappa1)
    checks = {
        "full_frozen_grid_evaluated": len(rows) == points,
        "six_modes_per_normal_point": all(
            len(row["panel_a_normal"]["eigenvalues"]) == 6 for row in rows
        ),
        "normal_branch_nonexpanding": normal_nonexpanding,
        "superradiant_points_present": superradiant_points > 0,
        "superradiant_branch_has_positive_mode": superradiant_positive,
        "threshold_inside_scan": start < threshold < stop,
    }
    return {
        "schema_version": 1,
        "target_id": TARGET_ID,
        "item_ids": list(ITEM_IDS),
        "mode": "paper_parameter_printed_equation_bogoliubov_scan",
        "model": {"omega_c": omega_c, "omega_a": omega_a, "kappa1": kappa1},
        "coupling_grid": {"start": start, "stop": stop, "points": points},
        "critical_coupling": threshold,
        "superradiant_points": superradiant_points,
        "checks": checks,
        "status": "passed" if all(checks.values()) else "failed",
        "scientific_coverage_promoted": False,
        "panel_records": rows,
    }


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    _validate_boundary(config)
    result = spectrum_records(config["target"])
    data_path = output_root / "data" / "t004_bogoliubov_closure" / "T004.json"
    check_path = output_root / "checks" / "t004_bogoliubov_closure" / "T004.json"
    manifest_path = output_root / "checks" / "t004_bogoliubov_closure" / "manifest.json"
    _write_json(data_path, result)
    _write_json(
        check_path,
        {
            "schema_version": 1,
            "target_id": TARGET_ID,
            "item_ids": list(ITEM_IDS),
            "status": result["status"],
            "mode": result["mode"],
            "checks": result["checks"],
            "scientific_coverage_promoted": False,
        },
    )
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "target_ids": [TARGET_ID],
        "item_ids": list(ITEM_IDS),
        "status": result["status"],
        "campaign_scale": config["campaign_scale"],
        "clean_room_boundary": config["clean_room_boundary"],
        "scientific_coverage_promoted": False,
    }
    _write_json(manifest_path, manifest)
    return manifest
