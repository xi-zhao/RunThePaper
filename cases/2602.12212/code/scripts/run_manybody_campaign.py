#!/usr/bin/env python3
"""Resumable CPU/A100 campaign for Figs. 2 and S1-S6."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

import leaf_thermodynamics as leaf  # noqa: E402


NONINTEGRABLE_FIELD = (
    (np.sqrt(5.0) + 5.0) / 8.0,
    0.5,
    np.sqrt(5.0) / 2.0,
)
DM = np.pi / 20.0
BETAS = (0.25, 0.75, 1.75)
THRESHOLDS = np.linspace(0.0, 0.17, 69)
GROUP_H0_Z = {"main": 1.5, "supplemental": 0.5, "integrable": 0.5}
GROUPS = tuple(GROUP_H0_Z)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(json_ready(payload), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def nvidia_profile() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return {"available": False}
    rows = []
    for line in completed.stdout.strip().splitlines():
        name, total, used, utilization = [item.strip() for item in line.split(",")]
        rows.append(
            {
                "name": name,
                "memory_total_mib": int(total),
                "memory_used_mib": int(used),
                "utilization_percent": int(utilization),
            }
        )
    return {"available": bool(rows), "gpus": rows}


def active_compute_processes() -> list[dict[str, str]]:
    command = [
        "nvidia-smi",
        "--query-compute-apps=pid,process_name,used_memory",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []
    processes = []
    for line in completed.stdout.strip().splitlines():
        if not line.strip():
            continue
        pid, name, used = [item.strip() for item in line.split(",", maxsplit=2)]
        processes.append({"pid": pid, "process_name": name, "used_memory_mib": used})
    return processes


def enforce_accelerator_contract(
    backend: str,
    *,
    require_a100: bool,
    require_idle_gpu: bool,
) -> dict[str, Any]:
    if backend != "cupy":
        if require_a100 or require_idle_gpu:
            raise RuntimeError("A100/idle checks require backend='cupy'")
        return {"available": False, "query_skipped": "cpu_backend"}
    profile = nvidia_profile()
    if require_a100:
        names = [str(item["name"]) for item in profile.get("gpus", [])]
        if not any("A100" in name for name in names):
            raise RuntimeError(f"A100 required, observed GPUs: {names or 'none'}")
    if require_idle_gpu:
        processes = active_compute_processes()
        if processes:
            raise RuntimeError(f"GPU has active compute processes: {processes}")
    return profile


def dense_on_backend(matrix: Any, backend: str) -> Any:
    xp = leaf.array_module(backend)
    return xp.asarray(matrix.toarray())


def observable_set(length: int, group: str) -> list[tuple[str, leaf.PauliOps]]:
    all_observables = leaf.central_local_observables(length)
    if group == "main":
        wanted = {"sigma_z", "sigma_z_sigma_z"}
        return [item for item in all_observables if item[0] in wanted]
    return all_observables


def curve_rows(
    values: Any,
    *,
    length: int,
    beta: float,
    group: str,
    observable: str,
    family: str,
    boundary: str,
) -> list[dict[str, Any]]:
    curve = leaf.typicality_curve(
        values,
        thresholds=THRESHOLDS,
        shell_width=max(1, int(round(np.sqrt(1 << length)))),
        shell_mode="centred",
    )
    rows = []
    for delta, count, log_count in zip(
        curve["thresholds"],
        curve["counts"],
        curve["log_d_counts"],
        strict=True,
    ):
        rows.append(
            {
                "artifact_state": "final_reproduction_candidate",
                "parameter_match": "paper_exact_reconstructed_metadata",
                "group": group,
                "length": length,
                "dimension": 1 << length,
                "beta": beta,
                "observable": observable,
                "family": family,
                "boundary": boundary,
                "shell_mode": curve["shell_mode"],
                "shell_width": curve["shell_width"],
                "delta": float(delta),
                "count": int(count),
                "log_d_count": (
                    float(log_count) if np.isfinite(log_count) else ""
                ),
            }
        )
    return rows


def compression_rows(
    *,
    length: int,
    beta: float,
    group: str,
    decomposition: str,
    energy_density: np.ndarray,
    entropy: np.ndarray,
    populations: np.ndarray,
) -> list[dict[str, Any]]:
    return [
        {
            "artifact_state": "final_reproduction_candidate",
            "parameter_match": "paper_exact_reconstructed_metadata",
            "group": group,
            "length": length,
            "beta": beta,
            "decomposition": decomposition,
            "representative_index": index,
            "energy_density": float(energy_density[index]),
            "diagonal_entropy": float(entropy[index]),
            "participation_number": float(np.exp(entropy[index])),
            "population": float(populations[index]),
        }
        for index in range(entropy.size)
    ]


def run_standard_group(
    *,
    length: int,
    group: str,
    h0_z: float,
    boundary: str,
    backend: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    xp = leaf.array_module(backend)
    started = time.perf_counter()
    h_sparse = leaf.spin_chain_hamiltonian(
        length,
        NONINTEGRABLE_FIELD,
        DM,
        boundary=boundary,
    )
    h0_sparse = leaf.spin_chain_hamiltonian(
        length,
        (0.0, 0.0, h0_z),
        0.0,
        boundary=boundary,
    )
    h = dense_on_backend(h_sparse, backend)
    h0 = dense_on_backend(h0_sparse, backend)
    build_seconds = time.perf_counter() - started

    diagonalization_started = time.perf_counter()
    h_energies, h_basis = xp.linalg.eigh(h)
    h0_energies, h0_basis = xp.linalg.eigh(h0)
    leaf.synchronize(backend)
    diagonalization_seconds = time.perf_counter() - diagonalization_started

    transform_started = time.perf_counter()
    h_in_h0_basis = h0_basis.conj().T @ h @ h0_basis
    overlap_eig = h_basis.conj().T @ h0_basis
    entropy_eig = leaf.diagonal_entropy(overlap_eig, backend=backend)
    energy_eig = xp.real(xp.diag(h_in_h0_basis))
    leaf.synchronize(backend)
    transform_seconds = time.perf_counter() - transform_started

    observables = observable_set(length, group)
    typicality: list[dict[str, Any]] = []
    compression: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    entropy_eig_np = np.real(leaf.to_numpy(entropy_eig))
    energy_eig_np = np.real(leaf.to_numpy(energy_eig)) / length

    if group in {"main", "supplemental"}:
        for label, ops in observables:
            h_values = leaf.pauli_expectations(
                h_basis,
                length,
                ops,
                backend=backend,
            )
            h0_values = (
                leaf.pauli_expectations(
                    h0_basis,
                    length,
                    ops,
                    backend=backend,
                )
                if group == "main"
                else None
            )
            for beta in BETAS:
                typicality.extend(
                    curve_rows(
                        leaf.to_numpy(h_values),
                        length=length,
                        beta=beta,
                        group=group,
                        observable=label,
                        family="eth_nonintegrable",
                        boundary=boundary,
                    )
                )
                if group == "main":
                    assert h0_values is not None
                    typicality.extend(
                        curve_rows(
                            leaf.to_numpy(h0_values),
                            length=length,
                            beta=beta,
                            group=group,
                            observable=label,
                            family="eth_integrable",
                            boundary=boundary,
                        )
                    )

    for beta in BETAS:
        beta_started = time.perf_counter()
        rho_eigenvalues = leaf.thermal_weights(h0_energies, beta, backend=backend)
        ensemble = leaf.minimum_variance_ensemble(
            rho_eigenvalues,
            h_in_h0_basis,
            rho_basis=h0_basis,
            thermal_energies=h0_energies,
            beta=beta,
            backend=backend,
        )
        invariants = leaf.ensemble_invariants(
            rho_eigenvalues,
            h_in_h0_basis,
            ensemble,
        )
        for label, ops in observables:
            values = leaf.pauli_expectations(
                ensemble.representatives,
                length,
                ops,
                backend=backend,
            )
            typicality.extend(
                curve_rows(
                    leaf.to_numpy(values),
                    length=length,
                    beta=beta,
                    group=group,
                    observable=label,
                    family="leaf",
                    boundary=boundary,
                )
            )

        overlap_mv = h_basis.conj().T @ ensemble.representatives
        entropy_mv = leaf.diagonal_entropy(overlap_mv, backend=backend)
        entropy_mv_np = np.real(leaf.to_numpy(entropy_mv))
        populations_np = np.real(leaf.to_numpy(ensemble.populations))
        energy_mv_np = np.real(leaf.to_numpy(ensemble.energies)) / length
        rho_eigenvalues_np = np.real(leaf.to_numpy(rho_eigenvalues))
        compression.extend(
            compression_rows(
                length=length,
                beta=beta,
                group=group,
                decomposition="eigen",
                energy_density=energy_eig_np,
                entropy=entropy_eig_np,
                populations=rho_eigenvalues_np,
            )
        )
        compression.extend(
            compression_rows(
                length=length,
                beta=beta,
                group=group,
                decomposition="min_variance",
                energy_density=energy_mv_np,
                entropy=entropy_mv_np,
                populations=populations_np,
            )
        )
        weighted_eig = float(np.sum(rho_eigenvalues_np * entropy_eig_np))
        weighted_mv = float(np.sum(populations_np * entropy_mv_np))
        leaf.synchronize(backend)
        summaries.append(
            {
                "beta": beta,
                "invariants": invariants,
                "weighted_diagonal_entropy_eigen": weighted_eig,
                "weighted_diagonal_entropy_min_variance": weighted_mv,
                "entropy_density_gain": (weighted_eig - weighted_mv) / length,
                "beta_runtime_seconds": time.perf_counter() - beta_started,
            }
        )
        del ensemble, overlap_mv, entropy_mv, rho_eigenvalues
        if backend == "cupy":  # pragma: no cover - exercised on A100 only
            xp.get_default_memory_pool().free_all_blocks()

    payload = {
        "group": group,
        "length": length,
        "dimension": 1 << length,
        "boundary": boundary,
        "backend": backend,
        "h0_z": h0_z,
        "betas": list(BETAS),
        "shell_width": max(1, int(round(np.sqrt(1 << length)))),
        "timing": {
            "build_seconds": build_seconds,
            "joint_diagonalization_seconds": diagonalization_seconds,
            "basis_transform_seconds": transform_seconds,
            "total_seconds": time.perf_counter() - started,
        },
        "summaries": summaries,
    }
    return typicality, compression, payload


def run_integrable_group(
    *,
    length: int,
    h0_z: float,
    boundary: str,
    backend: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    xp = leaf.array_module(backend)
    started = time.perf_counter()
    h = dense_on_backend(
        leaf.spin_chain_hamiltonian(
            length,
            NONINTEGRABLE_FIELD,
            DM,
            boundary=boundary,
        ),
        backend,
    )
    h0 = dense_on_backend(
        leaf.spin_chain_hamiltonian(
            length,
            (0.0, 0.0, h0_z),
            0.0,
            boundary=boundary,
        ),
        backend,
    )
    h_energies, h_basis = xp.linalg.eigh(h)
    h0_energies, h0_basis = xp.linalg.eigh(h0)
    h0_in_h_basis = h_basis.conj().T @ h0 @ h_basis
    beta = 0.25
    rho_eigenvalues = leaf.thermal_weights(h_energies, beta, backend=backend)
    ensemble = leaf.minimum_variance_ensemble(
        rho_eigenvalues,
        h0_in_h_basis,
        rho_basis=h_basis,
        thermal_energies=h_energies,
        beta=beta,
        backend=backend,
    )
    invariants = leaf.ensemble_invariants(
        rho_eigenvalues,
        h0_in_h_basis,
        ensemble,
    )
    typicality: list[dict[str, Any]] = []
    for label, ops in observable_set(length, "integrable"):
        benchmark_values = leaf.pauli_expectations(
            h0_basis,
            length,
            ops,
            backend=backend,
        )
        typicality.extend(
            curve_rows(
                leaf.to_numpy(benchmark_values),
                length=length,
                beta=beta,
                group="integrable",
                observable=label,
                family="eth_integrable",
                boundary=boundary,
            )
        )
        values = leaf.pauli_expectations(
            ensemble.representatives,
            length,
            ops,
            backend=backend,
        )
        typicality.extend(
            curve_rows(
                leaf.to_numpy(values),
                length=length,
                beta=beta,
                group="integrable",
                observable=label,
                family="leaf",
                boundary=boundary,
            )
        )
    leaf.synchronize(backend)
    payload = {
        "group": "integrable",
        "length": length,
        "dimension": 1 << length,
        "boundary": boundary,
        "backend": backend,
        "h0_z": h0_z,
        "beta": beta,
        "shell_width": max(1, int(round(np.sqrt(1 << length)))),
        "timing": {"total_seconds": time.perf_counter() - started},
        "invariants": invariants,
        "note": "Thermal state of nonintegrable H; foliation induced by integrable H0, matching Fig. S4.",
    }
    return typicality, [], payload


def output_paths(output_root: Path, group: str, length: int) -> dict[str, Path]:
    stem = f"{group}_L{length}"
    return {
        "typicality": output_root / "data" / "campaign_shards" / f"{stem}_typicality.csv",
        "compression": output_root / "data" / "campaign_shards" / f"{stem}_compression.csv",
        "check": output_root / "checks" / "campaign_shards" / f"{stem}.json",
    }


def run_point(
    *,
    output_root: Path,
    length: int,
    group: str,
    boundary: str,
    backend: str,
    force: bool,
) -> dict[str, Any]:
    paths = output_paths(output_root, group, length)
    if paths["check"].exists() and not force:
        existing = json.loads(paths["check"].read_text(encoding="utf-8"))
        if existing.get("status") == "passed":
            return {"status": "skipped_completed", "group": group, "length": length}

    if group == "integrable":
        typicality, compression, detail = run_integrable_group(
            length=length,
            h0_z=GROUP_H0_Z[group],
            boundary=boundary,
            backend=backend,
        )
    else:
        typicality, compression, detail = run_standard_group(
            length=length,
            group=group,
            h0_z=GROUP_H0_Z[group],
            boundary=boundary,
            backend=backend,
        )

    write_csv(paths["typicality"], typicality)
    if compression:
        write_csv(paths["compression"], compression)
    invariant_payloads: list[dict[str, float]] = []
    if "summaries" in detail:
        invariant_payloads.extend(item["invariants"] for item in detail["summaries"])
    elif "invariants" in detail:
        invariant_payloads.append(detail["invariants"])
    maximum_error = max(
        max(
            item["population_sum_error"],
            item["maximum_norm_error"],
            item["reconstruction_fro_error"],
            item["representative_energy_max_error"],
            item["qfi_variance_absolute_error"],
        )
        for item in invariant_payloads
    )
    passed = maximum_error < 1e-7
    payload = {
        "schema_version": 1,
        "paper_id": "2602.12212",
        "status": "passed" if passed else "failed",
        "artifact_state": (
            "final_reproduction_candidate"
            if length in {6, 8, 9, 10, 11, 12}
            else "exploratory"
        ),
        "parameter_match": "paper_exact_reconstructed_metadata",
        "generated_data_provenance": "independent_numerics",
        "maximum_formula_invariant_error": maximum_error,
        "paths": {
            key: str(path.relative_to(WORKSPACE))
            for key, path in paths.items()
            if key != "check" and path.exists()
        },
        "detail": detail,
    }
    write_json(paths["check"], payload)
    if not passed:
        raise RuntimeError(f"formula invariant failed for {group} L={length}: {maximum_error}")
    return {"status": "passed", "group": group, "length": length, "check": str(paths["check"])}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("numpy", "cupy"), default="numpy")
    parser.add_argument("--lengths", type=int, nargs="+", default=[6])
    parser.add_argument("--groups", choices=GROUPS, nargs="+", default=list(GROUPS))
    parser.add_argument("--boundary", choices=("open", "periodic"), default="periodic")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=WORKSPACE / "outputs",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--require-a100", action="store_true")
    parser.add_argument("--require-idle-gpu", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    accelerator = enforce_accelerator_contract(
        args.backend,
        require_a100=args.require_a100,
        require_idle_gpu=args.require_idle_gpu,
    )
    started = time.perf_counter()
    results = []
    for length in args.lengths:
        for group in args.groups:
            result = run_point(
                output_root=args.output_root,
                length=length,
                group=group,
                boundary=args.boundary,
                backend=args.backend,
                force=args.force,
            )
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    shard_checks = []
    coverage: dict[str, set[int]] = {group: set() for group in GROUPS}
    for check_path in sorted(
        (args.output_root / "checks" / "campaign_shards").glob("*_L*.json")
    ):
        payload = json.loads(check_path.read_text(encoding="utf-8"))
        detail = payload.get("detail", {})
        group = str(detail.get("group", "unknown"))
        length = int(detail.get("length", 0))
        shard_checks.append(
            {
                "group": group,
                "length": length,
                "status": payload.get("status", "unknown"),
                "backend": detail.get("backend", "unknown"),
                "maximum_formula_invariant_error": payload.get(
                    "maximum_formula_invariant_error"
                ),
                "check": str(check_path.relative_to(WORKSPACE)),
            }
        )
        if payload.get("status") == "passed" and group in coverage:
            coverage[group].add(length)
    manifest = {
        "schema_version": 1,
        "paper_id": "2602.12212",
        "status": (
            "passed"
            if shard_checks
            and all(item["status"] == "passed" for item in shard_checks)
            else "failed"
        ),
        "coverage": {
            group: sorted(lengths)
            for group, lengths in coverage.items()
        },
        "completed_shards": shard_checks,
        "last_run": {
            "backend": args.backend,
            "platform": f"{platform.system()}-{platform.release()}-{platform.machine()}",
            "accelerator": accelerator,
            "boundary": args.boundary,
            "lengths": args.lengths,
            "groups": args.groups,
            "results": results,
            "runtime_seconds": time.perf_counter() - started,
        },
    }
    write_json(args.output_root / "checks" / "manybody_campaign_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
