#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dtc_feature_sim import endpoint_mutual_information, normalize_compute_backend  # noqa: E402


PAPER_ID = "1608.02589"
TARGET_ID = "T003"
TARGET_LABEL = "Fig. 3b-d endpoint mutual information scaling collapse"

PANEL_PARAMETERS = [
    {"panel": "Fig. 3b", "J_z": 0.05, "epsilon_c": 0.043, "beta": 0.42, "nu": 1.21},
    {"panel": "Fig. 3c", "J_z": 0.10, "epsilon_c": 0.081, "beta": 0.44, "nu": 1.24},
    {"panel": "Fig. 3d", "J_z": 0.15, "epsilon_c": 0.130, "beta": 0.47, "nu": 1.35},
]

PROFILE_SAMPLE_COUNTS = {
    "smoke": {4: 1},
    "pilot": {8: 200, 10: 200},
    "medium": {8: 1000, 10: 1000, 12: 300},
    "final": {8: 10000, 10: 10000, 12: 3000, 14: 1000},
}

FINAL_EPSILON_GRIDS = {
    (0.05, 8): [0.0000, 0.0251, 0.0430, 0.0609, 0.0878, 0.1147, 0.1506, 0.1865, 0.1930, 0.2223, 0.2672, 0.3120, 0.4017, 0.4500],
    (0.05, 10): [0.0000, 0.0057, 0.0281, 0.0430, 0.0579, 0.0803, 0.1027, 0.1325, 0.1623, 0.1921, 0.1930, 0.2294, 0.2667, 0.3413, 0.4500],
    (0.05, 12): [0.0000, 0.0109, 0.0302, 0.0430, 0.0558, 0.0751, 0.0943, 0.1200, 0.1456, 0.1713, 0.1930, 0.2033, 0.2354, 0.2995, 0.4500],
    (0.05, 14): [0.0000, 0.0148, 0.0317, 0.0430, 0.0543, 0.0712, 0.0882, 0.1108, 0.1333, 0.1559, 0.1842, 0.1930, 0.2124, 0.2688, 0.4500],
    (0.10, 8): [0.0000, 0.0062, 0.0343, 0.0623, 0.0810, 0.0997, 0.1277, 0.1558, 0.1932, 0.2306, 0.2310, 0.2679, 0.3147, 0.3614, 0.4500],
    (0.10, 10): [0.0000, 0.0185, 0.0420, 0.0654, 0.0810, 0.0966, 0.1200, 0.1435, 0.1747, 0.2059, 0.2310, 0.2372, 0.2762, 0.3152, 0.3933, 0.4500],
    (0.10, 12): [0.0000, 0.0001, 0.0271, 0.0473, 0.0675, 0.0810, 0.0945, 0.1147, 0.1349, 0.1619, 0.1888, 0.2158, 0.2310, 0.2495, 0.2832, 0.3506, 0.4500],
    (0.10, 14): [0.0000, 0.0096, 0.0334, 0.0512, 0.0691, 0.0810, 0.0929, 0.1108, 0.1286, 0.1524, 0.1762, 0.2000, 0.2298, 0.2310, 0.2596, 0.3191, 0.4500],
    (0.15, 8): [0.0000, 0.0014, 0.0443, 0.0764, 0.1086, 0.1300, 0.1514, 0.1836, 0.2157, 0.2586, 0.2800, 0.3014, 0.3443, 0.3979, 0.4500],
    (0.15, 10): [0.0000, 0.0210, 0.0573, 0.0846, 0.1118, 0.1300, 0.1482, 0.1754, 0.2027, 0.2390, 0.2753, 0.2800, 0.3117, 0.3571, 0.4025, 0.4500],
    (0.15, 12): [0.0000, 0.0030, 0.0348, 0.0665, 0.0903, 0.1141, 0.1300, 0.1459, 0.1697, 0.1935, 0.2252, 0.2570, 0.2800, 0.2887, 0.3284, 0.3681, 0.4474, 0.4500],
    (0.15, 14): [0.0000, 0.0167, 0.0450, 0.0734, 0.0946, 0.1158, 0.1300, 0.1442, 0.1654, 0.1866, 0.2150, 0.2433, 0.2716, 0.2800, 0.3070, 0.3424, 0.4132, 0.4500],
}


