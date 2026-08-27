#!/usr/bin/env python3
"""Run the exact Science aaw1611 reproduction and write evidence artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.linalg import expm


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from quantum_walk import (  # noqa: E402
    build_hamiltonian,
    connected_z_correlation,
    distribution_fidelity,
    double_occupancy_probability,
    effective_couplings_from_detuning,
    evolve_state,
    evolve_single_excitation_lindblad,
    fock_state,
    mhz_to_rad_per_ns,
    normalized_correlation_distance,
    occupation_basis,
    one_particle_concurrence,
    one_particle_entropy,
    spectral_group_velocity,
    site_density,
    state_norms,
    two_particle_correlator,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=WORKSPACE / "config" / "paper_exact.json")
    parser.add_argument("--output-dir", type=Path, default=WORKSPACE / "outputs")
    parser.add_argument("--backend", choices=("numpy", "cupy", "auto"), default="numpy")
    parser.add_argument("--reference-signature", type=Path)
    parser.add_argument("--no-plots", action="store_true")
    return parser.parse_args()


def time_grid(settings: dict[str, Any], stop_key: str = "time_stop_ns") -> np.ndarray:
    start = float(settings["time_start_ns"])
    stop = float(settings[stop_key])
    step = float(settings["time_step_ns"])
    return np.arange(start, stop + 0.5 * step, step, dtype=np.float64)


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check_payload(metrics: dict[str, Any], rules: dict[str, bool]) -> dict[str, Any]:
    return {
        "status": "passed" if all(rules.values()) else "failed",
        "metrics": metrics,
        "rules": rules,
    }


def heatmap(
    axis: Any,
    values: np.ndarray,
    extent: tuple[float, float, float, float],
    title: str,
    label: str,
    vmax: float | None = None,
) -> None:
    from matplotlib import pyplot as plt

    image = axis.imshow(
        values,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="magma",
        vmin=0.0,
        vmax=vmax,
        interpolation="nearest",
    )
    axis.set_title(title)
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Qubit site")
    plt.colorbar(image, ax=axis, fraction=0.046, pad=0.04, label=label)


def render_figures(
    figure_dir: Path,
    one_times: np.ndarray,
    one_density: dict[str, np.ndarray],
    center_entropy: np.ndarray,
    center_correlation: np.ndarray,
    center_concurrence: np.ndarray,
    snapshot_index: int,
    center_rms_distance: np.ndarray,
    velocity_scale: float,
    reported_velocity: float,
    two_snapshot_correlations: dict[tuple[str, str], np.ndarray],
    snapshot_times: np.ndarray,
    snapshot_evolution_times: np.ndarray,
    double_times: np.ndarray,
    double_occupancy: np.ndarray,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    figure_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.5), constrained_layout=True)
    for axis, launch in zip(axes, ("Q6", "Q1", "Q11"), strict=True):
        density = one_density[launch]
        heatmap(
            axis,
            density.T,
            (one_times[0], one_times[-1], 0.5, density.shape[1] + 0.5),
            f"Launch {launch}",
            r"$\langle n_j\rangle$",
            vmax=1.0,
        )
    fig.suptitle("T001 — calibrated one-photon quantum walks")
    fig.savefig(figure_dir / "T001_one_particle_density.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(9, 7), constrained_layout=True)
    heatmap(
        axes[0, 0],
        center_entropy.T,
        (one_times[0], one_times[-1], 0.5, center_entropy.shape[1] + 0.5),
        "Q6 launch: one-site entropy",
        "entropy (nats)",
        vmax=np.log(2.0),
    )
    corr_image = axes[0, 1].imshow(center_correlation[snapshot_index], cmap="coolwarm", vmin=-1, vmax=1)
    axes[0, 1].set_title(f"Connected correlation at {one_times[snapshot_index]:.1f} ns")
    axes[0, 1].set_xlabel("site j")
    axes[0, 1].set_ylabel("site i")
    plt.colorbar(corr_image, ax=axes[0, 1], fraction=0.046, pad=0.04)
    conc_image = axes[1, 0].imshow(center_concurrence[snapshot_index], cmap="viridis", vmin=0, vmax=1)
    axes[1, 0].set_title(f"Concurrence at {one_times[snapshot_index]:.1f} ns")
    axes[1, 0].set_xlabel("site j")
    axes[1, 0].set_ylabel("site i")
    plt.colorbar(conc_image, ax=axes[1, 0], fraction=0.046, pad=0.04)
    axes[1, 1].plot(one_times, center_rms_distance, color="#4c78a8", lw=1.8)
    axes[1, 1].text(
        0.03,
        0.97,
        f"Eq. S29 spectrum: {velocity_scale:.5f} sites/us\npaper: {reported_velocity:.2f} sites/us",
        transform=axes[1, 1].transAxes,
        va="top",
    )
    axes[1, 1].set_title("Q6 launch: rms displacement")
    axes[1, 1].set_xlabel("Time (ns)")
    axes[1, 1].set_ylabel("sites")
    fig.suptitle("T002 — information spreading")
    fig.savefig(figure_dir / "T002_one_particle_observables.png", dpi=220)
    plt.close(fig)

    models = ("strong", "free", "hardcore")
    launches = ("Q1_Q12", "Q6_Q7")
    final_snapshot = -1
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.5), constrained_layout=True)
    for row, launch in enumerate(launches):
        vmax = max(
            float(np.max(two_snapshot_correlations[(model, launch)][final_snapshot])) for model in models
        )
        for column, model in enumerate(models):
            matrix = two_snapshot_correlations[(model, launch)][final_snapshot]
            image = axes[row, column].imshow(matrix, origin="lower", cmap="magma", vmin=0, vmax=vmax)
            axes[row, column].set_title(f"{launch}: {model}")
            axes[row, column].set_xlabel("site j")
            axes[row, column].set_ylabel("site i")
            plt.colorbar(image, ax=axes[row, column], fraction=0.046, pad=0.04)
    fig.suptitle(
        "T003 — two-photon Gij: "
        f"printed S20 time {snapshot_times[final_snapshot]:.1f} ns"
    )
    fig.savefig(figure_dir / "T003_two_particle_correlations.png", dpi=220)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7, 4.2), constrained_layout=True)
    heatmap(
        axis,
        double_occupancy.T,
        (double_times[0], double_times[-1], 0.5, double_occupancy.shape[1] + 0.5),
        "Q6+Q7 launch: double occupancy",
        r"$P(n_j=2)$",
        vmax=0.03,
    )
    fig.suptitle("T004 — suppression of on-site photon pairs")
    fig.savefig(figure_dir / "T004_double_occupancy.png", dpi=220)
    plt.close(fig)


def render_robustness_figures(
    figure_dir: Path,
    disorder_times: np.ndarray,
    disorder_widths: np.ndarray,
    one_disorder_density: dict[float, np.ndarray],
    two_disorder_density: dict[float, np.ndarray],
    fidelity_times: np.ndarray,
    solid_fidelity: dict[str, np.ndarray],
    dashed_fidelity: dict[str, np.ndarray],
) -> None:
    """Render the thirteen theory panels in Supplement Figs. S9-S11."""

    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    figure_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})

    fig, axes = plt.subplots(2, len(disorder_widths), figsize=(18, 6.2), constrained_layout=True)
    for column, width in enumerate(disorder_widths):
        one = one_disorder_density[float(width)]
        two = two_disorder_density[float(width)]
        heatmap(
            axes[0, column],
            one.T,
            (disorder_times[0], disorder_times[-1], 0.5, one.shape[1] + 0.5),
            f"S9: W/2π={width:g} MHz",
            r"$\langle n_j\rangle$",
            vmax=1.0,
        )
        heatmap(
            axes[1, column],
            two.T,
            (disorder_times[0], disorder_times[-1], 0.5, two.shape[1] + 0.5),
            f"S10: W/2π={width:g} MHz",
            r"$\langle n_j\rangle$",
            vmax=1.0,
        )
    fig.suptitle("T005 — 50-sequence disorder ensembles from Supplement Sec. IV.C")
    fig.savefig(figure_dir / "T005_disorder_ensembles.png", dpi=220)
    plt.close(fig)

    colors = {"Central": "#4c78a8", "Leftmost": "#e45756", "Rightmost": "#f2cf5b"}
    fig, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    for launch in ("Central", "Leftmost", "Rightmost"):
        axis.plot(
            fidelity_times,
            solid_fidelity[launch],
            color=colors[launch],
            lw=1.8,
            label=f"{launch}: coupling error",
        )
        axis.plot(
            fidelity_times,
            dashed_fidelity[launch],
            color=colors[launch],
            lw=1.4,
            ls="--",
            label=f"{launch}: + decoherence/disorder",
        )
    axis.set_xlim(float(fidelity_times[0]), float(fidelity_times[-1]))
    axis.set_ylim(0.75, 1.005)
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Distribution fidelity")
    axis.set_title("T005 — reconstructed Supplement Fig. S11")
    axis.legend(ncol=2, fontsize=7)
    fig.savefig(figure_dir / "T005_coupling_precision_fidelity.png", dpi=220)
    plt.close(fig)


def compare_signature(
    signature: dict[str, np.ndarray],
    reference_path: Path,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    reference = np.load(reference_path)
    metrics: dict[str, Any] = {}
    rules: dict[str, bool] = {}
    for key, values in signature.items():
        if key not in reference:
            metrics[key] = {"error": "missing from reference"}
            rules[key] = False
            continue
        expected = reference[key]
        max_abs = float(np.max(np.abs(values - expected)))
        metrics[key] = {"shape": list(values.shape), "max_abs_error": max_abs}
        rules[key] = bool(np.allclose(values, expected, atol=atol, rtol=rtol))
    payload = check_payload(metrics, rules)
    payload["reference"] = str(reference_path)
    payload["atol"] = atol
    payload["rtol"] = rtol
    return payload


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    acceptance = config["acceptance"]
    output_dir = args.output_dir.resolve()
    data_dir = output_dir / "data"
    check_dir = output_dir / "checks"
    figure_dir = output_dir / "figures"
    for path in (data_dir, check_dir, figure_dir):
        path.mkdir(parents=True, exist_ok=True)

    couplings = mhz_to_rad_per_ns(config["couplings_mhz"])
    interactions = mhz_to_rad_per_ns(config["interactions_mhz"])
    tolerance = float(acceptance["normalization_atol"])

    one_settings = config["one_particle"]
    one_times = time_grid(one_settings)
    one_basis = occupation_basis(int(one_settings["site_count"]), 1)
    one_hamiltonian = build_hamiltonian(one_basis, couplings[: len(one_basis[0]) - 1])
    one_density: dict[str, np.ndarray] = {}
    one_states: dict[str, np.ndarray] = {}
    one_rows: list[dict[str, Any]] = []
    one_norm_error = 0.0
    one_density_sum_error = 0.0
    one_initial_error = 0.0
    actual_backend = ""
    accelerator = ""
    for launch, sites in one_settings["launches"].items():
        initial = fock_state(one_basis, sites)
        result = evolve_state(one_hamiltonian, initial, one_times, args.backend)
        actual_backend, accelerator = result.backend, result.accelerator
        density = site_density(result.states, one_basis)
        one_states[launch] = result.states
        one_density[launch] = density
        one_norm_error = max(one_norm_error, float(np.max(np.abs(state_norms(result.states) - 1.0))))
        one_density_sum_error = max(one_density_sum_error, float(np.max(np.abs(np.sum(density, axis=1) - 1.0))))
        expected_initial = site_density(initial[None, :], one_basis)[0]
        one_initial_error = max(one_initial_error, float(np.max(np.abs(density[0] - expected_initial))))
        for time_index, time_ns in enumerate(one_times):
            for site, value in enumerate(density[time_index], start=1):
                one_rows.append({"launch": launch, "time_ns": time_ns, "site": site, "density": value})
    write_csv(data_dir / "one_particle_density.csv", ["launch", "time_ns", "site", "density"], one_rows)

    t001_metrics = {
        "basis_dimension": len(one_basis),
        "max_norm_error": one_norm_error,
        "max_density_sum_error": one_density_sum_error,
        "max_initial_density_error": one_initial_error,
    }
    t001_rules = {
        "basis_dimension_is_11": len(one_basis) == 11,
        "state_norm_preserved": one_norm_error < tolerance,
        "density_sums_to_one": one_density_sum_error < tolerance,
        "initial_conditions_exact": one_initial_error < tolerance,
    }
    t001 = check_payload(t001_metrics, t001_rules)
    write_json(check_dir / "T001_checks.json", t001)

    center_states = one_states["Q6"]
    center_density = one_density["Q6"]
    center_entropy = one_particle_entropy(center_density)
    center_correlation = connected_z_correlation(center_density)
    center_concurrence = one_particle_concurrence(center_states)
    positions = np.arange(center_density.shape[1], dtype=np.float64)
    launch_position = float(one_settings["launches"]["Q6"][0])
    squared_distance = (positions - launch_position) ** 2
    center_rms_distance = np.sqrt(center_density @ squared_distance)
    snapshot_index = int(np.argmin(np.abs(one_times - float(one_settings["observable_snapshot_ns"]))))
    observable_rows: list[dict[str, Any]] = []
    for time_index, time_ns in enumerate(one_times):
        for site in range(center_density.shape[1]):
            observable_rows.append(
                {
                    "time_ns": time_ns,
                    "site": site + 1,
                    "density": center_density[time_index, site],
                    "entropy_nats": center_entropy[time_index, site],
                    "rms_distance_sites": center_rms_distance[time_index],
                }
            )
    write_csv(
        data_dir / "one_particle_observables.csv",
        ["time_ns", "site", "density", "entropy_nats", "rms_distance_sites"],
        observable_rows,
    )
    pair_rows: list[dict[str, Any]] = []
    for site_i in range(center_density.shape[1]):
        for site_j in range(center_density.shape[1]):
            pair_rows.append(
                {
                    "time_ns": one_times[snapshot_index],
                    "site_i": site_i + 1,
                    "site_j": site_j + 1,
                    "connected_z": center_correlation[snapshot_index, site_i, site_j],
                    "concurrence": center_concurrence[snapshot_index, site_i, site_j],
                }
            )
    write_csv(
        data_dir / "one_particle_pair_observables.csv",
        ["time_ns", "site_i", "site_j", "connected_z", "concurrence"],
        pair_rows,
    )
    velocity_scale = spectral_group_velocity(couplings[: len(one_basis[0]) - 1])
    reported_velocity = float(config["reported_group_velocity_sites_per_us"])
    velocity_relative_error = abs(velocity_scale - reported_velocity) / reported_velocity
    t002_metrics = {
        "entropy_min": float(np.min(center_entropy)),
        "entropy_max": float(np.max(center_entropy)),
        "connected_z_max_abs": float(np.max(np.abs(center_correlation))),
        "concurrence_min": float(np.min(center_concurrence)),
        "concurrence_max": float(np.max(center_concurrence)),
        "spectral_group_velocity_sites_per_us": velocity_scale,
        "reported_velocity_sites_per_us": reported_velocity,
        "velocity_relative_error": velocity_relative_error,
    }
    t002_rules = {
        "entropy_in_binary_bounds": bool(np.min(center_entropy) >= -tolerance and np.max(center_entropy) <= np.log(2.0) + tolerance),
        "connected_correlation_bounded": bool(np.max(np.abs(center_correlation)) <= 1.0 + tolerance),
        "concurrence_bounded": bool(np.min(center_concurrence) >= -tolerance and np.max(center_concurrence) <= 1.0 + tolerance),
        "velocity_scale_matches_report": velocity_relative_error < float(acceptance["group_velocity_relative_tolerance"]),
    }
    t002 = check_payload(t002_metrics, t002_rules)
    write_json(check_dir / "T002_checks.json", t002)

    two_settings = config["two_particle"]
    two_times = time_grid(two_settings)
    snapshot_times = np.asarray(two_settings["correlator_snapshots_ns"], dtype=np.float64)
    snapshot_evolution_times = snapshot_times.copy()
    snapshot_indices = np.asarray(
        [int(np.argmin(np.abs(two_times - value))) for value in snapshot_evolution_times]
    )
    snapshot_grid_error = float(
        np.max(np.abs(two_times[snapshot_indices] - snapshot_evolution_times))
    )
    boson_basis = occupation_basis(int(two_settings["site_count"]), 2)
    hardcore_basis = occupation_basis(int(two_settings["site_count"]), 2, max_occupation=1)
    hamiltonians = {
        "strong": (boson_basis, build_hamiltonian(boson_basis, couplings, interactions)),
        "free": (boson_basis, build_hamiltonian(boson_basis, couplings)),
        "hardcore": (hardcore_basis, build_hamiltonian(hardcore_basis, couplings)),
    }
    two_density_rows: list[dict[str, Any]] = []
    correlator_rows: list[dict[str, Any]] = []
    two_densities: dict[tuple[str, str], np.ndarray] = {}
    two_snapshot_correlations: dict[tuple[str, str], np.ndarray] = {}
    two_norm_error = 0.0
    two_density_sum_error = 0.0
    correlator_sum_error = 0.0
    for model, (basis, hamiltonian) in hamiltonians.items():
        for launch, sites in two_settings["launches"].items():
            initial = fock_state(basis, sites)
            result = evolve_state(hamiltonian, initial, two_times, args.backend)
            actual_backend, accelerator = result.backend, result.accelerator
            density = site_density(result.states, basis)
            snapshot_correlators = two_particle_correlator(result.states[snapshot_indices], basis)
            two_densities[(model, launch)] = density
            two_snapshot_correlations[(model, launch)] = snapshot_correlators
            two_norm_error = max(two_norm_error, float(np.max(np.abs(state_norms(result.states) - 1.0))))
            two_density_sum_error = max(two_density_sum_error, float(np.max(np.abs(np.sum(density, axis=1) - 2.0))))
            correlator_sum_error = max(
                correlator_sum_error,
                float(np.max(np.abs(np.sum(snapshot_correlators, axis=(1, 2)) - 2.0))),
            )
            for time_index, time_ns in enumerate(two_times):
                for site, value in enumerate(density[time_index], start=1):
                    two_density_rows.append(
                        {"model": model, "launch": launch, "time_ns": time_ns, "site": site, "density": value}
                    )
            for snap_index, time_ns in enumerate(snapshot_times):
                for site_i in range(density.shape[1]):
                    for site_j in range(density.shape[1]):
                        correlator_rows.append(
                            {
                                "model": model,
                                "launch": launch,
                                "time_ns": time_ns,
                                "evolution_time_ns": snapshot_evolution_times[snap_index],
                                "site_i": site_i + 1,
                                "site_j": site_j + 1,
                                "G_ij": snapshot_correlators[snap_index, site_i, site_j],
                            }
                        )
    write_csv(
        data_dir / "two_particle_density.csv",
        ["model", "launch", "time_ns", "site", "density"],
        two_density_rows,
    )
    write_csv(
        data_dir / "two_particle_correlators.csv",
        ["model", "launch", "time_ns", "evolution_time_ns", "site_i", "site_j", "G_ij"],
        correlator_rows,
    )
    strong_to_hardcore = np.mean(
        [
            normalized_correlation_distance(
                two_snapshot_correlations[("strong", "Q6_Q7")][index],
                two_snapshot_correlations[("hardcore", "Q6_Q7")][index],
            )
            for index in range(len(snapshot_times))
        ]
    )
    strong_to_free = np.mean(
        [
            normalized_correlation_distance(
                two_snapshot_correlations[("strong", "Q6_Q7")][index],
                two_snapshot_correlations[("free", "Q6_Q7")][index],
            )
            for index in range(len(snapshot_times))
        ]
    )
    # Cross-check the eigendecomposition propagator against a mathematically
    # independent matrix-exponential backend.  This is deliberately performed
    # only at two printed S20 times so it remains a cheap canary while still
    # exercising both the interacting and free Hamiltonians.
    backend_crosscheck_error = 0.0
    for model, printed_time in (("strong", snapshot_times[0]), ("free", snapshot_times[-1])):
        basis, hamiltonian = hamiltonians[model]
        initial = fock_state(basis, two_settings["launches"]["Q6_Q7"])
        eigen_state = evolve_state(hamiltonian, initial, [printed_time], "numpy").states[0]
        expm_state = expm(-1.0j * hamiltonian * printed_time) @ initial
        backend_crosscheck_error = max(
            backend_crosscheck_error,
            float(np.max(np.abs(eigen_state - expm_state))),
        )
    t003_metrics = {
        "boson_basis_dimension": len(boson_basis),
        "hardcore_basis_dimension": len(hardcore_basis),
        "max_norm_error": two_norm_error,
        "max_density_sum_error": two_density_sum_error,
        "max_correlator_sum_error": correlator_sum_error,
        "mean_strong_to_hardcore_distance": float(strong_to_hardcore),
        "mean_strong_to_free_distance": float(strong_to_free),
        "s20_scientific_time_source": two_settings["correlator_time_source"],
        "source_pixels_used_for_time_selection": bool(
            two_settings["source_pixels_used_for_time_selection"]
        ),
        "s20_max_time_grid_error_ns": snapshot_grid_error,
        "independent_expm_backend_max_state_error": backend_crosscheck_error,
    }
    t003_rules = {
        "boson_basis_dimension_is_78": len(boson_basis) == 78,
        "hardcore_basis_dimension_is_66": len(hardcore_basis) == 66,
        "state_norm_preserved": two_norm_error < tolerance,
        "density_sums_to_two": two_density_sum_error < tolerance,
        "correlator_sums_to_two": correlator_sum_error < tolerance,
        "strong_pattern_closer_to_hardcore_than_free": bool(strong_to_hardcore < strong_to_free),
        "s20_printed_times_on_simulation_grid": snapshot_grid_error < 1.0e-12,
        "source_pixels_not_used_for_time_selection": not bool(
            two_settings["source_pixels_used_for_time_selection"]
        ),
        "independent_expm_backend_agrees": backend_crosscheck_error < tolerance,
    }
    t003 = check_payload(t003_metrics, t003_rules)
    write_json(check_dir / "T003_checks.json", t003)

    double_mask = two_times <= float(config["double_occupancy_stop_ns"]) + 1e-12
    double_times = two_times[double_mask]
    strong_basis, strong_hamiltonian = hamiltonians["strong"]
    adjacent_initial = fock_state(strong_basis, two_settings["launches"]["Q6_Q7"])
    adjacent_result = evolve_state(strong_hamiltonian, adjacent_initial, double_times, args.backend)
    double_correlators = two_particle_correlator(adjacent_result.states, strong_basis)
    double_occupancy = double_occupancy_probability(double_correlators)
    double_rows = [
        {"time_ns": time_ns, "site": site + 1, "probability_n_eq_2": double_occupancy[time_index, site]}
        for time_index, time_ns in enumerate(double_times)
        for site in range(double_occupancy.shape[1])
    ]
    write_csv(data_dir / "double_occupancy.csv", ["time_ns", "site", "probability_n_eq_2"], double_rows)
    max_double_occupancy = float(np.max(double_occupancy))
    t004_metrics = {
        "max_site_resolved_double_occupancy": max_double_occupancy,
        "paper_threshold": float(acceptance["double_occupancy_max"]),
        "time_window_ns": [float(double_times[0]), float(double_times[-1])],
    }
    t004_rules = {
        "double_occupancy_below_paper_threshold": max_double_occupancy < float(acceptance["double_occupancy_max"])
    }
    t004 = check_payload(t004_metrics, t004_rules)
    write_json(check_dir / "T004_checks.json", t004)

    disorder_settings = config["disorder_ensembles"]
    disorder_times = time_grid(disorder_settings)
    disorder_widths = np.asarray(disorder_settings["widths_mhz"], dtype=np.float64)
    sequence_count = int(disorder_settings["sequence_count"])
    disorder_rng = np.random.default_rng(int(disorder_settings["seed"]))
    base_couplings_mhz = np.asarray(config["couplings_mhz"], dtype=np.float64)
    base_interactions_mhz = np.asarray(config["interactions_mhz"], dtype=np.float64)
    one_disorder_basis = occupation_basis(
        int(disorder_settings["one_particle"]["site_count"]), 1
    )
    two_disorder_basis = occupation_basis(
        int(disorder_settings["two_particle"]["site_count"]), 2
    )
    one_disorder_initial = fock_state(
        one_disorder_basis, disorder_settings["one_particle"]["launch"]
    )
    two_disorder_initial = fock_state(
        two_disorder_basis, disorder_settings["two_particle"]["launch"]
    )
    one_disorder_density: dict[float, np.ndarray] = {}
    two_disorder_density: dict[float, np.ndarray] = {}
    disorder_norm_error = 0.0
    for width in disorder_widths:
        one_average = np.zeros((disorder_times.size, len(one_disorder_basis[0])))
        two_average = np.zeros((disorder_times.size, len(two_disorder_basis[0])))
        for _ in range(sequence_count):
            one_onsite_mhz = disorder_rng.uniform(
                -float(width) / 2.0,
                float(width) / 2.0,
                len(one_disorder_basis[0]),
            )
            one_effective_mhz = effective_couplings_from_detuning(
                base_couplings_mhz[: len(one_disorder_basis[0]) - 1],
                one_onsite_mhz,
            )
            one_disorder_hamiltonian = build_hamiltonian(
                one_disorder_basis,
                mhz_to_rad_per_ns(one_effective_mhz),
                onsite=mhz_to_rad_per_ns(one_onsite_mhz),
            )
            one_result = evolve_state(
                one_disorder_hamiltonian,
                one_disorder_initial,
                disorder_times,
                args.backend,
            )
            one_sequence_density = site_density(one_result.states, one_disorder_basis)
            one_average += one_sequence_density
            disorder_norm_error = max(
                disorder_norm_error,
                float(np.max(np.abs(np.sum(one_sequence_density, axis=1) - 1.0))),
            )

            two_onsite_mhz = disorder_rng.uniform(
                -float(width) / 2.0,
                float(width) / 2.0,
                len(two_disorder_basis[0]),
            )
            two_effective_mhz = effective_couplings_from_detuning(
                base_couplings_mhz[: len(two_disorder_basis[0]) - 1],
                two_onsite_mhz,
            )
            two_disorder_hamiltonian = build_hamiltonian(
                two_disorder_basis,
                mhz_to_rad_per_ns(two_effective_mhz),
                mhz_to_rad_per_ns(
                    base_interactions_mhz[: len(two_disorder_basis[0])]
                ),
                mhz_to_rad_per_ns(two_onsite_mhz),
            )
            two_result = evolve_state(
                two_disorder_hamiltonian,
                two_disorder_initial,
                disorder_times,
                args.backend,
            )
            two_sequence_density = site_density(two_result.states, two_disorder_basis)
            two_average += two_sequence_density
            disorder_norm_error = max(
                disorder_norm_error,
                float(np.max(np.abs(np.sum(two_sequence_density, axis=1) - 2.0))),
            )
        one_disorder_density[float(width)] = one_average / sequence_count
        two_disorder_density[float(width)] = two_average / sequence_count

    one_disorder_rows = [
        {
            "width_mhz": width,
            "sequence_count": sequence_count,
            "time_ns": time_ns,
            "site": site + 1,
            "density": density[time_index, site],
        }
        for width, density in one_disorder_density.items()
        for time_index, time_ns in enumerate(disorder_times)
        for site in range(density.shape[1])
    ]
    two_disorder_rows = [
        {
            "width_mhz": width,
            "sequence_count": sequence_count,
            "time_ns": time_ns,
            "site": site + 1,
            "density": density[time_index, site],
        }
        for width, density in two_disorder_density.items()
        for time_index, time_ns in enumerate(disorder_times)
        for site in range(density.shape[1])
    ]
    write_csv(
        data_dir / "disorder_density_one_particle.csv",
        ["width_mhz", "sequence_count", "time_ns", "site", "density"],
        one_disorder_rows,
    )
    write_csv(
        data_dir / "disorder_density_two_particle.csv",
        ["width_mhz", "sequence_count", "time_ns", "site", "density"],
        two_disorder_rows,
    )

    clean_one_mask = one_times <= disorder_times[-1] + 1.0e-12
    clean_two_mask = two_times <= disorder_times[-1] + 1.0e-12
    zero_width = float(disorder_widths[0])
    high_width = float(disorder_widths[-1])
    zero_one_error = float(
        np.max(
            np.abs(
                one_disorder_density[zero_width]
                - center_density[clean_one_mask]
            )
        )
    )
    zero_two_error = float(
        np.max(
            np.abs(
                two_disorder_density[zero_width]
                - two_densities[("strong", "Q6_Q7")][clean_two_mask]
            )
        )
    )
    late_mask = disorder_times >= 80.0
    one_launch_site = int(disorder_settings["one_particle"]["launch"][0])
    two_launch_sites = np.asarray(disorder_settings["two_particle"]["launch"], dtype=int)
    one_localization = {
        width: float(np.mean(density[late_mask, one_launch_site]))
        for width, density in one_disorder_density.items()
    }
    two_localization = {
        width: float(np.mean(np.sum(density[late_mask][:, two_launch_sites], axis=1) / 2.0))
        for width, density in two_disorder_density.items()
    }

    precision_settings = config["coupling_precision"]
    fidelity_times = time_grid(precision_settings)
    fidelity_basis = occupation_basis(11, 1)
    fidelity_couplings_mhz = base_couplings_mhz[:10]
    coupling_rng = np.random.default_rng(int(precision_settings["coupling_error_seed"]))
    relative_errors = coupling_rng.uniform(
        -float(precision_settings["relative_error_bound"]),
        float(precision_settings["relative_error_bound"]),
        fidelity_couplings_mhz.size,
    )
    perturbed_couplings_mhz = fidelity_couplings_mhz * (1.0 + relative_errors)
    precision_disorder_rng = np.random.default_rng(int(precision_settings["disorder_seed"]))
    precision_disorder_mhz = precision_disorder_rng.uniform(
        -float(precision_settings["disorder_width_mhz"]) / 2.0,
        float(precision_settings["disorder_width_mhz"]) / 2.0,
        len(fidelity_basis[0]),
    )
    dashed_couplings_mhz = effective_couplings_from_detuning(
        perturbed_couplings_mhz,
        precision_disorder_mhz,
    )
    ideal_hamiltonian = build_hamiltonian(
        fidelity_basis,
        mhz_to_rad_per_ns(fidelity_couplings_mhz),
    )
    perturbed_hamiltonian = build_hamiltonian(
        fidelity_basis,
        mhz_to_rad_per_ns(perturbed_couplings_mhz),
    )
    dashed_hamiltonian = build_hamiltonian(
        fidelity_basis,
        mhz_to_rad_per_ns(dashed_couplings_mhz),
        onsite=mhz_to_rad_per_ns(precision_disorder_mhz),
    )
    solid_fidelity: dict[str, np.ndarray] = {}
    dashed_fidelity: dict[str, np.ndarray] = {}
    fidelity_rows: list[dict[str, Any]] = []
    lindblad_trace_error = 0.0
    lindblad_hermiticity_error = 0.0
    zero_noise_fidelity_error = 0.0
    for launch, sites in precision_settings["launches"].items():
        initial_site = int(sites[0])
        initial_state = fock_state(fidelity_basis, sites)
        ideal_density = site_density(
            evolve_state(ideal_hamiltonian, initial_state, fidelity_times, args.backend).states,
            fidelity_basis,
        )
        perturbed_density = site_density(
            evolve_state(
                perturbed_hamiltonian,
                initial_state,
                fidelity_times,
                args.backend,
            ).states,
            fidelity_basis,
        )
        lindblad = evolve_single_excitation_lindblad(
            dashed_hamiltonian,
            initial_site,
            fidelity_times,
            config["t1_us"][:11],
            config["t2_star_us"][:11],
        )
        solid_fidelity[launch] = distribution_fidelity(ideal_density, perturbed_density)
        dashed_fidelity[launch] = distribution_fidelity(ideal_density, lindblad.site_density)
        identity_fidelity = distribution_fidelity(ideal_density, ideal_density)
        zero_noise_fidelity_error = max(
            zero_noise_fidelity_error,
            float(np.max(np.abs(identity_fidelity - 1.0))),
        )
        lindblad_trace_error = max(
            lindblad_trace_error,
            float(np.max(np.abs(lindblad.traces - 1.0))),
        )
        lindblad_hermiticity_error = max(
            lindblad_hermiticity_error,
            float(
                np.max(
                    np.abs(
                        lindblad.density_matrices
                        - np.swapaxes(lindblad.density_matrices.conj(), 1, 2)
                    )
                )
            ),
        )
        fidelity_rows.extend(
            {
                "launch": launch,
                "time_ns": time_ns,
                "ideal_vs_coupling_error": solid_fidelity[launch][time_index],
                "ideal_vs_coupling_error_decoherence_disorder": dashed_fidelity[launch][
                    time_index
                ],
            }
            for time_index, time_ns in enumerate(fidelity_times)
        )
    write_csv(
        data_dir / "coupling_precision_fidelity.csv",
        [
            "launch",
            "time_ns",
            "ideal_vs_coupling_error",
            "ideal_vs_coupling_error_decoherence_disorder",
        ],
        fidelity_rows,
    )
    fidelity_values = np.concatenate(
        [*solid_fidelity.values(), *dashed_fidelity.values()]
    )
    late_fidelity_decay = {
        launch: float(1.0 - np.mean(values[fidelity_times >= 200.0]))
        for launch, values in solid_fidelity.items()
    }
    t005_metrics = {
        "disorder_widths_mhz": disorder_widths.tolist(),
        "sequence_count": sequence_count,
        "seed": int(disorder_settings["seed"]),
        "max_ensemble_density_sum_error": disorder_norm_error,
        "zero_disorder_one_particle_max_abs_error": zero_one_error,
        "zero_disorder_two_particle_max_abs_error": zero_two_error,
        "late_one_particle_launch_density": one_localization,
        "late_two_particle_launch_fraction": two_localization,
        "maximum_absolute_relative_coupling_error": float(np.max(np.abs(relative_errors))),
        "maximum_absolute_precision_disorder_mhz": float(
            np.max(np.abs(precision_disorder_mhz))
        ),
        "fidelity_min": float(np.min(fidelity_values)),
        "fidelity_max": float(np.max(fidelity_values)),
        "zero_noise_fidelity_max_error": zero_noise_fidelity_error,
        "lindblad_max_trace_error": lindblad_trace_error,
        "lindblad_max_hermiticity_error": lindblad_hermiticity_error,
        "late_solid_fidelity_decay_by_launch": late_fidelity_decay,
        "central_decay_faster_than_both_edges": bool(
            late_fidelity_decay["Central"] > late_fidelity_decay["Leftmost"]
            and late_fidelity_decay["Central"] > late_fidelity_decay["Rightmost"]
        ),
        "central_decay_check_role": "reported diagnostic only; unpublished author seed prevents an exact-realization acceptance rule",
    }
    t005_rules = {
        "all_six_printed_widths_run": disorder_widths.tolist()
        == [0.0, 6.0, 12.0, 20.0, 60.0, 200.0],
        "fifty_sequences_per_width": sequence_count == 50,
        "ensemble_density_normalized": disorder_norm_error
        < float(acceptance["ensemble_normalization_atol"]),
        "zero_disorder_matches_clean_one_particle": zero_one_error
        < float(acceptance["zero_disorder_atol"]),
        "zero_disorder_matches_clean_two_particle": zero_two_error
        < float(acceptance["zero_disorder_atol"]),
        "large_disorder_localizes_one_particle": one_localization[high_width]
        > one_localization[zero_width],
        "large_disorder_localizes_two_particles": two_localization[high_width]
        > two_localization[zero_width],
        "coupling_errors_respect_published_bound": float(np.max(np.abs(relative_errors)))
        <= float(precision_settings["relative_error_bound"]),
        "frequency_disorder_respects_published_width": float(
            np.max(np.abs(precision_disorder_mhz))
        )
        <= float(precision_settings["disorder_width_mhz"]) / 2.0,
        "fidelity_is_bounded": bool(
            np.min(fidelity_values) >= -tolerance
            and np.max(fidelity_values) <= 1.0 + tolerance
        ),
        "zero_noise_fidelity_is_one": zero_noise_fidelity_error < tolerance,
        "lindblad_trace_preserved": lindblad_trace_error
        < float(acceptance["lindblad_trace_atol"]),
        "lindblad_hermitian": lindblad_hermiticity_error
        < float(acceptance["lindblad_trace_atol"]),
    }
    t005 = check_payload(t005_metrics, t005_rules)
    t005["parameter_match"] = {
        "Figs. S9-S10": "paper_exact declared equivalence class",
        "Fig. S11": "reconstructed because the author seed and collapse convention are unpublished",
    }
    write_json(check_dir / "T005_checks.json", t005)

    signature = {
        "one_density_Q6": center_density,
        "one_connected_Q6_snapshot": center_correlation[snapshot_index],
        "two_density_strong_Q6_Q7": two_densities[("strong", "Q6_Q7")],
        "two_correlator_strong_Q6_Q7": two_snapshot_correlations[("strong", "Q6_Q7")],
        "double_occupancy_Q6_Q7": double_occupancy,
        "disorder_one_W200": one_disorder_density[high_width],
        "disorder_two_W200": two_disorder_density[high_width],
        "fidelity_central_solid": solid_fidelity["Central"],
        "fidelity_central_dashed": dashed_fidelity["Central"],
    }
    np.savez_compressed(data_dir / "backend_signature.npz", **signature)
    parity: dict[str, Any] | None = None
    if args.reference_signature:
        parity = compare_signature(
            signature,
            args.reference_signature,
            float(acceptance["backend_parity_atol"]),
            float(acceptance["backend_parity_rtol"]),
        )
        write_json(check_dir / "backend_parity.json", parity)

    if not args.no_plots:
        render_figures(
            figure_dir,
            one_times,
            one_density,
            center_entropy,
            center_correlation,
            center_concurrence,
            snapshot_index,
            center_rms_distance,
            velocity_scale,
            reported_velocity,
            two_snapshot_correlations,
            snapshot_times,
            snapshot_evolution_times,
            double_times,
            double_occupancy,
        )
        render_robustness_figures(
            figure_dir,
            disorder_times,
            disorder_widths,
            one_disorder_density,
            two_disorder_density,
            fidelity_times,
            solid_fidelity,
            dashed_fidelity,
        )

    overall_rules = {
        "T001": t001["status"] == "passed",
        "T002": t002["status"] == "passed",
        "T003": t003["status"] == "passed",
        "T004": t004["status"] == "passed",
        "T005": t005["status"] == "passed",
    }
    if parity is not None:
        overall_rules["backend_parity"] = parity["status"] == "passed"
    overall = {
        "status": "passed" if all(overall_rules.values()) else "failed",
        "targets": overall_rules,
        "backend": actual_backend,
        "accelerator": accelerator,
    }
    write_json(check_dir / "overall_acceptance.json", overall)
    machine_profile = {
        "paper_id": config["paper_id"],
        "backend": actual_backend,
        "accelerator": accelerator,
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "machine": platform.machine(),
        "matrix_dimensions": {"one_particle": len(one_basis), "two_boson": len(boson_basis), "hardcore": len(hardcore_basis)},
        "elapsed_seconds": time.perf_counter() - started,
    }
    write_json(output_dir / "machine_profile.json", machine_profile)
    write_json(output_dir / "run_summary.json", {"acceptance": overall, "machine": machine_profile})
    return {"acceptance": overall, "machine": machine_profile}


if __name__ == "__main__":
    summary = run(parse_args())
    print(json.dumps(summary, indent=2, ensure_ascii=False))
