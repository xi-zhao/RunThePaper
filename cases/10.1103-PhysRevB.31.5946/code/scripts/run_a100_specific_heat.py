#!/usr/bin/env python3
"""Batched 16-color Metropolis scan for source Figs. 9-10.

The 4x4 coloring is exact for the NN, diagonal NNN, and axial distance-two
interaction graph: sites updated concurrently never share a Hamiltonian bond.
The trajectory is implementation-equivalent, not identical to the unavailable
1985 RNG/order, so outputs are labeled independent reduced evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch


def parse_ints(value: str) -> list[int]:
    return [int(item) for item in value.split(",") if item.strip()]


def temperature_grid(start: float, stop: float, count: int) -> np.ndarray:
    if count < 2 or start <= 0.0 or stop <= start:
        raise ValueError("temperature grid requires 0 < start < stop and count >= 2")
    return np.linspace(start, stop, count)


def neighbor_field(spins: torch.Tensor, r: float, r_prime: float) -> torch.Tensor:
    nn = sum(torch.roll(spins, shifts=shift, dims=axis) for axis in (1, 2) for shift in (-1, 1))
    nnn = sum(
        torch.roll(torch.roll(spins, shifts=dx, dims=1), shifts=dy, dims=2)
        for dx in (-1, 1)
        for dy in (-1, 1)
    )
    third = sum(torch.roll(spins, shifts=shift, dims=axis) for axis in (1, 2) for shift in (-2, 2))
    return nn + r * nnn + r_prime * third


def energy_per_spin(spins: torch.Tensor, r: float, r_prime: float) -> torch.Tensor:
    nn = torch.roll(spins, -1, 1) + torch.roll(spins, -1, 2)
    nnn = torch.roll(torch.roll(spins, -1, 1), -1, 2) + torch.roll(torch.roll(spins, -1, 1), 1, 2)
    third = torch.roll(spins, -2, 1) + torch.roll(spins, -2, 2)
    return (spins * (nn + r * nnn + r_prime * third)).mean(dim=(1, 2))


def color_masks(size: int, device: torch.device) -> list[torch.Tensor]:
    x, y = torch.meshgrid(torch.arange(size, device=device), torch.arange(size, device=device), indexing="ij")
    return [((x % 4) * 4 + (y % 4) == color).unsqueeze(0) for color in range(16)]


def sweep(
    spins: torch.Tensor,
    temperatures: torch.Tensor,
    masks: list[torch.Tensor],
    *,
    r: float,
    r_prime: float,
    generator: torch.Generator,
) -> None:
    for mask in masks:
        field = neighbor_field(spins, r, r_prime)
        delta = -2.0 * spins * field
        random = torch.rand(spins.shape, device=spins.device, generator=generator)
        accepted = mask & ((delta <= 0.0) | (random < torch.exp(-delta / temperatures)))
        spins[accepted] *= -1.0


def run_size(
    size: int,
    temperatures_np: np.ndarray,
    *,
    replicas: int,
    burnin: int,
    measurements: int,
    r: float,
    r_prime: float,
    device: torch.device,
    seed: int,
) -> dict[str, object]:
    if size <= 0 or size % 4:
        raise ValueError("16-color periodic updates require each lattice size to be a positive multiple of four")
    generator = torch.Generator(device=device)
    generator.manual_seed(seed + size)
    temperatures = torch.as_tensor(np.repeat(temperatures_np, replicas), dtype=torch.float32, device=device)
    temperature_field = temperatures[:, None, None]
    spins = torch.where(
        torch.rand((temperatures.numel(), size, size), device=device, generator=generator) < 0.5,
        -torch.ones((), device=device),
        torch.ones((), device=device),
    )
    masks = color_masks(size, device)
    for _ in range(burnin):
        sweep(spins, temperature_field, masks, r=r, r_prime=r_prime, generator=generator)

    energy_sum = torch.zeros_like(temperatures)
    energy_sq_sum = torch.zeros_like(temperatures)
    for _ in range(measurements):
        sweep(spins, temperature_field, masks, r=r, r_prime=r_prime, generator=generator)
        energy = energy_per_spin(spins, r, r_prime)
        energy_sum += energy
        energy_sq_sum += energy * energy

    mean = (energy_sum / measurements).reshape(-1, replicas)
    mean_sq = (energy_sq_sum / measurements).reshape(-1, replicas)
    per_replica_heat = size * size * (mean_sq - mean * mean) / torch.as_tensor(
        temperatures_np[:, None] ** 2, dtype=torch.float32, device=device
    )
    energy_curve = mean.mean(dim=1).cpu().numpy()
    heat_curve = per_replica_heat.mean(dim=1).cpu().numpy()
    heat_sem = per_replica_heat.std(dim=1, unbiased=True).div(math.sqrt(replicas)).cpu().numpy()
    peak_index = int(np.argmax(heat_curve))
    return {
        "size": size,
        "temperatures": temperatures_np.tolist(),
        "energy_per_spin": energy_curve.tolist(),
        "specific_heat_per_spin": heat_curve.tolist(),
        "specific_heat_sem": heat_sem.tolist(),
        "peak_temperature_grid": float(temperatures_np[peak_index]),
        "peak_specific_heat": float(heat_curve[peak_index]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--progress", required=True)
    parser.add_argument("--sizes", default="24,36,48,60")
    parser.add_argument("--temperature-start", type=float, default=0.6)
    parser.add_argument("--temperature-stop", type=float, default=2.0)
    parser.add_argument("--temperature-count", type=int, default=29)
    parser.add_argument("--replicas", type=int, default=8)
    parser.add_argument("--burnin", type=int, default=400)
    parser.add_argument("--measurements", type=int, default=400)
    parser.add_argument("--r", type=float, default=0.0)
    parser.add_argument("--r-prime", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=19850501)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    if args.replicas < 2 or args.burnin < 1 or args.measurements < 2:
        raise ValueError("replicas >= 2, burnin >= 1, and measurements >= 2 are required")
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    temperatures = temperature_grid(args.temperature_start, args.temperature_stop, args.temperature_count)
    output = Path(args.output)
    progress = Path(args.progress)
    output.parent.mkdir(parents=True, exist_ok=True)
    progress.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    records = []
    with progress.open("a", encoding="utf-8") as progress_file:
        for size in parse_ints(args.sizes):
            record = run_size(
                size,
                temperatures,
                replicas=args.replicas,
                burnin=args.burnin,
                measurements=args.measurements,
                r=args.r,
                r_prime=args.r_prime,
                device=device,
                seed=args.seed,
            )
            records.append(record)
            progress_file.write(json.dumps({"event": "size_complete", "elapsed_seconds": time.time() - started, **record}) + "\n")
            progress_file.flush()

    inverse_sizes = np.asarray([1.0 / int(record["size"]) for record in records])
    peaks = np.asarray([float(record["peak_temperature_grid"]) for record in records])
    if len(records) >= 2:
        slope, intercept = np.polyfit(inverse_sizes, peaks, 1)
    else:
        slope, intercept = math.nan, math.nan
    payload = {
        "schema_version": 1,
        "paper_id": "10.1103-PhysRevB.31.5946",
        "target": "Figs. 9-10 specific-heat finite-size scan",
        "provenance": "independent_numerics_parallel_16_color_metropolis",
        "artifact_stage": "exploratory",
        "parameter_match": "paper_subset",
        "paper_observation_tc2": 0.7,
        "settings": vars(args),
        "device": str(device),
        "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "elapsed_seconds": time.time() - started,
        "records": records,
        "linear_peak_fit_vs_inverse_l": {"slope": float(slope), "intercept_tc_infinite": float(intercept)},
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
