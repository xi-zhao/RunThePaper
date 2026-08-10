"""Generate Main Fig. 2 from independent formula-derived arrays."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .model import SETUPS, maximum_table_residual, table_coefficients


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_arrays(parameters: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    phi = np.linspace(
        float(parameters["phi_min"]),
        float(parameters["phi_max"]),
        int(parameters["phi_points"]),
        dtype=np.float64,
    )
    gamma = float(parameters["gamma"])
    return phi, {
        ordering: table_coefficients(ordering, phi, gamma=gamma)
        for ordering in SETUPS
    }


def write_dataset(path: Path, phi: np.ndarray, coefficients: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["phi", "phi_over_pi"]
    for ordering in SETUPS:
        fields.extend(
            [
                f"{ordering}_g",
                f"{ordering}_gamma_a",
                f"{ordering}_gamma_b",
                f"{ordering}_gamma_coll",
            ]
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index, phase in enumerate(phi):
            row: dict[str, float] = {
                "phi": float(phase),
                "phi_over_pi": float(phase / np.pi),
            }
            for ordering in SETUPS:
                values = coefficients[ordering]
                row[f"{ordering}_g"] = float(values.exchange[index])
                row[f"{ordering}_gamma_a"] = float(values.individual_a[index])
                row[f"{ordering}_gamma_b"] = float(values.individual_b[index])
                row[f"{ordering}_gamma_coll"] = float(values.collective[index])
            writer.writerow({key: format(value, ".17g") for key, value in row.items()})


def scientific_checks(phi: np.ndarray, coefficients: dict[str, Any], gamma: float) -> dict[str, Any]:
    middle = int(np.argmin(np.abs(phi - np.pi / 2.0)))
    braided = coefficients["abab"]
    separate = coefficients["aabb"]
    nested = coefficients["abba"]
    table_residual = maximum_table_residual(phi, gamma=gamma)
    checks = {
        "general_sum_matches_table": {
            "passed": table_residual < 1.0e-12,
            "max_abs_residual": table_residual,
            "tolerance": 1.0e-12,
        },
        "braided_decoherence_free_interaction": {
            "passed": bool(
                abs(float(braided.individual_a[middle])) < 1.0e-12
                and abs(float(braided.individual_b[middle])) < 1.0e-12
                and abs(float(braided.collective[middle])) < 1.0e-12
                and abs(float(braided.exchange[middle]) - gamma) < 1.0e-12
            ),
            "phi": float(phi[middle]),
            "g": float(braided.exchange[middle]),
            "gamma_a": float(braided.individual_a[middle]),
            "gamma_b": float(braided.individual_b[middle]),
            "gamma_coll": float(braided.collective[middle]),
        },
        "unbraided_zero_decay_forces_zero_exchange": {
            "passed": bool(
                max(
                    abs(float(separate.exchange[-1])),
                    abs(float(separate.individual_a[-1])),
                    abs(float(separate.individual_b[-1])),
                    abs(float(separate.collective[-1])),
                    abs(float(nested.exchange[-1])),
                    abs(float(nested.individual_a[-1])),
                    abs(float(nested.individual_b[-1])),
                    abs(float(nested.collective[-1])),
                )
                < 2.0e-12
            ),
            "phi": float(phi[-1]),
        },
        "individual_rates_nonnegative": {
            "passed": all(
                float(np.min(values.individual_a)) >= -1.0e-12
                and float(np.min(values.individual_b)) >= -1.0e-12
                for values in coefficients.values()
            ),
            "tolerance": 1.0e-12,
        },
    }
    return {
        "schema_version": 1,
        "paper_id": "1711.08863",
        "target_id": "T001",
        "status": "passed" if all(item["passed"] for item in checks.values()) else "failed",
        "checks": checks,
    }


def run_reproduction(config_path: Path) -> None:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    phi, coefficients = build_arrays(parameters)

    output_data = Path("outputs/data/main_fig2_coefficients.csv")
    output_check = Path("outputs/checks/target_checks.json")
    output_manifest = Path("outputs/checks/generated_data_manifest.json")
    write_dataset(output_data, phi, coefficients)
    _write_json(output_check, scientific_checks(phi, coefficients, float(parameters["gamma"])))

    model_path = Path("src/giant_atoms/model.py")
    manifest = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": "1711.08863",
        "run_id": config["run_id"],
        "generated_data_provenance": "independent_formula_numerics",
        "source_pixels_read": False,
        "author_code_used": False,
        "author_arrays_used": False,
        "artifacts": {
            "config": {"path": str(config_path), "sha256": _sha256(config_path)},
            "model": {"path": str(model_path), "sha256": _sha256(model_path)},
            "dataset": {"path": str(output_data), "sha256": _sha256(output_data)},
            "scientific_check": {"path": str(output_check), "sha256": _sha256(output_check)},
        },
    }
    _write_json(output_manifest, manifest)
