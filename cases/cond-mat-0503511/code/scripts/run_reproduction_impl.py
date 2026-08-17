#!/usr/bin/env python3
"""Run all five numerical targets from clean-room scientific inputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from zurek_qpt.model import (  # noqa: E402
    evolve_open_chain,
    final_observables,
    landau_zener_fidelity,
    low_excitation_spectrum,
    periodic_mode_observables,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def effective_hash(config_path: Path) -> tuple[str, str]:
    config_hash = sha256_file(config_path)
    digest = hashlib.sha256()
    for path in [Path(__file__).resolve(), SRC / "zurek_qpt" / "model.py"]:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return config_hash, digest.hexdigest()


def job_id(n_spins: int, rate: float) -> str:
    return f"N{n_spins:03d}-r{rate:.12g}".replace("+", "")


def compute_job(
    n_spins: int, rate: float, parameters: dict[str, Any], solver: dict[str, Any]
) -> dict[str, Any]:
    started = time.perf_counter()
    evolved = evolve_open_chain(
        n_spins,
        rate,
        field_start=float(parameters["field_start"]),
        field_end=float(parameters["field_end"]),
        coupling_w=float(parameters["coupling_w"]),
        hbar=float(parameters["hbar"]),
        rtol=float(solver["rtol"]),
        atol=float(solver["atol"]),
    )
    payload: dict[str, Any] = {
        "n_spins": n_spins,
        "rate_tau0_over_tauq": rate,
        "tau_q_hbar_over_w": evolved.tau_q,
        "nfev": evolved.nfev,
        "antisymmetry_error": evolved.antisymmetry_error,
        "purity_error": evolved.purity_error,
        "elapsed_seconds": time.perf_counter() - started,
    }
    payload.update(final_observables(evolved.covariance))
    return payload


def load_or_run_jobs(
    jobs: list[tuple[int, float]],
    *,
    output_root: Path,
    parameters: dict[str, Any],
    solver: dict[str, Any],
    config_hash: str,
    implementation_hash: str,
    resume: bool,
) -> list[dict[str, Any]]:
    checkpoint_root = output_root / "checkpoints"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    results: dict[tuple[int, float], dict[str, Any]] = {}
    pending: list[tuple[int, float]] = []
    for n_spins, rate in jobs:
        path = checkpoint_root / f"{job_id(n_spins, rate)}.json"
        if resume and path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if (
                payload.get("config_sha256") == config_hash
                and payload.get("implementation_sha256") == implementation_hash
            ):
                results[(n_spins, rate)] = payload["result"]
                continue
        pending.append((n_spins, rate))

    workers = max(1, int(solver.get("thread_workers", 1)))
    with ThreadPoolExecutor(
        max_workers=workers, thread_name_prefix="open-chain"
    ) as executor:
        futures = {
            executor.submit(compute_job, n_spins, rate, parameters, solver): (
                n_spins,
                rate,
            )
            for n_spins, rate in pending
        }
        for future in as_completed(futures):
            n_spins, rate = futures[future]
            result = future.result()
            results[(n_spins, rate)] = result
            atomic_json(
                checkpoint_root / f"{job_id(n_spins, rate)}.json",
                {
                    "schema_version": 1,
                    "config_sha256": config_hash,
                    "implementation_sha256": implementation_hash,
                    "result": result,
                },
            )
            print(
                f"completed N={n_spins} rate={rate:.7g} kinks={result['kink_count']:.7g} f={result['fidelity_exact']:.7g}",
                flush=True,
            )
    return [results[job] for job in jobs]


def build_jobs(
    config: dict[str, Any],
) -> tuple[list[tuple[int, float]], dict[int, list[float]]]:
    parameters = config["parameters"]
    grids = config["grids"]
    jobs: set[tuple[int, float]] = set()
    base_rates = [float(value) for value in grids["dynamic_rates_tau0_over_tauq"]]
    dynamic_lengths = set(parameters["main_chain_lengths"]) | set(
        parameters["fig2c_chain_lengths"]
    )
    for n_spins in dynamic_lengths:
        jobs.update((int(n_spins), rate) for rate in base_rates)
    fixed_rate = 0.5 / float(parameters["fixed_tau_q_hbar_over_w"])
    for n_spins in parameters["scaling_chain_lengths"]:
        jobs.add((int(n_spins), fixed_rate))
    target = float(parameters["fidelity_target"])
    coefficient = float(parameters["landau_zener_probe_coefficient"])
    multipliers = [float(value) for value in grids["tau99_probe_multipliers"]]
    probes: dict[int, list[float]] = {}
    for n_spins in parameters["scaling_chain_lengths"]:
        tau_guess = -math.log(1.0 - target) * int(n_spins) ** 2 / coefficient
        rates = sorted({0.5 / (tau_guess * multiplier) for multiplier in multipliers})
        probes[int(n_spins)] = rates
        jobs.update((int(n_spins), rate) for rate in rates)
    return sorted(jobs), probes


def interpolate_tau99(
    results: list[dict[str, Any]], n_spins: int, target: float, probe_rates: list[float]
) -> float:
    selected = [
        row
        for row in results
        if row["n_spins"] == n_spins
        and any(abs(row["rate_tau0_over_tauq"] - rate) < 1e-14 for rate in probe_rates)
    ]
    selected.sort(key=lambda row: row["tau_q_hbar_over_w"])
    tau = np.array([row["tau_q_hbar_over_w"] for row in selected], dtype=float)
    fidelity = np.maximum.accumulate(
        np.array([row["fidelity_exact"] for row in selected], dtype=float)
    )
    if fidelity[0] > target or fidelity[-1] < target:
        raise RuntimeError(f"tau99 probes do not bracket f={target} for N={n_spins}")
    return float(np.interp(target, fidelity, tau))


def fit_power(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    slope, intercept = np.polyfit(np.log(x), np.log(y), 1)
    return float(slope), float(np.exp(intercept))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["parameters"]["boundary_condition"] != "open":
        raise ValueError(
            "primary production profile must use the printed open boundary"
        )
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    config_hash, implementation_hash = effective_hash(config_path)
    started = time.perf_counter()

    jobs, probe_rates = build_jobs(config)
    results = load_or_run_jobs(
        jobs,
        output_root=output_root,
        parameters=config["parameters"],
        solver=config["solver"],
        config_hash=config_hash,
        implementation_hash=implementation_hash,
        resume=args.resume,
    )
    by_key = {(row["n_spins"], row["rate_tau0_over_tauq"]): row for row in results}
    parameters, grids = config["parameters"], config["grids"]

    fig1_rows: list[dict[str, Any]] = []
    fig2c_rows: list[dict[str, Any]] = []
    fig3_rows: list[dict[str, Any]] = []
    base_rates = set(grids["dynamic_rates_tau0_over_tauq"])
    for row in results:
        rate, n_spins = row["rate_tau0_over_tauq"], row["n_spins"]
        if n_spins in parameters["main_chain_lengths"] and rate in base_rates:
            if rate <= grids["fig1_rate_max"]:
                fig1_rows.append(
                    {
                        key: row[key]
                        for key in [
                            "n_spins",
                            "rate_tau0_over_tauq",
                            "kink_density_per_spin",
                        ]
                    }
                )
            fig3_rows.append(
                {
                    key: row[key]
                    for key in [
                        "n_spins",
                        "rate_tau0_over_tauq",
                        "kink_count",
                        "fidelity_exact",
                    ]
                }
            )
        if (
            n_spins in parameters["fig2c_chain_lengths"]
            and rate in base_rates
            and rate <= grids["fig2c_rate_max"]
        ):
            fig2c_rows.append(
                {
                    key: row[key]
                    for key in [
                        "n_spins",
                        "rate_tau0_over_tauq",
                        "fidelity_lower_bound",
                        "fidelity_upper_bound",
                        "fidelity_exact",
                    ]
                }
            )

    target = float(parameters["fidelity_target"])
    fixed_rate = 0.5 / float(parameters["fixed_tau_q_hbar_over_w"])
    fig2b_rows = []
    for n_spins in parameters["scaling_chain_lengths"]:
        fixed = by_key[(n_spins, fixed_rate)]
        tau_q_hbar_over_w = interpolate_tau99(
            results, n_spins, target, probe_rates[n_spins]
        )
        tau_q_over_tau0 = (
            tau_q_hbar_over_w
            * 2.0
            * float(parameters["coupling_w"])
            / float(parameters["hbar"])
        )
        fig2b_rows.append(
            {
                "n_spins": n_spins,
                "tau_q_hbar_over_w_for_target_fidelity": tau_q_hbar_over_w,
                "tau_q_over_tau0_for_target_fidelity": tau_q_over_tau0,
                "fixed_tau_q_hbar_over_w": parameters["fixed_tau_q_hbar_over_w"],
                "fixed_time_fidelity_exact": fixed["fidelity_exact"],
                "fixed_time_fidelity_lower": fixed["fidelity_lower_bound"],
                "fixed_time_fidelity_upper": fixed["fidelity_upper_bound"],
            }
        )

    tau_power, tau_prefactor = fit_power(
        np.array([row["n_spins"] for row in fig2b_rows], dtype=float),
        np.array(
            [row["tau_q_over_tau0_for_target_fidelity"] for row in fig2b_rows],
            dtype=float,
        ),
    )
    fig2b_lzf_coefficient = float(parameters["fig2b_lzf_coefficient"])
    for row in fig2b_rows:
        n_spins = int(row["n_spins"])
        row["tau_q_power_fit"] = tau_prefactor * n_spins**tau_power
        row["fixed_time_lzf_fit"] = landau_zener_fidelity(
            n_spins,
            float(parameters["fixed_tau_q_hbar_over_w"]),
            coefficient_a=fig2b_lzf_coefficient,
        )

    fields = np.linspace(
        grids["spectrum_field_start"],
        grids["spectrum_field_end"],
        int(grids["spectrum_field_points"]),
    )
    spectrum_curves = low_excitation_spectrum(
        int(parameters["fig2a_chain_length"]),
        fields,
        coupling_w=float(parameters["coupling_w"]),
        max_particles=int(grids["spectrum_max_particles"]),
        max_energy=float(grids["spectrum_max_energy"]),
    )
    spectrum_rows: list[dict[str, Any]] = []
    for curve_id, curve in enumerate(spectrum_curves):
        subset = "+".join(str(value) for value in curve["subset"]) or "vacuum"
        for field, energy in zip(curve["field_values"], curve["energies"], strict=True):
            if energy <= grids["spectrum_max_energy"]:
                spectrum_rows.append(
                    {
                        "curve_id": curve_id,
                        "subset": subset,
                        "particle_count": curve["particle_count"],
                        "parity": curve["parity"],
                        "field_j_over_w": float(field),
                        "energy_over_w": float(energy),
                    }
                )

    kzm_low, kzm_high = grids["kzm_fit_window"]
    n_max = max(parameters["main_chain_lengths"])
    kzm_fits: dict[int, tuple[float, float]] = {}
    for n_spins in parameters["main_chain_lengths"]:
        selected = [
            row
            for row in fig3_rows
            if row["n_spins"] == n_spins
            and kzm_low <= row["rate_tau0_over_tauq"] <= kzm_high
        ]
        kzm_fits[int(n_spins)] = fit_power(
            np.array([row["rate_tau0_over_tauq"] for row in selected]),
            np.array([row["kink_count"] for row in selected]),
        )

    nmax_exponent, nmax_count_prefactor = kzm_fits[n_max]
    nmax_density_prefactor = nmax_count_prefactor / n_max
    for row in fig1_rows:
        rate = float(row["rate_tau0_over_tauq"])
        row["n100_kzm_fit_density"] = (
            nmax_density_prefactor * rate**nmax_exponent
            if row["n_spins"] == n_max
            else ""
        )

    fig2c_coefficients = {
        int(key): float(value)
        for key, value in parameters["fig2c_lzf_coefficients_by_chain"].items()
    }
    for row in fig2c_rows:
        n_spins = int(row["n_spins"])
        tau_q = 0.5 / float(row["rate_tau0_over_tauq"])
        row["lzf_fit_coefficient"] = fig2c_coefficients[n_spins]
        row["lzf_fit_fidelity"] = landau_zener_fidelity(
            n_spins,
            tau_q,
            coefficient_a=fig2c_coefficients[n_spins],
        )

    fig3_lzf_coefficient = float(parameters["fig3_lzf_coefficient"])
    for row in fig3_rows:
        n_spins = int(row["n_spins"])
        rate = float(row["rate_tau0_over_tauq"])
        exponent, prefactor = kzm_fits[n_spins]
        row["kzm_fit_kink_count"] = prefactor * rate**exponent
        row["kzm_fit_exponent"] = exponent
        row["lzf_fit_coefficient"] = fig3_lzf_coefficient
        row["lzf_kink_estimate"] = 1.0 - landau_zener_fidelity(
            n_spins,
            0.5 / rate,
            coefficient_a=fig3_lzf_coefficient,
        )

    data_root = output_root / "data"
    write_csv(
        data_root / "fig1_kink_density.csv",
        fig1_rows,
        [
            "n_spins",
            "rate_tau0_over_tauq",
            "kink_density_per_spin",
            "n100_kzm_fit_density",
        ],
    )
    write_csv(
        data_root / "fig2a_spectrum.csv",
        spectrum_rows,
        [
            "curve_id",
            "subset",
            "particle_count",
            "parity",
            "field_j_over_w",
            "energy_over_w",
        ],
    )
    write_csv(
        data_root / "fig2b_fidelity_scaling.csv",
        fig2b_rows,
        [
            "n_spins",
            "tau_q_hbar_over_w_for_target_fidelity",
            "tau_q_over_tau0_for_target_fidelity",
            "fixed_tau_q_hbar_over_w",
            "fixed_time_fidelity_exact",
            "fixed_time_fidelity_lower",
            "fixed_time_fidelity_upper",
            "tau_q_power_fit",
            "fixed_time_lzf_fit",
        ],
    )
    write_csv(
        data_root / "fig2c_fidelity_bounds.csv",
        fig2c_rows,
        [
            "n_spins",
            "rate_tau0_over_tauq",
            "fidelity_lower_bound",
            "fidelity_upper_bound",
            "fidelity_exact",
            "lzf_fit_coefficient",
            "lzf_fit_fidelity",
        ],
    )
    write_csv(
        data_root / "fig3_kink_count.csv",
        fig3_rows,
        [
            "n_spins",
            "rate_tau0_over_tauq",
            "kink_count",
            "fidelity_exact",
            "kzm_fit_kink_count",
            "kzm_fit_exponent",
            "lzf_fit_coefficient",
            "lzf_kink_estimate",
        ],
    )

    nmax_rows = [
        row
        for row in fig1_rows
        if row["n_spins"] == n_max and kzm_low <= row["rate_tau0_over_tauq"] <= kzm_high
    ]
    kzm_exponent, kzm_prefactor = fit_power(
        np.array([row["rate_tau0_over_tauq"] for row in nmax_rows]),
        np.array([row["kink_density_per_spin"] for row in nmax_rows]),
    )
    critical_rows = [
        row
        for row in spectrum_rows
        if row["subset"] == "0+1" and abs(row["field_j_over_w"] - 1.0) < 1e-12
    ]
    critical_gap = float(critical_rows[0]["energy_over_w"])
    asymptotic_gap = 4.0 * np.pi / int(parameters["fig2a_chain_length"])
    critical_gap_relative_error = abs(critical_gap - asymptotic_gap) / asymptotic_gap
    bound_violation = max(
        max(
            row["fidelity_lower_bound"] - row["fidelity_exact"],
            row["fidelity_exact"] - row["fidelity_upper_bound"],
            0.0,
        )
        for row in results
    )

    cross_rate = 0.05
    open_cross = by_key.get((n_max, cross_rate)) or compute_job(
        n_max, cross_rate, parameters, config["solver"]
    )
    periodic_cross = periodic_mode_observables(n_max, cross_rate)
    periodic_open_gap = abs(
        periodic_cross["kink_density_per_spin"] - open_cross["kink_density_per_spin"]
    ) / max(open_cross["kink_density_per_spin"], 1e-12)

    spectrum_curve_counts = {
        parity: len(
            {int(row["curve_id"]) for row in spectrum_rows if row["parity"] == parity}
        )
        for parity in ["accessible_even", "inaccessible_odd"]
    }
    expected_spectrum_curve_counts = {
        "accessible_even": 1
        + int(parameters["fig2a_chain_length"])
        * (int(parameters["fig2a_chain_length"]) - 1)
        // 2,
        "inaccessible_odd": int(parameters["fig2a_chain_length"]),
    }

    acceptance = config["acceptance"]
    metrics = {
        "max_purity_error": max(row["purity_error"] for row in results),
        "max_antisymmetry_error": max(row["antisymmetry_error"] for row in results),
        "max_fidelity_bound_violation": bound_violation,
        "n100_kzm_exponent": kzm_exponent,
        "n100_kzm_prefactor": kzm_prefactor,
        "tau99_power": tau_power,
        "tau99_prefactor": tau_prefactor,
        "tau99_axis_unit_conversion_max_error": max(
            abs(
                row["tau_q_over_tau0_for_target_fidelity"]
                - row["tau_q_hbar_over_w_for_target_fidelity"]
                * 2.0
                * float(parameters["coupling_w"])
                / float(parameters["hbar"])
            )
            for row in fig2b_rows
        ),
        "n20_critical_accessible_gap": critical_gap,
        "n20_asymptotic_4pi_over_n": asymptotic_gap,
        "critical_gap_relative_error": critical_gap_relative_error,
        "periodic_open_kink_relative_gap": periodic_open_gap,
        "periodic_crosscheck": periodic_cross,
        "spectrum_curve_counts": spectrum_curve_counts,
        "expected_spectrum_curve_counts": expected_spectrum_curve_counts,
    }
    gates = {
        "covariance_purity": metrics["max_purity_error"]
        <= acceptance["max_purity_error"],
        "covariance_antisymmetry": metrics["max_antisymmetry_error"]
        <= acceptance["max_antisymmetry_error"],
        "fidelity_bounds": bound_violation
        <= acceptance["max_fidelity_bound_violation"],
        "critical_gap": critical_gap_relative_error
        <= acceptance["critical_gap_relative_tolerance"],
        "kzm_exponent": acceptance["kzm_exponent_range"][0]
        <= kzm_exponent
        <= acceptance["kzm_exponent_range"][1],
        "tau99_power": acceptance["tau99_power_range"][0]
        <= tau_power
        <= acceptance["tau99_power_range"][1],
        "tau99_axis_units": metrics["tau99_axis_unit_conversion_max_error"] <= 1.0e-12,
        "periodic_open_crosscheck": periodic_open_gap
        <= acceptance["max_periodic_open_kink_relative_gap"],
        "spectrum_sector_coverage": spectrum_curve_counts
        == expected_spectrum_curve_counts,
    }
    checks = {
        "schema_version": 1,
        "targets": ["T001", "T002", "T003", "T004", "T005"],
        "author_code_used": False,
        "author_arrays_used": False,
        "source_pixels_used_as_numeric_input": False,
        "metrics": metrics,
        "gates": gates,
        "status": "passed" if all(gates.values()) else "failed",
    }
    atomic_json(output_root / "checks" / "science_checks.json", checks)

    output_files = sorted(data_root.glob("*.csv")) + [
        output_root / "checks" / "science_checks.json"
    ]
    atomic_json(
        output_root / "checks" / "generated_data_manifest.json",
        {
            "schema_version": 1,
            "config_sha256": config_hash,
            "implementation_sha256": implementation_hash,
            "files": [
                {
                    "path": str(path.relative_to(output_root)),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
                for path in output_files
            ],
        },
    )
    atomic_json(
        output_root / "checks" / "run_summary.json",
        {
            "schema_version": 1,
            "profile": config["profile"],
            "jobs_total": len(jobs),
            "elapsed_seconds": time.perf_counter() - started,
            "config_sha256": config_hash,
            "implementation_sha256": implementation_hash,
            "science_status": checks["status"],
        },
    )
    print(
        json.dumps({"status": checks["status"], "metrics": metrics}, indent=2),
        flush=True,
    )
    return 0 if checks["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