def build_jobs(
    profile: str,
    sample_chunk_size: int | None = None,
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
) -> list[dict[str, Any]]:
    if profile not in PROFILE_SAMPLE_COUNTS:
        raise ValueError(f"unknown profile: {profile}")
    if sample_chunk_size is not None and sample_chunk_size <= 0:
        raise ValueError("sample_chunk_size must be positive")
    if sample_chunk_sizes_by_l:
        for system_size, chunk_size in sample_chunk_sizes_by_l.items():
            if int(system_size) <= 0 or int(chunk_size) <= 0:
                raise ValueError("sample_chunk_sizes_by_l must use positive sizes and chunks")

    rows: list[dict[str, Any]] = []
    sample_counts = PROFILE_SAMPLE_COUNTS[profile]
    for panel in PANEL_PARAMETERS:
        j_z = float(panel["J_z"])
        for system_size, sample_count in sample_counts.items():
            chunk_size = _chunk_size_for(system_size, sample_chunk_size, sample_chunk_sizes_by_l)
            epsilons = _epsilon_grid(profile, j_z, system_size, float(panel["epsilon_c"]))
            for epsilon in epsilons:
                for sample_start, chunk_count in _sample_chunks(int(sample_count), chunk_size):
                    job_index = len(rows)
                    rows.append(
                        {
                            "job_index": job_index,
                            "job_id": _job_id(profile, str(panel["panel"]), system_size, float(epsilon), sample_start),
                            "paper_id": PAPER_ID,
                            "target_id": TARGET_ID,
                            "target_label": TARGET_LABEL,
                            "profile": profile,
                            "panel": panel["panel"],
                            "L": system_size,
                            "J_z": j_z,
                            "epsilon": float(epsilon),
                            "epsilon_c": float(panel["epsilon_c"]),
                            "beta": float(panel["beta"]),
                            "nu": float(panel["nu"]),
                            "sample_start": sample_start,
                            "sample_count": chunk_count,
                            "seed": _seed_for(j_z, system_size, float(epsilon), profile) + sample_start,
                        }
                    )
    return rows


def run_campaign(
    workspace: Path = WORKSPACE,
    *,
    profile: str,
    job_index: int | None = None,
    max_jobs: int | None = None,
    sample_chunk_size: int | None = None,
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    compute_backend: str | None = None,
) -> dict[str, Any]:
    backend = _compute_backend(compute_backend)
    jobs = build_jobs(profile, sample_chunk_size=sample_chunk_size, sample_chunk_sizes_by_l=sample_chunk_sizes_by_l)
    selected = _select_jobs(jobs, job_index=job_index, max_jobs=max_jobs)
    rows = [_run_job(job, compute_backend=backend) for job in selected]

    if job_index is not None:
        return _write_shard_result(workspace, profile=profile, jobs_total=len(jobs), row=rows[0])

    data_path = workspace / "outputs" / "data" / "fig3_large_ed_campaign.csv"
    result_path = workspace / "outputs" / "checks" / "paper_exact_campaign_result.json"
    paper_rows = _aggregate_chunk_rows(rows)
    _write_csv(data_path, paper_rows)

    result = {
        "schema_version": 1,
        "status": _status_for(profile, len(selected), len(jobs)),
        "paper_id": PAPER_ID,
        "target_id": TARGET_ID,
        "target_label": TARGET_LABEL,
        "profile": profile,
        "sample_chunk_size": sample_chunk_size,
        "sample_chunk_sizes_by_l": sample_chunk_sizes_by_l or {},
        "compute_backend": backend,
        "jobs_total": len(jobs),
        "jobs_completed": len(selected),
        "paper_points_completed": len(paper_rows),
        "outputs": {
            "data_csv": "outputs/data/fig3_large_ed_campaign.csv",
            "result_json": "outputs/checks/paper_exact_campaign_result.json",
        },
        "paper_parameter_scope": _scope_for(profile),
        "excluded_scope": [
            "The dense Floquet eigensolver path does not schedule the optional L=16 and L=18 checks; those need a separate memory-aware strategy.",
        ],
    }
    _write_json(result_path, result)
    return result


