"""Isolated paper-exact execution for every Wigner-theory target.

The runner consumes only a frozen JSON configuration and the independently
derived density-matrix implementation. It intentionally has no paper, raw,
reference-image, author-array, or author-code input path.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .wigner_model import physical_checks, scan_target


TARGET_STEMS = {
    "T-FIG003": "fig003_theory",
    "T-FIG004": "fig004_theory",
    "T-FIG005A": "fig005a_theory",
    "T-FIG005B": "fig005b_theory",
}


def _write_csv(path: Path, result: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["angle_deg", "p_ab", "p_bc", "p_ac", "wigner", "w_limit"])
        writer.writerows(
            zip(
                result.angle_deg,
                result.p_ab,
                result.p_bc,
                result.p_ac,
                result.wigner,
                result.w_limit,
                strict=True,
            )
        )


def run_bundle(config_path: Path, output_root: Path) -> dict[str, Any]:
    """Run all declared targets and return a compact machine summary."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "2606.30255":
        raise ValueError("configuration paper_id must be 2606.30255")
    targets = config.get("targets")
    if not isinstance(targets, dict) or set(targets) != set(TARGET_STEMS):
        raise ValueError("configuration must declare exactly the four theory targets")

    results: dict[str, dict[str, Any]] = {}
    for target_id, stem in TARGET_STEMS.items():
        params = targets[target_id]
        scan = scan_target(target_id, params)
        checks = physical_checks(scan)
        if checks["status"] != "passed":
            raise AssertionError(f"smoke checks failed for {target_id}: {checks}")

        data_path = output_root / "data" / "isolated_reproduction" / f"{stem}.csv"
        check_path = output_root / "checks" / "isolated_reproduction" / f"{stem}.json"
        _write_csv(data_path, scan)
        check_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "paper_id": "2606.30255",
            "target_id": target_id,
            "status": "passed",
            "artifact_stage": "final_reproduction",
            "parameter_match": "paper_exact",
            "generated_data_provenance": "independent_numerics",
            "parameters": params,
            "checks": checks["assertions"],
            "metrics": checks["metrics"],
            "outputs": {
                "data": data_path.as_posix(),
                "check": check_path.as_posix(),
            },
            "forbidden_scientific_inputs": [],
        }
        check_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        results[target_id] = {
            "status": "passed",
            "rows": int(scan.angle_deg.size),
        }

    return {
        "schema_version": 1,
        "paper_id": "2606.30255",
        "status": "passed",
        "mode": config.get("mode"),
        "targets": results,
    }
