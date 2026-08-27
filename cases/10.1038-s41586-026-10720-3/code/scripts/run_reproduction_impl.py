#!/usr/bin/env python3
"""Run phase matching and the batched clean-room UPPE reproduction."""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

from optical_hawking import (
    AnalyticSignalUPPE,
    CleanRoomPCFDispersion,
    PropagationConfig,
    SimulationGrid,
    build_counterfactual_batch,
    conjugated_spm_contribution,
    figure2_landmarks,
    phase_matching_markers,
    stimulated_signal,
)
from optical_hawking.model import PAPER_PROBE_1400, PAPER_PUMP


WORKSPACE = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scientific_array_digest(arrays: dict[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(arrays.items()):
        array = np.ascontiguousarray(value)
        digest.update(name.encode("utf-8"))
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(json.dumps(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def implementation_digest() -> str:
    digest = hashlib.sha256()
    for relative, path in (
        ("scripts/run_reproduction.py", Path(__file__).resolve()),
        ("src/optical_hawking/model.py", WORKSPACE / "src/optical_hawking/model.py"),
        (
            "src/optical_hawking/physical_dispersion.py",
            WORKSPACE / "src/optical_hawking/physical_dispersion.py",
        ),
        (
            "src/optical_hawking/analysis.py",
            WORKSPACE / "src/optical_hawking/analysis.py",
        ),
        ("src/optical_hawking/solver.py", WORKSPACE / "src/optical_hawking/solver.py"),
    ):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preset",
        choices=("smoke", "feature", "a100-fast", "paper"),
        default="smoke",
    )
    parser.add_argument("--device", default=None)
    parser.add_argument("--output", type=Path, default=Path("outputs/data"))
    parser.add_argument("--no-compile", action="store_true")
    return parser.parse_args()


def preset(name: str, no_compile: bool) -> tuple[SimulationGrid, PropagationConfig]:
    if name == "smoke":
        return SimulationGrid(2**10), PropagationConfig(
            length_mm=0.004, step_mm=0.001, integrator="ifrk4", precision="complex128"
        )
    if name == "feature":
        return SimulationGrid(2**13), PropagationConfig(
            length_mm=0.25, step_mm=0.001, integrator="ifrk4", precision="complex64"
        )
    if name == "a100-fast":
        return SimulationGrid(2**16), PropagationConfig(
            length_mm=7.0,
            step_mm=0.001,
            integrator="ifrk4",
            precision="complex64",
            compile_step=not no_compile,
        )
    return SimulationGrid(2**16), PropagationConfig(
        length_mm=7.0,
        step_mm=0.0005,
        integrator="dopri5",
        precision="complex64",
    )


def main() -> None:
    args = parse_args()
    grid, config = preset(args.preset, args.no_compile)
    dispersion = CleanRoomPCFDispersion()
    config = replace(
        config,
        frame_velocity_over_c=dispersion.frame_velocity_over_c,
    )
    solver = AnalyticSignalUPPE(grid, config, dispersion, args.device)
    initial_time, weights = build_counterfactual_batch(
        solver.time_fs, PAPER_PUMP, PAPER_PROBE_1400, config.complex_dtype
    )
    if solver.device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(solver.device)
    result = solver.propagate(initial_time, weights)
    args.output.mkdir(parents=True, exist_ok=True)
    data_path = args.output / f"uppe_{args.preset}.npz"
    frozen_arrays = {
        "scenario_names": np.asarray(result.scenario_names),
        "omega_rad_fs": result.omega_rad_fs.numpy(),
        "initial_spectral_power": result.initial_spectral_power.numpy(),
        "final_spectral_power": result.final_spectral_power.numpy(),
        "snapshot_steps": np.asarray(sorted(result.snapshots)),
        "snapshot_power": np.asarray(
            [result.snapshots[key].numpy() for key in sorted(result.snapshots)]
        ),
    }
    np.savez_compressed(
        data_path,
        **frozen_arrays,
    )
    fig2 = figure2_landmarks(PAPER_PROBE_1400)
    omega_plot = torch.linspace(0.0, 8.5, 1200, dtype=torch.float64)
    omega_prime_plot = dispersion.omega_prime(omega_plot).numpy()
    signal = stimulated_signal(result.final_spectral_power).numpy()
    conjugated = conjugated_spm_contribution(result.final_spectral_power).numpy()
    positive = result.omega_rad_fs.numpy() > 0
    wavelength_nm = np.full(result.omega_rad_fs.shape, np.nan, dtype=float)
    wavelength_nm[positive] = (
        2.0 * np.pi * 299.792458 / result.omega_rad_fs.numpy()[positive]
    )
    uv = positive & (wavelength_nm >= 200.0) & (wavelength_nm <= 400.0)
    figure, axes = plt.subplots(1, 2, figsize=(9.0, 3.5))
    axes[0].plot(omega_plot.numpy(), omega_prime_plot, color="black", lw=1.2)
    axes[0].set(
        xlabel=r"$\omega$ (rad/fs)",
        ylabel=r"$\omega'$ (rad/fs)",
        title="Formula-only PCF surrogate",
    )
    axes[1].plot(wavelength_nm[uv], signal[0, uv], label="stimulated signal")
    axes[1].plot(
        wavelength_nm[uv],
        conjugated[uv],
        label="conjugated-SPM contribution",
    )
    axes[1].set(
        xlabel="wavelength (nm)",
        ylabel="spectral power (arb.)",
        title=f"{args.preset} UPPE diagnostic",
    )
    axes[1].legend(frameon=False, fontsize=8)
    figure.suptitle("Exploratory clean-room output — not paper-exact", fontsize=10)
    figure.tight_layout()
    figure_path = Path("outputs/figures") / f"formula_only_{args.preset}.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(figure_path, dpi=160)
    plt.close(figure)
    summary = {
        "preset": args.preset,
        "grid": asdict(grid),
        "propagation": config.as_dict(),
        "pump": asdict(PAPER_PUMP),
        "probe": asdict(PAPER_PROBE_1400),
        "input_pulse_phase_matching": phase_matching_markers(
            PAPER_PUMP, PAPER_PROBE_1400, dispersion
        ),
        "formula_only_fig2_landmarks": fig2,
        "phase_matching": fig2,
        "dispersion": dispersion.metadata(),
        "paper_exact": False,
        "scientific_status": "blocked_missing_paper_parameters",
        "blocking_missing_inputs": [
            "measured_effective_fibre_dispersion_coefficients",
            "measured_pulse_shapes_delays_and_chirps",
        ],
        "scientific_input_boundary": {
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "digitized_curves_used": False,
            "source_pixels_used": False,
        },
        "steps": result.steps,
        "rhs_evaluations": result.rhs_evaluations,
        "maximum_embedded_relative_error": result.maximum_embedded_relative_error,
        "precision": result.precision,
        "integrator": result.integrator,
        "data_path": str(data_path),
        "figure_path": str(figure_path),
        "scientific_array_sha256": scientific_array_digest(frozen_arrays),
    }
    summary_path = args.output / f"uppe_{args.preset}.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    manifest = {
        "schema_version": 1,
        "status": "passed_smoke_only" if args.preset == "smoke" else "exploratory",
        "preset": args.preset,
        "implementation_sha256": implementation_digest(),
        "scientific_array_sha256": summary["scientific_array_sha256"],
        "output_sha256": {
            str(data_path): sha256_file(data_path),
            str(summary_path): sha256_file(summary_path),
            str(figure_path): sha256_file(figure_path),
        },
        "paper_exact": False,
        "runtime_file_access_attested": False,
        "scientific_input_boundary": summary["scientific_input_boundary"],
    }
    manifest_path = Path("outputs/checks") / f"formula_only_{args.preset}_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    runtime = {
        "runtime_seconds": result.runtime_seconds,
        "device": result.device,
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "gpu_name": (
            torch.cuda.get_device_name(solver.device)
            if solver.device.type == "cuda"
            else None
        ),
        "peak_gpu_memory_bytes": (
            torch.cuda.max_memory_allocated(solver.device)
            if solver.device.type == "cuda"
            else None
        ),
    }
    print(json.dumps({"scientific_summary": summary, "runtime": runtime}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
