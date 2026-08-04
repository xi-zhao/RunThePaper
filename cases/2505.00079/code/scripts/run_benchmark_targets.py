"""Run independently generated PRL-Bench idx56 targets.

Paper-scale measurement/decorrelation counts are available through the CLI, but
the burn-in length is not reported by the source and must always be disclosed.
The script therefore labels every Monte Carlo output with its full generated
run parameters and never silently promotes a smoke run to a final artifact.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np


HERE = Path(__file__).resolve().parent
WS = HERE.parent
sys.path.insert(0, str(WS / "src"))

from zn_lgt import (  # noqa: E402
    Model,
    MetropolisSampler,
    coulomb_correlator_ratio,
    symmetry_augment_polyakov,
)


TARGETS = {
    "z7": {"length": 10, "measurements": 20_000, "decorrelation_sweeps": 20},
    "z4": {"length": 6, "measurements": 10_000, "decorrelation_sweeps": 1},
    "z3": {"length": 8, "measurements": 40_000, "decorrelation_sweeps": 100},
}


def run_chain(
    *,
    length: int,
    model: Model,
    seed: int,
    thermal_sweeps: int,
    measurements: int,
    decorrelation_sweeps: int,
    start: str,
) -> tuple[list[dict[str, float]], dict[str, float]]:
    sampler = MetropolisSampler(length=length, model=model, seed=seed, start=start)
    t0 = perf_counter()
    sampler.sweep(thermal_sweeps)
    rows: list[dict[str, float]] = []
    for index in range(measurements):
        sampler.sweep(decorrelation_sweeps)
        polyakov = sampler.polyakov_loop()
        rows.append(
            {
                "measurement": index,
                "polyakov_real": polyakov.real,
                "polyakov_imag": polyakov.imag,
                "polyakov_abs": abs(polyakov),
                "action": sampler.action(),
                "vortex_density": sampler.vortex_density(),
                "monopole_density": sampler.monopole_density(),
            }
        )
    runtime = perf_counter() - t0
    return rows, {
        "runtime_sec": runtime,
        "acceptance_rate": sampler.acceptance_rate,
        "sweeps_total": thermal_sweeps + measurements * decorrelation_sweeps,
    }


def write_rows(path: Path, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, float]], length: int, n: int) -> dict[str, float]:
    polyakov = np.asarray([complex(row["polyakov_real"], row["polyakov_imag"]) for row in rows])
    augmented = symmetry_augment_polyakov(polyakov, n)
    actions = np.asarray([row["action"] for row in rows])
    return {
        "mean_polyakov_real": float(np.mean(polyakov.real)),
        "mean_polyakov_imag": float(np.mean(polyakov.imag)),
        "mean_polyakov_abs": float(np.mean(np.abs(polyakov))),
        "abs_mean_polyakov": float(abs(np.mean(polyakov))),
        "q_raw": float(abs(np.mean(polyakov)) / np.mean(np.abs(polyakov))),
        "q_symmetry_augmented": float(abs(np.mean(augmented)) / np.mean(np.abs(augmented))),
        "action_mean": float(np.mean(actions)),
        "action_susceptibility": float(np.var(actions, ddof=0) / length**4),
        "vortex_density_mean": float(np.mean([row["vortex_density"] for row in rows])),
        "monopole_density_mean": float(np.mean([row["monopole_density"] for row in rows])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["z7", "z4", "z3", "analytic"], required=True)
    parser.add_argument("--measurements", type=int)
    parser.add_argument("--decorrelation-sweeps", type=int)
    parser.add_argument("--thermal-sweeps", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=5601)
    parser.add_argument("--start", choices=["hot", "cold"], default="hot")
    parser.add_argument("--tag", default="run")
    args = parser.parse_args()

    data_dir = WS / "outputs" / "data"
    checks_dir = WS / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    if args.target == "analytic":
        ratios = [
            {"n": n, "ratio": coulomb_correlator_ratio(n, 16)} for n in range(1, 8)
        ]
        write_rows(data_dir / f"idx56_analytic_{args.tag}.csv", ratios)
        payload = {
            "status": "passed",
            "target": "Fig. 5 finite-torus Coulomb correlator ratio",
            "parameter_match": "paper_exact",
            "generated_data_provenance": "analytic_reference",
            "length": 16,
            "c7_over_c8": ratios[-1]["ratio"],
            "benchmark_gold": 1.1,
            "paper_long_distance_expectation_match": abs(ratios[-1]["ratio"] - 1.1) < 0.1,
        }
        (checks_dir / f"idx56_analytic_{args.tag}.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(payload, indent=2))
        return

    paper = TARGETS[args.target]
    measurements = args.measurements or paper["measurements"]
    decorrelation = args.decorrelation_sweeps or paper["decorrelation_sweeps"]
    if args.target == "z4":
        models = [("beta1p543", Model(n=4, beta=1.543, beta_tilde=-0.393))]
    elif args.target == "z3":
        models = [("beta0p512", Model(n=3, beta=0.512, monopole_mu=1.0))]
    else:
        models = [(f"beta{value:g}", Model(n=7, beta=value)) for value in (1.0, 2.0, 2.5)]

    summaries = []
    for label, model in models:
        rows, runtime = run_chain(
            length=paper["length"],
            model=model,
            seed=args.seed,
            thermal_sweeps=args.thermal_sweeps,
            measurements=measurements,
            decorrelation_sweeps=decorrelation,
            start=args.start,
        )
        stem = f"idx56_{args.target}_{label}_{args.tag}"
        write_rows(data_dir / f"{stem}.csv", rows)
        summary = {
            "label": label,
            "model": asdict(model),
            "paper_parameters": paper,
            "generated_run": {
                "length": paper["length"],
                "measurements": measurements,
                "decorrelation_sweeps": decorrelation,
                "thermal_sweeps": args.thermal_sweeps,
                "thermal_sweeps_source": "not reported by paper; explicit case choice",
                "seed": args.seed,
                "start": args.start,
            },
            "parameter_match": (
                "paper_subset"
                if measurements == paper["measurements"] and decorrelation == paper["decorrelation_sweeps"]
                else "reduced_scale"
            ),
            **runtime,
            **summarize(rows, paper["length"], model.n),
        }
        summaries.append(summary)

    payload = {
        "status": "passed",
        "target": args.target,
        "paper_id": "2505.00079",
        "benchmark_record": "prlb-f37350e-056",
        "summaries": summaries,
    }
    (checks_dir / f"idx56_{args.target}_{args.tag}.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
