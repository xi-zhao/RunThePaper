"""Paper-protocol ensemble run and deterministic rendering."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import scipy

from rqaoa import (
    edge_pairs,
    exact_ising_max,
    optimize_qaoa1,
    random_signed_regular_instance,
    run_rqaoa1,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def _matrix_fingerprint(matrix: np.ndarray) -> str:
    canonical = np.ascontiguousarray(matrix.astype("<f8", copy=False))
    return hashlib.sha256(canonical.tobytes()).hexdigest()


def _render_panel(records: list[dict[str, Any]], output: Path) -> None:
    instances = np.array([int(row["instance"]) for row in records])
    qaoa = np.array([float(row["qaoa_ratio"]) for row in records])
    rqaoa = np.array([float(row["rqaoa_ratio"]) for row in records])

    # The dimensions, palette, axis limits, tick cadence and legend placement
    # implement a RenderContract only.  Bar heights come exclusively from the
    # independently generated records above.
    figure, axis = plt.subplots(figsize=(5.102, 4.142), dpi=250)
    width = 0.24
    axis.bar(
        instances - width / 2,
        qaoa,
        width,
        color="#0072BD",
        edgecolor="black",
        linewidth=0.55,
        label="QAOA",
    )
    axis.bar(
        instances + width / 2,
        rqaoa,
        width,
        color="#D95319",
        edgecolor="black",
        linewidth=0.55,
        label="RQAOA",
    )
    axis.set_xlim(0.0, 17.0)
    axis.set_ylim(0.0, 1.0)
    axis.set_xticks(np.arange(2, 17, 2))
    axis.set_yticks(np.linspace(0.0, 1.0, 6))
    axis.set_yticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1"])
    axis.set_xlabel("problem instance", fontsize=14)
    axis.set_ylabel("approximation ratio", fontsize=14)
    axis.tick_params(direction="in", top=True, right=True, labelsize=12, length=4)
    legend = axis.legend(
        loc="lower right",
        bbox_to_anchor=(1.0, 0.085),
        frameon=True,
        fancybox=False,
        framealpha=1.0,
        edgecolor="black",
        fontsize=12,
        borderpad=0.25,
        handlelength=2.2,
        handletextpad=0.3,
    )
    legend.get_frame().set_linewidth(0.5)
    for spine in axis.spines.values():
        spine.set_linewidth(0.55)
    figure.subplots_adjust(left=0.118, right=0.968, bottom=0.135, top=0.965)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=250, facecolor="white")
    plt.close(figure)


def _run_size(
    specification: dict[str, Any],
    parameters: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], np.ndarray]:
    n = int(specification["n"])
    cutoff = int(specification["cutoff"])
    count = int(parameters["instances_per_size"])
    degree = int(parameters["degree"])
    master_seed = int(parameters["master_seed"])
    generator = np.random.default_rng(master_seed + 1009 * n)
    matrices = np.empty((count, n, n), dtype=np.float64)
    records: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for instance in range(1, count + 1):
        graph_seed = int(generator.integers(0, 2**31 - 1))
        coupling_seed = int(generator.integers(0, 2**31 - 1))
        couplings = random_signed_regular_instance(
            n,
            degree=degree,
            graph_seed=graph_seed,
            coupling_seed=coupling_seed,
        )
        matrices[instance - 1] = couplings
        degrees = np.count_nonzero(couplings, axis=1)
        if not np.all(degrees == degree):
            raise RuntimeError("generated graph violates the declared regular degree")
        if len(edge_pairs(couplings)) != n * degree // 2:
            raise RuntimeError("generated graph has the wrong edge count")

        started = perf_counter()
        exact = exact_ising_max(
            couplings,
            time_limit_seconds=float(parameters["exact_time_limit_seconds"]),
        )
        qaoa = optimize_qaoa1(
            couplings,
            gamma_grid_points=int(parameters["gamma_grid_points"]),
            local_candidates=int(parameters["gamma_local_candidates"]),
        )
        rqaoa = run_rqaoa1(
            couplings,
            cutoff=cutoff,
            gamma_grid_points=int(parameters["gamma_grid_points"]),
            local_candidates=int(parameters["gamma_local_candidates"]),
            exact_time_limit_seconds=float(parameters["exact_time_limit_seconds"]),
        )
        wall = perf_counter() - started
        if rqaoa.energy > exact.energy + 1e-8:
            raise RuntimeError("RQAOA exceeded the independently proved exact optimum")
        record = {
            "n": n,
            "cutoff": cutoff,
            "instance": instance,
            "graph_seed": graph_seed,
            "coupling_seed": coupling_seed,
            "coupling_sha256": _matrix_fingerprint(couplings),
            "edge_count": len(edge_pairs(couplings)),
            "exact_energy": exact.energy,
            "exact_mip_gap": exact.mip_gap,
            "qaoa_expected_energy": qaoa.expected_energy,
            "qaoa_beta": qaoa.beta,
            "qaoa_gamma": qaoa.gamma,
            "qaoa_ratio": qaoa.expected_energy / exact.energy,
            "rqaoa_energy": rqaoa.energy,
            "rqaoa_ratio": rqaoa.energy / exact.energy,
            "exact_runtime_seconds": exact.runtime_seconds,
            "rqaoa_runtime_seconds": rqaoa.runtime_seconds,
            "instance_runtime_seconds": wall,
        }
        records.append(record)
        traces.append(
            {
                "n": n,
                "instance": instance,
                "coupling_sha256": record["coupling_sha256"],
                "eliminations": list(rqaoa.eliminations),
            }
        )
        print(
            f"n={n} instance={instance:02d}/{count} "
            f"QAOA={record['qaoa_ratio']:.6f} "
            f"RQAOA={record['rqaoa_ratio']:.6f} wall={wall:.2f}s",
            flush=True,
        )
    return records, traces, matrices


def _target_check(target_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    qaoa = np.array([float(row["qaoa_ratio"]) for row in records])
    rqaoa = np.array([float(row["rqaoa_ratio"]) for row in records])
    n = int(records[0]["n"])
    rqaoa_mean_floor = 0.95 if n == 32 else 0.92
    checks = {
        "all_exact_mip_gaps_zero": bool(
            all(float(row["exact_mip_gap"]) <= 1e-10 for row in records)
        ),
        "all_ratios_bounded": bool(
            np.all((-1.0 <= qaoa) & (qaoa <= 1.0 + 1e-10))
            and np.all((-1.0 <= rqaoa) & (rqaoa <= 1.0 + 1e-10))
        ),
        "rqaoa_outperforms_qaoa_each_instance": bool(np.all(rqaoa > qaoa)),
        "qaoa_mean_in_paper_feature_band": bool(0.35 <= np.mean(qaoa) <= 0.60),
        "rqaoa_mean_in_paper_feature_band": bool(
            np.mean(rqaoa) >= rqaoa_mean_floor
        ),
        "mean_advantage_at_least_0p40": bool(np.mean(rqaoa - qaoa) >= 0.40),
    }
    return {
        "target_id": target_id,
        "n": n,
        "instance_count": len(records),
        "qaoa_mean": float(np.mean(qaoa)),
        "qaoa_min": float(np.min(qaoa)),
        "qaoa_max": float(np.max(qaoa)),
        "rqaoa_mean": float(np.mean(rqaoa)),
        "rqaoa_min": float(np.min(rqaoa)),
        "rqaoa_max": float(np.max(rqaoa)),
        "mean_advantage": float(np.mean(rqaoa - qaoa)),
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def run_reproduction(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    workspace = config_path.parents[1]
    parameters = json.loads(config_path.read_text(encoding="utf-8"))["parameters"]
    outputs = workspace / "outputs"
    data_directory = outputs / "data"
    figure_directory = outputs / "figures"
    check_directory = outputs / "checks"
    for directory in (data_directory, figure_directory, check_directory):
        directory.mkdir(parents=True, exist_ok=True)

    run_started = perf_counter()
    target_checks: list[dict[str, Any]] = []
    data_paths: list[Path] = []
    all_records: dict[str, list[dict[str, Any]]] = {}

    for index, specification in enumerate(parameters["sizes"], start=1):
        target_id = f"T{index:03d}"
        n = int(specification["n"])
        records, traces, matrices = _run_size(specification, parameters)
        all_records[target_id] = records
        csv_path = data_directory / f"main_fig1_n{n}.csv"
        trace_path = data_directory / f"main_fig1_n{n}_traces.json"
        instances_path = data_directory / f"main_fig1_n{n}_instances.npz"
        _write_csv(csv_path, records)
        _write_json(trace_path, traces)
        np.savez_compressed(instances_path, couplings=matrices)
        data_paths.extend((csv_path, trace_path, instances_path))
        _render_panel(records, figure_directory / f"main_fig1_n{n}.png")
        target_checks.append(_target_check(target_id, records))

    checks_payload = {
        "schema_version": 1,
        "paper_id": "1910.08980",
        "targets": target_checks,
        "all_targets_passed": bool(all(item["passed"] for item in target_checks)),
        "interpretation": (
            "Feature checks compare independently sampled ensembles because the paper "
            "does not publish its 16 graph/coupling instances or random seeds."
        ),
    }
    _write_json(check_directory / "target_checks.json", checks_payload)

    manifest_entries = [
        {
            "path": str(path.relative_to(workspace)),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "provenance": "independent_numerics",
        }
        for path in data_paths
    ]
    _write_json(
        check_directory / "generated_data_manifest.json",
        {
            "schema_version": 1,
            "paper_id": "1910.08980",
            "source_pixels_used_as_numerical_input": False,
            "author_code_used": False,
            "author_arrays_used": False,
            "artifacts": manifest_entries,
        },
    )
    runtime_payload = {
        "wall_seconds": perf_counter() - run_started,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "networkx": nx.__version__,
        "matplotlib": matplotlib.__version__,
        "targets": {
            target_id: {
                "instance_count": len(records),
                "mean_instance_seconds": float(
                    np.mean([row["instance_runtime_seconds"] for row in records])
                ),
            }
            for target_id, records in all_records.items()
        },
    }
    _write_json(check_directory / "runtime.json", runtime_payload)
    return {
        "paper_id": "1910.08980",
        "targets": [item["target_id"] for item in target_checks],
        "all_targets_passed": checks_payload["all_targets_passed"],
        "wall_seconds": runtime_payload["wall_seconds"],
    }
