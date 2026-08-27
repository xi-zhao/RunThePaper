#!/usr/bin/env python3
"""Reproduce Main Fig. 2-right with exact mixed and representative dynamics."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

import leaf_thermodynamics as leaf  # noqa: E402


NONINTEGRABLE_FIELD = (
    (np.sqrt(5.0) + 5.0) / 8.0,
    0.5,
    np.sqrt(5.0) / 2.0,
)
DM = np.pi / 20.0
OBSERVABLES: tuple[tuple[str, leaf.PauliOps, float, str, str, str], ...] = (
    ("sigma_x", ((0, "x"),), 0.0, r"$\sigma^x$", "#ef5a08", "o"),
    ("sigma_y", ((0, "y"),), 0.4, r"$\sigma^y+0.4I$", "#596fc8", "s"),
    ("sigma_z", ((0, "z"),), -0.2, r"$\sigma^z-0.2I$", "#ef9200", "D"),
    (
        "sigma_x_sigma_x",
        ((0, "x"), (1, "x")),
        1.0,
        r"$\sigma^x\otimes\sigma^x+I$",
        "#a23ab5",
        "^",
    ),
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def gpu_profile() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return {"available": False}
    devices = []
    for line in completed.stdout.strip().splitlines():
        name, total, used, utilization = [part.strip() for part in line.split(",")]
        devices.append(
            {
                "name": name,
                "memory_total_mib": int(total),
                "memory_used_mib": int(used),
                "utilization_percent": int(utilization),
            }
        )
    return {"available": bool(devices), "gpus": devices}


def choose_band_indices(
    shell_indices: np.ndarray,
    deltas: np.ndarray,
    representative_index: int,
    maximum: int,
) -> np.ndarray:
    ordered = shell_indices[np.argsort(deltas[shell_indices])]
    if ordered.size <= maximum:
        selected = ordered
    else:
        positions = np.linspace(0, ordered.size - 1, maximum, dtype=int)
        selected = ordered[positions]
    if representative_index not in selected:
        if selected.size < maximum:
            selected = np.append(selected, representative_index)
        else:
            selected[-1] = representative_index
    return np.unique(selected)


def comparison_board(source: Path, reproduction: Path, output: Path) -> None:
    source_image = Image.open(source).convert("RGB")
    reproduction_image = Image.open(reproduction).convert("RGB")
    panel_width = 760
    header = 62

    def fit(image: Image.Image) -> Image.Image:
        scale = min(panel_width / image.width, 700 / image.height)
        return image.resize(
            (round(image.width * scale), round(image.height * scale)),
            Image.Resampling.LANCZOS,
        )

    left = fit(source_image)
    right = fit(reproduction_image)
    height = header + max(left.height, right.height) + 20
    canvas = Image.new("RGB", (2 * panel_width, height), "white")
    canvas.paste(left, ((panel_width - left.width) // 2, header))
    canvas.paste(right, (panel_width + (panel_width - right.width) // 2, header))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=22)
    draw.text((20, 18), "T003 - paper source", fill="black", font=font)
    draw.text((panel_width + 20, 18), "independent reproduction", fill="black", font=font)
    draw.line((panel_width, 0, panel_width, height), fill="#b5b5b5", width=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("numpy", "cupy"), default="numpy")
    parser.add_argument("--length", type=int, default=6)
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument("--time-max", type=float, default=3.0)
    parser.add_argument("--time-points", type=int, default=61)
    parser.add_argument("--boundary", choices=("open", "periodic"), default="periodic")
    parser.add_argument("--max-band-representatives", type=int, default=48)
    parser.add_argument("--require-a100", action="store_true")
    parser.add_argument("--no-reference-comparison", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.length < 2:
        raise ValueError("length must be at least 2")
    if args.time_points < 2:
        raise ValueError("time-points must be at least 2")
    accelerator = (
        gpu_profile()
        if args.backend == "cupy" or args.require_a100
        else {"available": False, "query_skipped": "cpu_backend"}
    )
    if args.require_a100:
        names = [str(item["name"]) for item in accelerator.get("gpus", [])]
        if args.backend != "cupy" or not any("A100" in name for name in names):
            raise RuntimeError(f"A100/CuPy required; observed GPUs: {names or 'none'}")

    xp = leaf.array_module(args.backend)
    dimension = 1 << args.length
    central = args.length // 2 - 1 if args.length % 2 == 0 else args.length // 2
    observables = tuple(
        (
            name,
            tuple((central + site, operator) for site, operator in relative_ops),
            offset,
            label,
            color,
            marker,
        )
        for name, relative_ops, offset, label, color, marker in OBSERVABLES
    )
    started = time.perf_counter()
    h_sparse = leaf.spin_chain_hamiltonian(
        args.length,
        NONINTEGRABLE_FIELD,
        DM,
        boundary=args.boundary,
    )
    h0_sparse = leaf.spin_chain_hamiltonian(
        args.length,
        (0.0, 0.0, 1.5),
        0.0,
        boundary=args.boundary,
    )
    h = xp.asarray(h_sparse.toarray())
    h0 = xp.asarray(h0_sparse.toarray())
    build_seconds = time.perf_counter() - started

    diagonalization_started = time.perf_counter()
    h_energies, h_basis = xp.linalg.eigh(h)
    h0_energies, h0_basis = xp.linalg.eigh(h0)
    leaf.synchronize(args.backend)
    diagonalization_seconds = time.perf_counter() - diagonalization_started

    ensemble_started = time.perf_counter()
    overlap = h_basis.conj().T @ h0_basis
    h_in_h0_basis = h0_basis.conj().T @ h @ h0_basis
    rho_eigenvalues = leaf.thermal_weights(h0_energies, args.beta, backend=args.backend)
    ensemble = leaf.minimum_variance_ensemble(
        rho_eigenvalues,
        h_in_h0_basis,
        rho_basis=h0_basis,
        thermal_energies=h0_energies,
        beta=args.beta,
        backend=args.backend,
    )
    invariants = leaf.ensemble_invariants(
        rho_eigenvalues,
        h_in_h0_basis,
        ensemble,
    )
    h_representatives = h_in_h0_basis @ ensemble.representatives_rho_basis
    representative_means = xp.sum(
        ensemble.representatives_rho_basis.conj() * h_representatives,
        axis=0,
    ).real
    representative_h2 = xp.sum(xp.abs(h_representatives) ** 2, axis=0).real
    representative_variances = xp.maximum(
        representative_h2 - representative_means**2,
        0.0,
    )
    thermal_energy = xp.sum(rho_eigenvalues * xp.real(xp.diag(h_in_h0_basis)))
    denominator = xp.sqrt(representative_variances + invariants["qfi_spectral"] / 4.0)
    deltas = xp.abs(ensemble.energies - thermal_energy) / denominator
    deltas_host = np.real(leaf.to_numpy(deltas))
    representative_index = int(np.argmin(deltas_host))
    shell_radius = (float(np.max(deltas_host)) - float(np.min(deltas_host))) / args.length
    shell_indices = np.flatnonzero(
        deltas_host - float(np.min(deltas_host)) <= shell_radius + 1e-15
    )
    sampled_indices = choose_band_indices(
        shell_indices,
        deltas_host,
        representative_index,
        args.max_band_representatives,
    )
    selected_position = int(np.flatnonzero(sampled_indices == representative_index)[0])
    sampled_coefficients = overlap @ ensemble.representatives_rho_basis[:, sampled_indices]
    rho_h_basis = (overlap * rho_eigenvalues[None, :]) @ overlap.conj().T
    leaf.synchronize(args.backend)
    ensemble_seconds = time.perf_counter() - ensemble_started

    observable_kernels: dict[str, Any] = {}
    direct_initial: dict[str, float] = {}
    operator_started = time.perf_counter()
    for name, ops, _offset, _label, _color, _marker in observables:
        operator_h_basis = h_basis.conj().T @ leaf.apply_pauli_string(
            h_basis,
            args.length,
            ops,
            backend=args.backend,
        )
        observable_kernels[name] = rho_h_basis * operator_h_basis.T
        h0_expectations = leaf.pauli_expectations(
            h0_basis,
            args.length,
            ops,
            backend=args.backend,
        )
        direct_initial[name] = float(
            leaf.to_numpy(xp.sum(rho_eigenvalues * h0_expectations)).real
        )
        del operator_h_basis
    leaf.synchronize(args.backend)
    operator_seconds = time.perf_counter() - operator_started

    times = np.linspace(0.0, args.time_max, args.time_points)
    trajectory_rows: list[dict[str, Any]] = []
    initial_errors: dict[str, float] = {}
    evolution_started = time.perf_counter()
    for time_value in times:
        phases = xp.exp(-1j * h_energies * time_value)
        evolved_samples = h_basis @ (phases[:, None] * sampled_coefficients)
        for name, ops, offset, _label, _color, _marker in observables:
            mixed = phases @ observable_kernels[name] @ phases.conj()
            sample_values = np.real(
                leaf.to_numpy(
                    leaf.pauli_expectations(
                        evolved_samples,
                        args.length,
                        ops,
                        backend=args.backend,
                    )
                )
            )
            q025, q16, q84, q975 = np.quantile(sample_values, (0.025, 0.16, 0.84, 0.975))
            mixed_value = float(leaf.to_numpy(mixed).real)
            representative_value = float(sample_values[selected_position])
            if time_value == 0.0:
                initial_errors[name] = abs(mixed_value - direct_initial[name])
            trajectory_rows.append(
                {
                    "artifact_state": (
                        "final_reproduction" if args.length == 12 else "scaled_down_reproduction"
                    ),
                    "parameter_match": "paper_exact_reconstructed_metadata",
                    "length": args.length,
                    "dimension": dimension,
                    "beta": args.beta,
                    "boundary": args.boundary,
                    "time": float(time_value),
                    "observable": name,
                    "display_offset": offset,
                    "mixed_exact": mixed_value,
                    "representative": representative_value,
                    "lower_68": float(q16),
                    "upper_68": float(q84),
                    "lower_95": float(q025),
                    "upper_95": float(q975),
                }
            )
        del evolved_samples
    leaf.synchronize(args.backend)
    evolution_seconds = time.perf_counter() - evolution_started

    data_path = WORKSPACE / "outputs" / "data" / "t003_dynamics.csv"
    write_csv(data_path, trajectory_rows)

    figure, axis = plt.subplots(figsize=(6.4, 6.4))
    for name, _ops, offset, label, color, marker in observables:
        points = [row for row in trajectory_rows if row["observable"] == name]
        x = np.asarray([row["time"] for row in points])
        mixed = np.asarray([row["mixed_exact"] + offset for row in points])
        representative = np.asarray([row["representative"] + offset for row in points])
        lower_68 = np.asarray([row["lower_68"] + offset for row in points])
        upper_68 = np.asarray([row["upper_68"] + offset for row in points])
        lower_95 = np.asarray([row["lower_95"] + offset for row in points])
        upper_95 = np.asarray([row["upper_95"] + offset for row in points])
        axis.fill_between(x, lower_95, upper_95, color=color, alpha=0.10, linewidth=0)
        axis.fill_between(x, lower_68, upper_68, color=color, alpha=0.20, linewidth=0)
        axis.plot(x, mixed, color=color, linewidth=2.0, label=label)
        marker_stride = max(1, len(x) // 25)
        axis.plot(
            x[::marker_stride],
            representative[::marker_stride],
            linestyle="none",
            marker=marker,
            markersize=4.2,
            color=color,
        )
    axis.axhline(0.0, color="#777777", linewidth=0.6)
    axis.set_xlim(0.0, args.time_max)
    axis.set_xlabel("$t$", fontsize=13)
    axis.set_ylabel(r"$\langle O\rangle$", fontsize=13)
    axis.tick_params(direction="in", top=True, right=True)
    axis.legend(frameon=False, loc="lower center", fontsize=9)
    axis.set_title(
        f"$L={args.length}$, $\\beta={args.beta:g}$; "
        f"{sampled_indices.size}/{shell_indices.size} shell representatives"
    )
    figure.tight_layout()
    figure_path = WORKSPACE / "outputs" / "figures" / "t003_dynamics.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close(figure)

    comparison_path = WORKSPACE / "outputs" / "comparisons" / "t003_source_vs_reproduction.png"
    if not args.no_reference_comparison:
        comparison_board(
            WORKSPACE / "references" / "original_figures" / "dyn.png",
            figure_path,
            comparison_path,
        )

    invariant_max = max(
        invariants["population_sum_error"],
        invariants["maximum_norm_error"],
        invariants["reconstruction_fro_error"],
        invariants["representative_energy_max_error"],
        invariants["qfi_variance_absolute_error"],
    )
    finite = all(
        np.isfinite(
            [
                row["mixed_exact"],
                row["representative"],
                row["lower_68"],
                row["upper_68"],
                row["lower_95"],
                row["upper_95"],
            ]
        ).all()
        for row in trajectory_rows
    )
    passed = invariant_max < 1e-7 and max(initial_errors.values()) < 1e-8 and finite
    check = {
        "schema_version": 1,
        "paper_id": "2602.12212",
        "target_id": "T003",
        "status": "passed" if passed else "failed",
        "coverage_status": "complete" if args.length == 12 else "scaled_down_pending_a100",
        "artifact_state": (
            "final_reproduction" if args.length == 12 else "scaled_down_reproduction"
        ),
        "parameter_match": "paper_exact_reconstructed_metadata",
        "generated_data_provenance": "independent_numerics",
        "backend": args.backend,
        "platform": f"{platform.system()}-{platform.release()}-{platform.machine()}",
        "accelerator": accelerator,
        "length": args.length,
        "dimension": dimension,
        "beta": args.beta,
        "boundary": args.boundary,
        "representative_index": representative_index,
        "minimum_delta": float(deltas_host[representative_index]),
        "delta_shell_radius": shell_radius,
        "delta_shell_count": int(shell_indices.size),
        "sampled_band_representatives": int(sampled_indices.size),
        "band_sampling": (
            "complete delta shell"
            if sampled_indices.size == shell_indices.size
            else "deterministic quantiles across evenly spaced delta-ranked shell representatives"
        ),
        "invariants": invariants,
        "maximum_formula_invariant_error": invariant_max,
        "mixed_initial_condition_errors": initial_errors,
        "finite_trajectories": finite,
        "timing": {
            "build_seconds": build_seconds,
            "diagonalization_seconds": diagonalization_seconds,
            "ensemble_seconds": ensemble_seconds,
            "observable_transform_seconds": operator_seconds,
            "evolution_seconds": evolution_seconds,
            "total_seconds": time.perf_counter() - started,
        },
        "paths": {
            "data": str(data_path.relative_to(WORKSPACE)),
            "figure": str(figure_path.relative_to(WORKSPACE)),
            "comparison": str(comparison_path.relative_to(WORKSPACE)),
        },
        "note": (
            "The paper omits boundary/site/interval implementation metadata. "
            "Periodic boundaries, the central bond, and empirical shell quantiles "
            "are disclosed reconstructions."
        ),
    }
    check_path = WORKSPACE / "outputs" / "checks" / "t003_dynamics.json"
    write_json(check_path, check)
    print(json.dumps(check, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
