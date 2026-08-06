#!/usr/bin/env python3
"""Diagnose cutoff-dependent runaway with one-photon loss only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from src.dicke import trajectory_density


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        parameters = json.load(handle)["parameters"]

    started = time.monotonic()
    lambdas = np.asarray(parameters["lambdas"], dtype=float)
    cutoffs = np.asarray(parameters["cutoffs"], dtype=int)
    means = np.empty((cutoffs.size, lambdas.size))
    spin_z = np.empty_like(means)
    tails = np.empty_like(means)
    arrays: dict[str, np.ndarray] = {"lambda": lambdas, "cutoff": cutoffs}
    records: list[dict[str, object]] = []
    for cutoff_index, cutoff in enumerate(cutoffs):
        for lambda_index, coupling in enumerate(lambdas):
            job_started = time.monotonic()
            result = trajectory_density(
                int(parameters["N"]),
                int(cutoff),
                float(coupling),
                omega_c=float(parameters["omega_c"]),
                omega_a=float(parameters["omega_a"]),
                kappa1=float(parameters["kappa1"]),
                kappa2=float(parameters["kappa2"]),
                final_time=float(parameters["final_time"]),
                trajectories=int(parameters["trajectories"]),
                seed=int(parameters["seed_base"]) + 100 * cutoff_index + lambda_index,
            )
            means[cutoff_index, lambda_index] = float(result["photon_mean"])
            spin_z[cutoff_index, lambda_index] = float(result["spin_z_mean"])
            tails[cutoff_index, lambda_index] = float(result["photon_tail"])
            label = f"M{cutoff}_l{coupling:.2f}".replace(".", "p")
            arrays[f"{label}_fock"] = np.asarray(result["fock_distribution"])
            records.append(
                {
                    "N": int(parameters["N"]),
                    "M": int(cutoff),
                    "lambda": float(coupling),
                    "photon_mean": float(result["photon_mean"]),
                    "spin_z_mean": float(result["spin_z_mean"]),
                    "photon_tail": float(result["photon_tail"]),
                    "trace_error": float(result["trace_error"]),
                    "runtime_seconds": time.monotonic() - job_started,
                }
            )
            print(
                f"M={cutoff}, lambda={coupling:.2f}: n={result['photon_mean']:.3g}, "
                f"tail={result['photon_tail']:.3g}",
                flush=True,
            )
    arrays["photon_mean"] = means
    arrays["spin_z_mean"] = spin_z
    arrays["photon_tail"] = tails
    output_data = Path("outputs/data")
    output_checks = Path("outputs/checks")
    output_data.mkdir(parents=True, exist_ok=True)
    output_checks.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_data / "fig2_quantum.npz", **arrays)

    target_index = int(np.argmin(abs(lambdas - 1.25)))
    target_means = means[:, target_index]
    target_tails = tails[:, target_index]
    science = {
        "lambda": float(lambdas[target_index]),
        "cutoffs": cutoffs.tolist(),
        "photon_means": target_means.tolist(),
        "cutoff_tail_probabilities": target_tails.tolist(),
        "cutoff_dependence_range": float(np.ptp(target_means)),
        "runaway_evidence": bool(np.ptp(target_means) > 3 or np.max(target_tails) > 0.02),
        "method_variant": "finite-time quantum trajectories; paper uses truncated-Liouvillian steady states",
        "interpretation": "cutoff-sensitive finite-time occupation is the reproduced instability signal, not a claimed converged NESS",
    }
    with (output_checks / "fig2_quantum_science.json").open("w", encoding="utf-8") as handle:
        json.dump(science, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    summary = {
        "schema_version": 1,
        "paper_id": "2412.14271",
        "method": "finite-time Monte-Carlo unraveling of the printed one-photon-loss master equation",
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_numeric_data_used": False,
        "parameters": parameters,
        "runtime_seconds": time.monotonic() - started,
        "jobs": records,
        "fidelity": {
            "level": "feature_reproduced_candidate",
            "paper_exact": False,
            "reason": "finite-time trajectories replace prohibitively costly steady-state ED at M=60,80,100",
        },
    }
    with (output_data / "fig2_quantum_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