def merge_shards(
    workspace: Path = WORKSPACE,
    *,
    profile: str,
    sample_chunk_size: int | None = None,
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
) -> dict[str, Any]:
    jobs = build_jobs(profile, sample_chunk_size=sample_chunk_size, sample_chunk_sizes_by_l=sample_chunk_sizes_by_l)
    shard_dir = workspace / "outputs" / "data" / "fig3_large_ed_campaign_shards"
    rows = _read_shard_rows(shard_dir)
    completed = {int(row["job_index"]) for row in rows}
    expected = set(range(len(jobs)))
    missing = sorted(expected - completed)
    paper_rows = _aggregate_chunk_rows(rows)

    data_path = workspace / "outputs" / "data" / "fig3_large_ed_campaign.csv"
    result_path = workspace / "outputs" / "checks" / "paper_exact_campaign_result.json"
    _write_csv(data_path, paper_rows)

    result = {
        "schema_version": 1,
        "status": "completed_profile" if not missing else "partial_profile",
        "paper_id": PAPER_ID,
        "target_id": TARGET_ID,
        "target_label": TARGET_LABEL,
        "profile": profile,
        "sample_chunk_size": sample_chunk_size,
        "sample_chunk_sizes_by_l": sample_chunk_sizes_by_l or {},
        "jobs_total": len(jobs),
        "jobs_completed": len(completed),
        "paper_points_completed": len(paper_rows),
        "missing_job_indices": missing,
        "outputs": {
            "data_csv": "outputs/data/fig3_large_ed_campaign.csv",
            "result_json": "outputs/checks/paper_exact_campaign_result.json",
            "data_shards": "outputs/data/fig3_large_ed_campaign_shards/",
            "check_shards": "outputs/checks/fig3_large_ed_campaign_shards/",
        },
        "paper_parameter_scope": _scope_for(profile),
        "excluded_scope": [
            "The dense Floquet eigensolver path does not schedule the optional L=16 and L=18 checks; those need a separate memory-aware strategy.",
        ],
    }
    _write_json(result_path, result)
    return result


def run_shards(
    workspace: Path = WORKSPACE,
    *,
    profile: str,
    workers: int = 1,
    start_index: int = 0,
    max_jobs: int | None = None,
    sample_chunk_size: int | None = None,
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    skip_existing: bool = False,
    compute_backend: str | None = None,
) -> dict[str, Any]:
    backend = _compute_backend(compute_backend)
    jobs = build_jobs(profile, sample_chunk_size=sample_chunk_size, sample_chunk_sizes_by_l=sample_chunk_sizes_by_l)
    selected = _select_job_range(jobs, start_index=start_index, max_jobs=max_jobs)
    skipped = [job for job in selected if skip_existing and _shard_exists(workspace, int(job["job_index"]))]
    skipped_indices = [int(job["job_index"]) for job in skipped]
    skipped_index_set = set(skipped_indices)
    to_run = [job for job in selected if int(job["job_index"]) not in skipped_index_set]
    workers = max(1, int(workers))

    rows: list[dict[str, Any]] = []
    if workers == 1:
        for job in to_run:
            row = _run_job(job, compute_backend=backend)
            _write_shard_result(workspace, profile=profile, jobs_total=len(jobs), row=row)
            rows.append(row)
    elif to_run:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_run_job, job, compute_backend=backend) for job in to_run]
            for future in as_completed(futures):
                row = future.result()
                _write_shard_result(workspace, profile=profile, jobs_total=len(jobs), row=row)
                rows.append(row)

    rows = sorted(rows, key=lambda row: int(row["job_index"]))

    return {
        "schema_version": 1,
        "status": "shard_batch_completed",
        "paper_id": PAPER_ID,
        "target_id": TARGET_ID,
        "target_label": TARGET_LABEL,
        "profile": profile,
        "sample_chunk_size": sample_chunk_size,
        "sample_chunk_sizes_by_l": sample_chunk_sizes_by_l or {},
        "compute_backend": backend,
        "jobs_total": len(jobs),
        "jobs_completed": len(rows) + len(skipped_indices),
        "jobs_ran": len(rows),
        "jobs_skipped": len(skipped_indices),
        "job_indices": [int(row["job_index"]) for row in rows],
        "skipped_job_indices": skipped_indices,
        "selected_job_indices": [int(job["job_index"]) for job in selected],
        "workers": workers,
        "outputs": {
            "data_shards": "outputs/data/fig3_large_ed_campaign_shards/",
            "check_shards": "outputs/checks/fig3_large_ed_campaign_shards/",
        },
    }


