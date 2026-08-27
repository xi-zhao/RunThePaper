"""Source-blind, reduced-cost execution proof for all implemented targets.

This runner exercises the same capacity, NMSE, and spectral code used by the
paper-scale campaign.  Its reduced dimensions prove implementation closure;
they do not replace the frozen paper-scale scientific outputs.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import run_figS1  # noqa: E402
import run_nmse  # noqa: E402
import run_scan  # noqa: E402
from mackey_glass import generate_mg_sequences  # noqa: E402
from qrc_engine import cluster_hamiltonian, tfim_hamiltonian  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty probe output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _capacity_probe(config: dict[str, Any]) -> list[dict[str, Any]]:
    run_scan.N_WASH = int(config["n_wash"])
    run_scan.N_EVAL = int(config["n_eval"])
    rows: list[dict[str, Any]] = []
    for job in config["jobs"]:
        row = run_scan.run_one(
            (
                job["model"],
                float(job["parameter"]),
                int(job["realization"]),
                int(config["n_seq"]),
                int(job["seed"]),
            )
        )
        rows.append(row)
    return rows


def _nmse_probe(config: dict[str, Any]) -> list[dict[str, Any]]:
    run_nmse.N_WASH = int(config["n_wash"])
    run_nmse.N_TRAIN = int(config["n_train"])
    run_nmse.N_TEST = int(config["n_test"])
    rows: list[dict[str, Any]] = []
    for job in config["jobs"]:
        row = run_nmse.run_one(
            (
                job["model"],
                float(job["parameter"]),
                int(job["realization"]),
                int(config["n_seq"]),
                int(job["seed"]),
            )
        )
        rows.append(row)
    return rows


def _spectral_probe(config: dict[str, Any]) -> list[dict[str, Any]]:
    sequences = generate_mg_sequences(
        int(config["n_seq"]),
        int(config["n_samples"]),
        seed=int(config["seed"]),
    )
    omegas = np.linspace(0.02, 3.0, int(config["omega_points"]))
    g_factor = run_figS1.g_factor_binned(
        sequences,
        omegas,
        n_wash=min(20, int(config["n_samples"]) // 4),
        n_bins=8,
    )
    rows = [
        {
            "record_kind": "g_factor",
            "parameter": float(omega),
            "minimum": float(value),
            "maximum": float(value),
            "samples": int(config["n_seq"]),
        }
        for omega, value in zip(omegas, g_factor)
    ]
    for j_index, coupling in enumerate(
        np.logspace(-1, 2, int(config["j_points"]))
    ):
        spectra = []
        for realization in range(int(config["tfim_realizations"])):
            rng = np.random.default_rng(50_000 + 977 * j_index + realization)
            spectra.append(np.linalg.eigvalsh(tfim_hamiltonian(6, float(coupling), rng)))
        mean_spectrum = np.mean(spectra, axis=0)
        rows.append(
            {
                "record_kind": "tfim_spectrum",
                "parameter": float(coupling),
                "minimum": float(mean_spectrum[0]),
                "maximum": float(mean_spectrum[-1]),
                "samples": int(config["tfim_realizations"]),
            }
        )
    for alpha in np.linspace(0.0, 1.0, int(config["alpha_points"])):
        spectrum = np.linalg.eigvalsh(cluster_hamiltonian(6, float(alpha)))
        rows.append(
            {
                "record_kind": "cluster_spectrum",
                "parameter": float(alpha),
                "minimum": float(spectrum[0]),
                "maximum": float(spectrum[-1]),
                "samples": 1,
            }
        )
    return rows


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.config.read_text(encoding="utf-8"))
    parameters = payload["parameters"]
    output_root = WORKSPACE / "outputs"
    data_dir = output_root / "data" / "implementation_probe"
    checks_dir = output_root / "checks" / "implementation_probe"

    capacity = _capacity_probe(parameters["capacity"])
    nmse = _nmse_probe(parameters["nmse"])
    spectral = _spectral_probe(parameters["spectral"])
    tolerance = float(parameters["identity_tolerance"])
    capacity_ok = all(
        np.isfinite(float(row["identity_residual_max"]))
        and float(row["identity_residual_max"]) <= tolerance
        for row in capacity
    )
    nmse_ok = all(
        np.isfinite(float(row[key])) and float(row[key]) >= 0.0
        for row in nmse
        for key in ("nmse_h1", "nmse_h2", "nmse_h3")
    )
    spectral_ok = all(
        np.isfinite(float(row["minimum"]))
        and np.isfinite(float(row["maximum"]))
        and float(row["maximum"]) >= float(row["minimum"])
        for row in spectral
    )

    _write_csv(data_dir / "capacity_smoke.csv", capacity)
    _write_csv(data_dir / "nmse_smoke.csv", nmse)
    _write_csv(data_dir / "spectral_smoke.csv", spectral)
    summary = {
        "schema_version": 1,
        "paper_id": payload["paper_id"],
        "profile": parameters["profile"],
        "status": "passed" if capacity_ok and nmse_ok and spectral_ok else "failed",
        "target_results": {
            "T001": {"status": "passed" if capacity_ok and nmse_ok else "failed"},
            "T002": {"status": "passed" if spectral_ok else "failed"},
            "T003": {"status": "passed" if capacity_ok and nmse_ok else "failed"},
        },
        "checks": {
            "thermodynamic_identity": capacity_ok,
            "nmse_finite_nonnegative": nmse_ok,
            "spectra_finite_ordered": spectral_ok,
        },
        "generated_data_provenance": "independent_numerics",
        "scientific_role": "implementation_smoke_only",
        "paper_scale_outputs_replaced": False,
    }
    checks_dir.mkdir(parents=True, exist_ok=True)
    (checks_dir / "implementation_probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
