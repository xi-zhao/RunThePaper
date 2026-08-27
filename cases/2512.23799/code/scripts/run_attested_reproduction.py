#!/usr/bin/env python3
"""Run the case-owned Steane and sampling checks without paper artifacts.

The runner deliberately uses an independently declared p-grid.  It never reads
the paper, source figures, digitized reference curves, or author numerical
artifacts.  Reference comparison is a separate post-run operation.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

import magic_state_simulation as proxy  # noqa: E402
import steane_h_prep as steane  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        help="Workspace-relative JSON configuration under config/.",
    )
    return parser.parse_args()


def _parameter_path(config_ref: str | None) -> Path:
    value = config_ref or os.environ.get(
        "PRAGENT_PARAMETER_FILE",
        "config/independent_reproduction.json",
    )
    path = Path(value)
    if not path.is_absolute():
        if ".." in path.parts or path.parts[:1] != ("config",):
            raise ValueError(
                f"configuration must be workspace-relative under config/: {value!r}"
            )
        path = WORKSPACE / path
    return path


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _is_nonincreasing(
    values: list[float], errors: list[float], sigma: float = 2.0
) -> bool:
    return all(
        next_value <= value + sigma * (error + next_error)
        for value, next_value, error, next_error in zip(
            values, values[1:], errors, errors[1:]
        )
    )


def _is_nondecreasing(
    values: list[float], errors: list[float], sigma: float = 2.0
) -> bool:
    return all(
        next_value + sigma * (error + next_error) >= value
        for value, next_value, error, next_error in zip(
            values, values[1:], errors, errors[1:]
        )
    )


def main() -> int:
    args = _parse_args()
    parameter_path = _parameter_path(args.config)
    parameters = json.loads(parameter_path.read_text(encoding="utf-8"))["model"]
    boundary = parameters["scientific_boundary"]
    if any(
        boundary[key]
        for key in (
            "author_code_used",
            "author_numeric_arrays_used",
            "source_pixels_used_as_numerical_inputs",
            "reference_curves_read_by_runner",
        )
    ):
        raise RuntimeError("forbidden numerical input declared in the run configuration")

    steane_cfg = parameters["steane"]
    steane.set_protocol_config(
        steane_cfg["stab_schedule"],
        steane_cfg["idle_policy"],
        steane_cfg["encoding"],
    )
    steane_rows = [
        steane.run_point(
            float(p),
            int(steane_cfg["shots_per_point"]),
            int(steane_cfg["seed"]) + index,
        )
        for index, p in enumerate(steane_cfg["p_grid"])
    ]

    proxy_cfg = parameters["proxy"]
    protocol = proxy.ToyProtocol(
        error_locations=int(proxy_cfg["error_locations"]),
        undetected_probability=float(proxy_cfg["undetected_probability"]),
        logical_error_per_undetected_error=float(
            proxy_cfg["logical_error_per_undetected_error"]
        ),
        shots=int(proxy_cfg["shots"]),
        seed=int(proxy_cfg["seed"]),
    )
    proxy_grid = np.asarray(proxy_cfg["p_grid"], dtype=float)
    runtime_rows = proxy.runtime_proxy(proxy_grid, protocol)
    sampling_rows, sampling_slope = proxy.sampling_scaling(
        p=float(proxy_cfg["sampling_p"]),
        protocol=protocol,
        shot_counts=proxy_cfg["sampling_shot_counts"],
        repeats=int(proxy_cfg["sampling_repeats"]),
    )

    steane_path = WORKSPACE / "outputs" / "data" / "attested_steane_subset.csv"
    runtime_path = WORKSPACE / "outputs" / "data" / "attested_runtime_proxy.csv"
    sampling_path = WORKSPACE / "outputs" / "data" / "attested_sampling_scaling.csv"
    _write_csv(steane_path, steane_rows)
    _write_csv(runtime_path, runtime_rows)
    _write_csv(sampling_path, sampling_rows)

    noiseless = steane.run_point(0.0, 32, int(steane_cfg["seed"]))
    acceptance_values = [float(row["acceptance_rate"]) for row in steane_rows]
    infidelity_values = [float(row["infidelity"]) for row in steane_rows]
    acceptance_errors = [float(row["acceptance_se"]) for row in steane_rows]
    infidelity_errors = [float(row["infidelity_se"]) for row in steane_rows]
    low_p_runtime = min(runtime_rows, key=lambda row: abs(float(row["p"]) - 1e-3))
    gates = {
        "noiseless_acceptance_is_one": noiseless["acceptance_rate"] == 1.0,
        "noiseless_infidelity_is_zero": noiseless["infidelity"] == 0.0,
        "acceptance_statistically_nonincreasing": _is_nonincreasing(
            acceptance_values, acceptance_errors
        ),
        "infidelity_statistically_nondecreasing": _is_nondecreasing(
            infidelity_values, infidelity_errors
        ),
        "local_runtime_proxy_exceeds_tenfold_at_p_1e_minus_3": float(
            low_p_runtime["speedup_ratio"]
        )
        > 10.0,
        "sampling_slope_close_to_minus_half": abs(float(sampling_slope) + 0.5) < 0.15,
    }
    summary = {
        "schema_version": 1,
        "status": "passed" if all(gates.values()) else "failed",
        "paper_id": "2512.23799",
        "target_ids": ["T001", "T002", "T003", "T004"],
        "scientific_boundary": boundary,
        "steane_configuration": steane_cfg,
        "proxy_configuration": proxy_cfg,
        "gates": gates,
        "sampling_loglog_slope": float(sampling_slope),
        "runtime_proxy_speedup_at_p_1e_minus_3": float(low_p_runtime["speedup_ratio"]),
        "interpretation": {
            "T001": "real clean-room attempt; exact paper curve remains unidentifiable from public inputs",
            "T002": "acceptance trend and physical scale reproduced on an independently declared grid",
            "T003": "local method proxy only; not the authors' absolute wall-clock benchmark",
            "T004": "published inverse-square-root sampling law reproduced numerically",
        },
        "outputs": [
            "outputs/data/attested_steane_subset.csv",
            "outputs/data/attested_runtime_proxy.csv",
            "outputs/data/attested_sampling_scaling.csv",
        ],
    }
    _write_json(WORKSPACE / "outputs" / "checks" / "attested_science_checks.json", summary)
    print(json.dumps({"status": summary["status"], "gates": gates}, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