def write_manifest(
    workspace: Path = WORKSPACE,
    *,
    profile: str,
    sample_chunk_size: int | None = None,
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    compute_backend: str | None = None,
) -> dict[str, Any]:
    backend = _compute_backend(compute_backend)
    jobs = build_jobs(profile, sample_chunk_size=sample_chunk_size, sample_chunk_sizes_by_l=sample_chunk_sizes_by_l)
    manifest = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "target_id": TARGET_ID,
        "profile": profile,
        "sample_chunk_size": sample_chunk_size,
        "sample_chunk_sizes_by_l": sample_chunk_sizes_by_l or {},
        "compute_backend": backend,
        "jobs_total": len(jobs),
        "jobs": jobs,
    }
    _write_json(workspace / "outputs" / "checks" / "fig3_large_ed_campaign_manifest.json", manifest)
    return manifest


def _epsilon_grid(profile: str, j_z: float, system_size: int, epsilon_c: float) -> list[float]:
    if profile == "smoke":
        return [0.0]
    if profile == "pilot":
        return [0.0, epsilon_c, 0.45]
    if profile == "medium":
        full = FINAL_EPSILON_GRIDS[(j_z, system_size)]
        return full[::3] + ([] if full[-1] in full[::3] else [full[-1]])
    return FINAL_EPSILON_GRIDS[(j_z, system_size)]


def _sample_chunks(sample_count: int, sample_chunk_size: int | None) -> list[tuple[int, int]]:
    if sample_chunk_size is None or sample_chunk_size >= sample_count:
        return [(0, sample_count)]
    chunks: list[tuple[int, int]] = []
    for sample_start in range(0, sample_count, sample_chunk_size):
        chunks.append((sample_start, min(sample_chunk_size, sample_count - sample_start)))
    return chunks


def _chunk_size_for(
    system_size: int,
    sample_chunk_size: int | None,
    sample_chunk_sizes_by_l: dict[int, int] | None,
) -> int | None:
    if sample_chunk_sizes_by_l and system_size in sample_chunk_sizes_by_l:
        return int(sample_chunk_sizes_by_l[system_size])
    return sample_chunk_size


def _job_id(profile: str, panel: str, system_size: int, epsilon: float, sample_start: int) -> str:
    panel_slug = _panel_slug(panel)
    return f"{TARGET_ID}-{profile}-{panel_slug}-L{system_size}-eps{epsilon:.4f}-s{sample_start}"


def _point_id(profile: str, panel: str, system_size: int, epsilon: float) -> str:
    panel_slug = _panel_slug(panel)
    return f"{TARGET_ID}-{profile}-{panel_slug}-L{system_size}-eps{epsilon:.4f}"


def _panel_slug(panel: str) -> str:
    return panel.replace(" ", "").replace(".", "").lower()


def _run_job(job: dict[str, Any], *, compute_backend: str | None = None) -> dict[str, Any]:
    backend = _compute_backend(compute_backend)
    mi = endpoint_mutual_information(
        int(job["L"]),
        float(job["J_z"]),
        float(job["epsilon"]),
        samples=int(job["sample_count"]),
        seed=int(job["seed"]),
        compute_backend=backend,
    )
    scaling_x = (float(job["epsilon"]) - float(job["epsilon_c"])) * (int(job["L"]) ** (1.0 / float(job["nu"])))
    scaling_y = (int(job["L"]) ** float(job["beta"])) * mi
    row = dict(job)
    row["endpoint_mutual_information"] = mi
    row["scaling_x"] = scaling_x
    row["scaling_y"] = scaling_y
    row["compute_backend"] = backend
    return row


