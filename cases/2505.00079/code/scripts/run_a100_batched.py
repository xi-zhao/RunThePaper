"""Run resumable batched Z_N chains on CUDA and emit monitorable progress.

The batch dimension represents independent, separately thermalized chains. The
paper's per-chain structure is not reported, so outputs are labelled
``paper_total_measurements_batched_chains`` rather than ``paper_exact``.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, time

import numpy as np
import torch


HERE = Path(__file__).resolve().parent
WS = HERE.parent
sys.path.insert(0, str(WS / "src"))

from torch_zn_lgt import BatchedMetropolisSampler, TorchModel  # noqa: E402


TARGETS = {
    "z7": {
        "length": 10,
        "measurements": 20_000,
        "decorrelation_sweeps": 20,
        "models": [("beta1", TorchModel(7, 1.0)), ("beta2", TorchModel(7, 2.0)), ("beta2p5", TorchModel(7, 2.5))],
        "defects": True,
    },
    "z4": {
        "length": 6,
        "measurements": 10_000,
        "decorrelation_sweeps": 1,
        "models": [("beta1p543", TorchModel(4, 1.543, beta_tilde=-0.393))],
        "defects": False,
    },
    "z3": {
        "length": 8,
        "measurements": 40_000,
        "decorrelation_sweeps": 100,
        "models": [("beta0p512", TorchModel(3, 0.512, monopole_mu=1.0))],
        "defects": False,
    },
}


DTYPE = np.dtype(
    [
        ("sample", "<i8"),
        ("chain", "<i4"),
        ("measurement_in_chain", "<i8"),
        ("polyakov_real", "<f8"),
        ("polyakov_imag", "<f8"),
        ("action", "<f8"),
        ("vortex_density", "<f8"),
        ("monopole_density", "<f8"),
    ]
)


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def checkpoint(
    *,
    sampler: BatchedMetropolisSampler,
    state_path: Path,
    meta_path: Path,
    rows: np.memmap,
    completed_batches: int,
    completed_samples: int,
    elapsed_sec: float,
) -> None:
    rows.flush()
    temporary = state_path.with_suffix(state_path.suffix + ".tmp")
    torch.save(
        {
            "links": sampler.links.detach().cpu(),
            "generator_state": sampler.generator.get_state().cpu(),
            "proposed": sampler.proposed,
            "accepted": sampler.accepted,
        },
        temporary,
    )
    os.replace(temporary, state_path)
    atomic_json(
        meta_path,
        {
            "completed_batches": completed_batches,
            "completed_samples": completed_samples,
            "elapsed_sec": elapsed_sec,
            "updated_unix": time(),
        },
    )


def restore(
    sampler: BatchedMetropolisSampler, state_path: Path, meta_path: Path
) -> tuple[int, int, float]:
    state = torch.load(state_path, map_location="cpu", weights_only=True)
    sampler.links = state["links"].to(sampler.device)
    sampler.generator.set_state(state["generator_state"])
    sampler.proposed = int(state["proposed"])
    sampler.accepted = int(state["accepted"])
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return (
        int(meta["completed_batches"]),
        int(meta["completed_samples"]),
        float(meta["elapsed_sec"]),
    )


def append_progress(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def summarize(rows: np.ndarray, length: int, sampler: BatchedMetropolisSampler) -> dict:
    polyakov = rows["polyakov_real"] + 1j * rows["polyakov_imag"]
    action = rows["action"]
    payload = {
        "mean_polyakov_abs": float(np.mean(np.abs(polyakov))),
        "abs_mean_polyakov": float(abs(np.mean(polyakov))),
        "q_raw": float(abs(np.mean(polyakov)) / np.mean(np.abs(polyakov))),
        "action_mean": float(np.mean(action)),
        "action_susceptibility": float(np.var(action, ddof=0) / length**4),
        "acceptance_rate": sampler.acceptance_rate,
    }
    if not np.all(np.isnan(rows["vortex_density"])):
        payload["vortex_density_mean"] = float(np.nanmean(rows["vortex_density"]))
        payload["monopole_density_mean"] = float(np.nanmean(rows["monopole_density"]))
    return payload


def write_csv(path: Path, rows: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(DTYPE.names)
        writer.writerows(rows.tolist())


def run_model(args: argparse.Namespace, label: str, model: TorchModel) -> dict:
    spec = TARGETS[args.target]
    total = args.measurements or spec["measurements"]
    decorrelation = args.decorrelation_sweeps or spec["decorrelation_sweeps"]
    batches_total = math.ceil(total / args.batch_size)
    stem = f"idx56_{args.target}_{label}_{args.tag}"
    data_dir = WS / "outputs" / "data"
    checks_dir = WS / "outputs" / "checks"
    checkpoints_dir = WS / "outputs" / "checkpoints"
    for directory in (data_dir, checks_dir, checkpoints_dir):
        directory.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / f"{stem}.npy"
    state_path = checkpoints_dir / f"{stem}.pt"
    meta_path = checkpoints_dir / f"{stem}.json"
    progress_path = checks_dir / f"{stem}_progress.jsonl"

    sampler = BatchedMetropolisSampler(
        batch_size=args.batch_size,
        length=spec["length"],
        model=model,
        seed=args.seed,
        device=args.device,
        start=args.start,
    )
    if args.resume:
        if not (data_path.exists() and state_path.exists() and meta_path.exists()):
            raise FileNotFoundError("--resume requires data and checkpoint files")
        rows = np.lib.format.open_memmap(data_path, mode="r+")
        start_batch, completed, prior_elapsed = restore(sampler, state_path, meta_path)
    else:
        rows = np.lib.format.open_memmap(data_path, mode="w+", dtype=DTYPE, shape=(total,))
        rows["vortex_density"] = np.nan
        rows["monopole_density"] = np.nan
        start_batch, completed, prior_elapsed = 0, 0, 0.0
        sampler.sweep(args.thermal_sweeps)

    started = perf_counter()
    for batch_index in range(start_batch, batches_total):
        sampler.sweep(decorrelation)
        polyakov = sampler.polyakov_loop().detach().cpu().numpy()
        action = sampler.action().detach().cpu().numpy()
        if spec["defects"]:
            vortex, monopole = sampler.defect_densities()
            vortex_np = vortex.detach().cpu().numpy()
            monopole_np = monopole.detach().cpu().numpy()
        else:
            vortex_np = monopole_np = np.full(args.batch_size, np.nan)
        take = min(args.batch_size, total - completed)
        target = rows[completed : completed + take]
        target["sample"] = np.arange(completed, completed + take)
        target["chain"] = np.arange(take)
        target["measurement_in_chain"] = batch_index
        target["polyakov_real"] = polyakov[:take].real
        target["polyakov_imag"] = polyakov[:take].imag
        target["action"] = action[:take]
        target["vortex_density"] = vortex_np[:take]
        target["monopole_density"] = monopole_np[:take]
        completed += take

        if (batch_index + 1) % args.progress_every == 0 or completed == total:
            elapsed = prior_elapsed + perf_counter() - started
            payload = {
                "target": args.target,
                "label": label,
                "completed_samples": completed,
                "total_samples": total,
                "completed_batches": batch_index + 1,
                "total_batches": batches_total,
                "elapsed_sec": elapsed,
                "acceptance_rate": sampler.acceptance_rate,
                "updated_unix": time(),
            }
            append_progress(progress_path, payload)
        if (batch_index + 1) % args.checkpoint_every == 0 or completed == total:
            checkpoint(
                sampler=sampler,
                state_path=state_path,
                meta_path=meta_path,
                rows=rows,
                completed_batches=batch_index + 1,
                completed_samples=completed,
                elapsed_sec=prior_elapsed + perf_counter() - started,
            )

    final_rows = np.asarray(rows[:total])
    if args.write_csv:
        write_csv(data_dir / f"{stem}.csv", final_rows)
    result = {
        "status": "passed",
        "paper_id": "2505.00079",
        "benchmark_record": "prlb-f37350e-056",
        "target": args.target,
        "label": label,
        "model": asdict(model),
        "paper_parameters": {
            "length": spec["length"],
            "measurements": spec["measurements"],
            "decorrelation_sweeps": spec["decorrelation_sweeps"],
        },
        "generated_run": {
            "length": spec["length"],
            "total_measurements": total,
            "independent_chains": args.batch_size,
            "decorrelation_sweeps_per_chain": decorrelation,
            "thermal_sweeps_per_chain": args.thermal_sweeps,
            "thermal_sweeps_source": "not reported by paper; explicit case choice",
            "seed": args.seed,
            "start": args.start,
            "device": args.device,
        },
        "parameter_match": (
            "paper_total_measurements_batched_chains"
            if total == spec["measurements"] and decorrelation == spec["decorrelation_sweeps"]
            else "reduced_scale_batched_chains"
        ),
        "data_path": str(data_path.relative_to(WS)),
        "progress_path": str(progress_path.relative_to(WS)),
        **summarize(final_rows, spec["length"], sampler),
    }
    atomic_json(checks_dir / f"{stem}.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=TARGETS, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--measurements", type=int)
    parser.add_argument("--decorrelation-sweeps", type=int)
    parser.add_argument("--thermal-sweeps", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=5605)
    parser.add_argument("--start", choices=["hot", "cold"], default="hot")
    parser.add_argument("--tag", default="a100")
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--write-csv", action="store_true")
    args = parser.parse_args()
    results = [run_model(args, label, model) for label, model in TARGETS[args.target]["models"]]
    print(json.dumps({"status": "passed", "results": results}, indent=2))


if __name__ == "__main__":
    main()