def _write_shard_result(workspace: Path, *, profile: str, jobs_total: int, row: dict[str, Any]) -> dict[str, Any]:
    job_index = int(row["job_index"])
    data_path, result_path = _shard_paths(workspace, job_index)
    _write_csv(data_path, [row])
    result = {
        "schema_version": 1,
        "status": "shard_completed",
        "paper_id": PAPER_ID,
        "target_id": TARGET_ID,
        "target_label": TARGET_LABEL,
        "profile": profile,
        "job_index": job_index,
        "job_id": str(row["job_id"]),
        "jobs_total": jobs_total,
        "jobs_completed": 1,
        "compute_backend": str(row.get("compute_backend", "numpy")),
        "outputs": {
            "data_csv": f"outputs/data/fig3_large_ed_campaign_shards/job_{job_index:06d}.csv",
            "result_json": f"outputs/checks/fig3_large_ed_campaign_shards/job_{job_index:06d}.json",
        },
    }
    _write_json(result_path, result)
    return result


def _shard_exists(workspace: Path, job_index: int) -> bool:
    data_path, result_path = _shard_paths(workspace, job_index)
    return data_path.is_file() and result_path.is_file()


def _shard_paths(workspace: Path, job_index: int) -> tuple[Path, Path]:
    return (
        workspace / "outputs" / "data" / "fig3_large_ed_campaign_shards" / f"job_{job_index:06d}.csv",
        workspace / "outputs" / "checks" / "fig3_large_ed_campaign_shards" / f"job_{job_index:06d}.json",
    )


def _aggregate_chunk_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(_paper_point_key(row), []).append(row)

    paper_rows: list[dict[str, Any]] = []
    for point_index, chunk_rows in enumerate(
        sorted(groups.values(), key=lambda group: min(int(row["job_index"]) for row in group))
    ):
        chunk_rows = sorted(chunk_rows, key=lambda row: int(row["job_index"]))
        first = chunk_rows[0]
        sample_total = sum(int(row["sample_count"]) for row in chunk_rows)
        if sample_total <= 0:
            raise ValueError("sample_count must be positive")
        endpoint_mi = (
            sum(float(row["endpoint_mutual_information"]) * int(row["sample_count"]) for row in chunk_rows)
            / sample_total
        )
        system_size = int(first["L"])
        beta = float(first["beta"])
        scaling_x = (float(first["epsilon"]) - float(first["epsilon_c"])) * (system_size ** (1.0 / float(first["nu"])))
        scaling_y = (system_size**beta) * endpoint_mi
        source_job_indices = [int(row["job_index"]) for row in chunk_rows]
        backends = sorted({str(row.get("compute_backend", "unknown")) for row in chunk_rows})
        paper_rows.append(
            {
                "paper_point_index": point_index,
                "job_index": source_job_indices[0],
                "job_id": _point_id(str(first["profile"]), str(first["panel"]), system_size, float(first["epsilon"])),
                "paper_id": str(first["paper_id"]),
                "target_id": str(first["target_id"]),
                "target_label": str(first["target_label"]),
                "profile": str(first["profile"]),
                "panel": str(first["panel"]),
                "L": system_size,
                "J_z": float(first["J_z"]),
                "epsilon": float(first["epsilon"]),
                "epsilon_c": float(first["epsilon_c"]),
                "beta": beta,
                "nu": float(first["nu"]),
                "sample_start": 0,
                "sample_count": sample_total,
                "seed": int(first["seed"]),
                "endpoint_mutual_information": endpoint_mi,
                "scaling_x": scaling_x,
                "scaling_y": scaling_y,
                "chunk_job_count": len(chunk_rows),
                "source_job_indices": ";".join(str(index) for index in source_job_indices),
                "compute_backend": backends[0] if len(backends) == 1 else ";".join(backends),
            }
        )
    return paper_rows


def _paper_point_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["paper_id"]),
        str(row["target_id"]),
        str(row["profile"]),
        str(row["panel"]),
        int(row["L"]),
        round(float(row["J_z"]), 12),
        round(float(row["epsilon"]), 12),
        round(float(row["epsilon_c"]), 12),
        round(float(row["beta"]), 12),
        round(float(row["nu"]), 12),
    )


def _read_shard_rows(shard_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(shard_dir.glob("job_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"no shard rows found in {shard_dir}")
    return sorted(rows, key=lambda row: int(row["job_index"]))


def _select_jobs(
    jobs: list[dict[str, Any]],
    *,
    job_index: int | None,
    max_jobs: int | None,
) -> list[dict[str, Any]]:
    if job_index is not None:
        if job_index < 0 or job_index >= len(jobs):
            raise ValueError(f"job_index out of range: {job_index}")
        return [jobs[job_index]]
    if max_jobs is not None:
        return jobs[:max_jobs]
    return jobs


def _select_job_range(jobs: list[dict[str, Any]], *, start_index: int, max_jobs: int | None) -> list[dict[str, Any]]:
    if start_index < 0 or start_index >= len(jobs):
        raise ValueError(f"start_index out of range: {start_index}")
    stop = len(jobs) if max_jobs is None else min(len(jobs), start_index + max_jobs)
    return jobs[start_index:stop]


def _status_for(profile: str, jobs_completed: int, jobs_total: int) -> str:
    if profile == "smoke":
        return "partial_smoke"
    if jobs_completed < jobs_total:
        return "partial_profile"
    return "completed_profile"


def _scope_for(profile: str) -> str:
    if profile == "smoke":
        return "contract smoke only; not a paper-scale reproduction claim"
    if profile == "final":
        return "Fig. 3b-d main scaling sets with L=8,10,12,14 and paper-derived epsilon grids"
    return f"{profile} staged run using reduced sample counts before the final paper-scale campaign"


def _seed_for(j_z: float, system_size: int, epsilon: float, profile: str) -> int:
    profile_offset = {"smoke": 100000, "pilot": 200000, "medium": 300000, "final": 400000}[profile]
    return profile_offset + int(round(j_z * 10000)) * 1000 + system_size * 100 + int(round(epsilon * 10000))


def parse_chunk_sizes_by_l(value: str | None) -> dict[int, int] | None:
    if not value:
        return None
    chunks: dict[int, int] = {}
    for item in value.split(","):
        if not item:
            continue
        system_size, chunk_size = item.split(":", 1)
        chunks[int(system_size)] = int(chunk_size)
    return chunks


def _compute_backend(value: str | None = None) -> str:
    return normalize_compute_backend(value or os.environ.get("DTC_COMPUTE_BACKEND", "numpy"))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("no campaign rows to write")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or manifest the DTC Fig. 3 large-ED campaign.")
    parser.add_argument("--profile", choices=sorted(PROFILE_SAMPLE_COUNTS), default="smoke")
    parser.add_argument("--job-index", type=int, default=None)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--sample-chunk-size", type=int, default=None)
    parser.add_argument("--sample-chunk-sizes-by-l", default=None, help="Comma-separated chunks such as 8:500,10:500,12:100,14:1")
    parser.add_argument("--compute-backend", default=None, help="Compute backend: numpy or cupy. Defaults to DTC_COMPUTE_BACKEND or numpy.")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--run-shards", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--merge-shards", action="store_true")
    args = parser.parse_args()
    sample_chunk_sizes_by_l = parse_chunk_sizes_by_l(args.sample_chunk_sizes_by_l)

    if args.merge_shards:
        payload = merge_shards(
            WORKSPACE,
            profile=args.profile,
            sample_chunk_size=args.sample_chunk_size,
            sample_chunk_sizes_by_l=sample_chunk_sizes_by_l,
        )
    elif args.run_shards:
        payload = run_shards(
            WORKSPACE,
            profile=args.profile,
            workers=args.workers,
            start_index=args.start_index,
            max_jobs=args.max_jobs,
            sample_chunk_size=args.sample_chunk_size,
            sample_chunk_sizes_by_l=sample_chunk_sizes_by_l,
            skip_existing=args.skip_existing,
            compute_backend=args.compute_backend,
        )
    elif args.write_manifest:
        payload = write_manifest(
            WORKSPACE,
            profile=args.profile,
            sample_chunk_size=args.sample_chunk_size,
            sample_chunk_sizes_by_l=sample_chunk_sizes_by_l,
            compute_backend=args.compute_backend,
        )
    else:
        payload = run_campaign(
            WORKSPACE,
            profile=args.profile,
            job_index=args.job_index,
            max_jobs=args.max_jobs,
            sample_chunk_size=args.sample_chunk_size,
            sample_chunk_sizes_by_l=sample_chunk_sizes_by_l,
            compute_backend=args.compute_backend,
        )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
