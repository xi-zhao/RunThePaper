#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


WORKSPACE = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import run_fig3_large_ed_campaign as campaign  # noqa: E402


DEFAULT_CHUNKS_BY_L = {8: 500, 10: 500, 12: 100, 14: 10}
DEFAULT_CANARY_JOBS = 2
DEFAULT_CAMPAIGN_BATCH_SIZE = 100
DEFAULT_GPU_FREE_MEMORY_MIB = 100
DEFAULT_IDLE_RESIDUAL_GPU_MEMORY_MIB = 1024
DEFAULT_GUARD_POLL_SECONDS = 60.0
PLATFORM_RESULT = "outputs/checks/fig3_large_ed_a100_platform_run.json"
THREAD_ENV_KEYS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "DTC_COMPUTE_BACKEND",
)


def run_platform_batch(
    workspace: Path = WORKSPACE,
    *,
    mode: str,
    profile: str = "final",
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    start_index: int = 0,
    max_jobs: int | None = None,
    workers: int = 1,
    skip_existing: bool = True,
    allow_full: bool = False,
    platform_probe: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if mode not in {"canary", "batch"}:
        raise ValueError(f"unsupported mode for batch runner: {mode}")
    if mode == "canary" and max_jobs is None:
        max_jobs = DEFAULT_CANARY_JOBS
    if mode == "batch" and max_jobs is None and not allow_full:
        raise ValueError("refusing unbounded batch without allow_full=True")

    chunks = sample_chunk_sizes_by_l or DEFAULT_CHUNKS_BY_L
    if platform_probe is None:
        platform_probe = platform_profile
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    platform_data = platform_probe()
    manifest_summary: dict[str, Any] | None = None
    try:
        manifest = campaign.write_manifest(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
        manifest_summary = {
            "jobs_total": manifest["jobs_total"],
            "sample_chunk_sizes_by_l": chunks,
            "manifest_json": "outputs/checks/fig3_large_ed_campaign_manifest.json",
        }
        batch = campaign.run_shards(
            workspace,
            profile=profile,
            workers=workers,
            start_index=start_index,
            max_jobs=max_jobs,
            sample_chunk_sizes_by_l=chunks,
            skip_existing=skip_existing,
        )
    except Exception as exc:
        _write_json(
            workspace / PLATFORM_RESULT,
            _failure_payload(
                mode=mode,
                started_at=started_at,
                profile=profile,
                platform_data=platform_data,
                manifest_summary=manifest_summary,
                error=exc,
            ),
        )
        raise
    payload = {
        "schema_version": 1,
        "status": "canary_completed" if mode == "canary" else "batch_completed",
        "mode": mode,
        "started_at": started_at,
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "paper_id": campaign.PAPER_ID,
        "target_id": campaign.TARGET_ID,
        "profile": profile,
        "platform": platform_data,
        "manifest": manifest_summary,
        "batch": batch,
        "outputs": {
            "platform_result_json": PLATFORM_RESULT,
            "data_shards": "outputs/data/fig3_large_ed_campaign_shards/",
            "check_shards": "outputs/checks/fig3_large_ed_campaign_shards/",
        },
    }
    _write_json(workspace / PLATFORM_RESULT, payload)
    return payload


def run_platform_guarded_batch(
    workspace: Path = WORKSPACE,
    *,
    profile: str = "final",
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    start_index: int = 0,
    max_jobs: int | None = None,
    workers: int = 1,
    skip_existing: bool = True,
    allow_full: bool = False,
    resume_missing: bool = False,
    guard_max_wait_seconds: float = 0.0,
    guard_poll_seconds: float = DEFAULT_GUARD_POLL_SECONDS,
    gpu_max_memory_mib: int = DEFAULT_GPU_FREE_MEMORY_MIB,
    gpu_probe: Callable[[], dict[str, Any]] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    platform_probe: Callable[[], dict[str, Any]] | None = None,
    heartbeat_writer: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    if guard_max_wait_seconds < 0:
        raise ValueError("guard_max_wait_seconds must be non-negative")
    if guard_poll_seconds <= 0:
        raise ValueError("guard_poll_seconds must be positive")

    chunks = sample_chunk_sizes_by_l or DEFAULT_CHUNKS_BY_L
    if platform_probe is None:
        platform_probe = platform_profile
    if gpu_probe is None:
        gpu_probe = lambda: gpu_guard_snapshot(max_memory_mib=gpu_max_memory_mib)

    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    platform_data = platform_probe()
    status_before = platform_campaign_status(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
    selected_start_index = int(status_before["next_start_index"]) if resume_missing else start_index
    if selected_start_index >= int(status_before["jobs_total"]):
        payload = _guarded_batch_payload(
            status="guarded_batch_no_missing_jobs",
            started_at=started_at,
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            profile=profile,
            platform_data=platform_data,
            status_before=status_before,
            selected_start_index=selected_start_index,
            max_jobs=max_jobs,
            workers=workers,
            resume_missing=resume_missing,
            guard={"status": "skipped", "reason": "no_missing_jobs"},
            batch=None,
            status_after=status_before,
        )
        _write_json(workspace / PLATFORM_RESULT, payload)
        return payload

    def write_waiting_heartbeat(waiting_guard: dict[str, Any]) -> None:
        heartbeat = _guarded_batch_payload(
            status="guarded_batch_waiting",
            started_at=started_at,
            finished_at=None,
            profile=profile,
            platform_data=platform_data,
            status_before=status_before,
            selected_start_index=selected_start_index,
            max_jobs=max_jobs,
            workers=workers,
            resume_missing=resume_missing,
            guard=waiting_guard,
            batch=None,
            status_after=status_before,
        )
        _write_heartbeat(workspace, heartbeat, heartbeat_writer)

    guard = wait_for_gpu_free(
        max_wait_seconds=guard_max_wait_seconds,
        poll_seconds=guard_poll_seconds,
        gpu_probe=gpu_probe,
        sleep_fn=sleep_fn,
        clock=clock,
        on_waiting=write_waiting_heartbeat,
    )
    if guard["status"] != "gpu_free":
        payload = _guarded_batch_payload(
            status="guarded_batch_wait_timeout",
            started_at=started_at,
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            profile=profile,
            platform_data=platform_data,
            status_before=status_before,
            selected_start_index=selected_start_index,
            max_jobs=max_jobs,
            workers=workers,
            resume_missing=resume_missing,
            guard=guard,
            batch=None,
            status_after=status_before,
        )
        _write_json(workspace / PLATFORM_RESULT, payload)
        return payload

    running_heartbeat = _guarded_batch_payload(
        status="guarded_batch_running",
        started_at=started_at,
        finished_at=None,
        profile=profile,
        platform_data=platform_data,
        status_before=status_before,
        selected_start_index=selected_start_index,
        max_jobs=max_jobs,
        workers=workers,
        resume_missing=resume_missing,
        guard=guard,
        batch=None,
        status_after=status_before,
    )
    _write_heartbeat(workspace, running_heartbeat, heartbeat_writer)
    batch = run_platform_batch(
        workspace,
        mode="batch",
        profile=profile,
        sample_chunk_sizes_by_l=chunks,
        start_index=selected_start_index,
        max_jobs=max_jobs,
        workers=workers,
        skip_existing=skip_existing,
        allow_full=allow_full,
        platform_probe=lambda: platform_data,
    )
    status_after = platform_campaign_status(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
    payload = _guarded_batch_payload(
        status="guarded_batch_completed",
        started_at=started_at,
        finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        profile=profile,
        platform_data=platform_data,
        status_before=status_before,
        selected_start_index=selected_start_index,
        max_jobs=max_jobs,
        workers=workers,
        resume_missing=resume_missing,
        guard=guard,
        batch=batch,
        status_after=status_after,
    )
    _write_json(workspace / PLATFORM_RESULT, payload)
    return payload


def run_platform_guarded_campaign(
    workspace: Path = WORKSPACE,
    *,
    profile: str = "final",
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    batch_size: int = 1,
    max_batches: int | None = None,
    max_jobs: int | None = None,
    workers: int = 1,
    skip_existing: bool = True,
    allow_full: bool = False,
    guard_max_wait_seconds: float = 0.0,
    guard_poll_seconds: float = DEFAULT_GUARD_POLL_SECONDS,
    gpu_max_memory_mib: int = DEFAULT_GPU_FREE_MEMORY_MIB,
    idle_residual_gpu_memory_mib: int = DEFAULT_IDLE_RESIDUAL_GPU_MEMORY_MIB,
    gpu_probe: Callable[[], dict[str, Any]] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    platform_probe: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if max_batches is not None and max_batches <= 0:
        raise ValueError("max_batches must be positive")
    if max_jobs is not None and max_jobs <= 0:
        raise ValueError("max_jobs must be positive")
    if idle_residual_gpu_memory_mib < gpu_max_memory_mib:
        raise ValueError("idle_residual_gpu_memory_mib must be at least gpu_max_memory_mib")
    if max_batches is None and max_jobs is None and not allow_full:
        raise ValueError("refusing unbounded guarded campaign without allow_full=True, max_jobs, or max_batches")

    chunks = sample_chunk_sizes_by_l or DEFAULT_CHUNKS_BY_L
    if platform_probe is None:
        platform_probe = platform_profile
    platform_data = platform_probe()
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    status_before = platform_campaign_status(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
    batches: list[dict[str, Any]] = []
    jobs_ran = 0
    stop_reason = ""

    while True:
        if max_batches is not None and len(batches) >= max_batches:
            stop_reason = "max_batches_reached"
            break
        if max_jobs is not None and jobs_ran >= max_jobs:
            stop_reason = "max_jobs_reached"
            break
        current_status = platform_campaign_status(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
        if int(current_status["missing_jobs"]) <= 0:
            stop_reason = "completed_profile"
            break
        jobs_this_batch = batch_size
        if max_jobs is not None:
            jobs_this_batch = min(jobs_this_batch, max_jobs - jobs_ran)

        allow_idle_residual_context = bool(batches)

        def campaign_gpu_probe() -> dict[str, Any]:
            probe = gpu_probe or (lambda: gpu_guard_snapshot(max_memory_mib=gpu_max_memory_mib))
            snapshot = probe()
            if allow_idle_residual_context:
                return _allow_idle_residual_gpu_context(
                    snapshot,
                    max_memory_mib=idle_residual_gpu_memory_mib,
                )
            return snapshot

        def write_campaign_heartbeat(active_batch: dict[str, Any]) -> None:
            active_status = str(active_batch.get("status", ""))
            campaign_status = (
                "guarded_campaign_waiting"
                if active_status == "guarded_batch_waiting"
                else "guarded_campaign_running"
            )
            _write_json(
                workspace / PLATFORM_RESULT,
                _guarded_campaign_payload(
                    status=campaign_status,
                    started_at=started_at,
                    finished_at=None,
                    profile=profile,
                    platform_data=platform_data,
                    status_before=status_before,
                    status_after=platform_campaign_status(workspace, profile=profile, sample_chunk_sizes_by_l=chunks),
                    batch_size=batch_size,
                    max_batches=max_batches,
                    max_jobs=max_jobs,
                    workers=workers,
                    guard_max_wait_seconds=guard_max_wait_seconds,
                    guard_poll_seconds=guard_poll_seconds,
                    gpu_max_memory_mib=gpu_max_memory_mib,
                    idle_residual_gpu_memory_mib=idle_residual_gpu_memory_mib,
                    batches=batches,
                    stop_reason=active_status or "running",
                    jobs_ran=jobs_ran,
                    active_batch=active_batch,
                ),
            )

        batch = run_platform_guarded_batch(
            workspace,
            profile=profile,
            sample_chunk_sizes_by_l=chunks,
            max_jobs=jobs_this_batch,
            workers=workers,
            skip_existing=skip_existing,
            allow_full=True,
            resume_missing=True,
            guard_max_wait_seconds=guard_max_wait_seconds,
            guard_poll_seconds=guard_poll_seconds,
            gpu_max_memory_mib=gpu_max_memory_mib,
            gpu_probe=campaign_gpu_probe,
            sleep_fn=sleep_fn,
            clock=clock,
            platform_probe=lambda: platform_data,
            heartbeat_writer=write_campaign_heartbeat,
        )
        batches.append(batch)
        jobs_ran += int(((batch.get("batch") or {}).get("batch") or {}).get("jobs_ran", 0))
        payload = _guarded_campaign_payload(
            status="guarded_campaign_running",
            started_at=started_at,
            finished_at=None,
            profile=profile,
            platform_data=platform_data,
            status_before=status_before,
            status_after=platform_campaign_status(workspace, profile=profile, sample_chunk_sizes_by_l=chunks),
            batch_size=batch_size,
            max_batches=max_batches,
            max_jobs=max_jobs,
            workers=workers,
            guard_max_wait_seconds=guard_max_wait_seconds,
            guard_poll_seconds=guard_poll_seconds,
            gpu_max_memory_mib=gpu_max_memory_mib,
            idle_residual_gpu_memory_mib=idle_residual_gpu_memory_mib,
            batches=batches,
            stop_reason="running",
            jobs_ran=jobs_ran,
        )
        _write_json(workspace / PLATFORM_RESULT, payload)
        if batch["status"] in {"guarded_batch_wait_timeout", "guarded_batch_no_missing_jobs"}:
            stop_reason = str(batch["status"])
            break

    status_after = platform_campaign_status(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
    if int(status_after["missing_jobs"]) <= 0:
        status = "guarded_campaign_completed"
        stop_reason = stop_reason or "completed_profile"
    elif stop_reason == "guarded_batch_wait_timeout":
        status = "guarded_campaign_wait_timeout"
    else:
        status = "guarded_campaign_partial"
    payload = _guarded_campaign_payload(
        status=status,
        started_at=started_at,
        finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        profile=profile,
        platform_data=platform_data,
        status_before=status_before,
        status_after=status_after,
        batch_size=batch_size,
        max_batches=max_batches,
        max_jobs=max_jobs,
        workers=workers,
        guard_max_wait_seconds=guard_max_wait_seconds,
        guard_poll_seconds=guard_poll_seconds,
        gpu_max_memory_mib=gpu_max_memory_mib,
        idle_residual_gpu_memory_mib=idle_residual_gpu_memory_mib,
        batches=batches,
        stop_reason=stop_reason,
        jobs_ran=jobs_ran,
    )
    _write_json(workspace / PLATFORM_RESULT, payload)
    return payload


def wait_for_gpu_free(
    *,
    max_wait_seconds: float,
    poll_seconds: float,
    gpu_probe: Callable[[], dict[str, Any]],
    sleep_fn: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    on_waiting: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    started = clock()
    snapshots: list[dict[str, Any]] = []
    while True:
        snapshot = gpu_probe()
        snapshots.append(snapshot)
        if bool(snapshot.get("free")):
            return {
                "status": "gpu_free",
                "polls": len(snapshots),
                "waited_seconds": max(0.0, clock() - started),
                "snapshots": snapshots,
            }
        elapsed = max(0.0, clock() - started)
        if max_wait_seconds <= 0 or elapsed >= max_wait_seconds:
            return {
                "status": "gpu_wait_timeout",
                "polls": len(snapshots),
                "waited_seconds": elapsed,
                "snapshots": snapshots,
            }
        if on_waiting is not None:
            on_waiting(
                {
                    "status": "gpu_waiting",
                    "polls": len(snapshots),
                    "waited_seconds": elapsed,
                    "next_poll_seconds": min(poll_seconds, max_wait_seconds - elapsed),
                    "snapshots": snapshots,
                }
            )
        sleep_fn(min(poll_seconds, max_wait_seconds - elapsed))


def gpu_guard_snapshot(*, max_memory_mib: int = DEFAULT_GPU_FREE_MEMORY_MIB) -> dict[str, Any]:
    gpu = _capture(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"])
    apps = _capture(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"])
    memory_used_mib: int | None = None
    utilization_gpu_pct: int | None = None
    if gpu.get("status") == "passed":
        first_line = str(gpu.get("stdout", "")).splitlines()[0] if str(gpu.get("stdout", "")).strip() else ""
        parts = [part.strip() for part in first_line.split(",")]
        if len(parts) >= 2:
            memory_used_mib = _parse_int(parts[0])
            utilization_gpu_pct = _parse_int(parts[1])
    app_lines = [line.strip() for line in str(apps.get("stdout", "")).splitlines() if line.strip()]
    free = (
        gpu.get("status") == "passed"
        and apps.get("status") == "passed"
        and memory_used_mib is not None
        and memory_used_mib <= max_memory_mib
        and not app_lines
    )
    return {
        "status": "passed" if gpu.get("status") == "passed" and apps.get("status") == "passed" else "failed",
        "free": free,
        "memory_used_mib": memory_used_mib,
        "utilization_gpu_pct": utilization_gpu_pct,
        "max_memory_mib": max_memory_mib,
        "compute_app_count": len(app_lines),
        "compute_apps": app_lines,
        "gpu_query": gpu,
        "apps_query": apps,
    }


def _allow_idle_residual_gpu_context(snapshot: dict[str, Any], *, max_memory_mib: int) -> dict[str, Any]:
    if bool(snapshot.get("free")):
        return snapshot
    memory_used_mib = snapshot.get("memory_used_mib")
    utilization_gpu_pct = snapshot.get("utilization_gpu_pct")
    if (
        snapshot.get("status") == "passed"
        and isinstance(memory_used_mib, int)
        and memory_used_mib <= max_memory_mib
        and utilization_gpu_pct == 0
        and int(snapshot.get("compute_app_count") or 0) > 0
    ):
        updated = dict(snapshot)
        updated["free"] = True
        updated["original_free"] = False
        updated["free_reason"] = "idle_residual_gpu_context"
        updated["idle_residual_gpu_memory_mib"] = max_memory_mib
        return updated
    return snapshot


def run_platform_merge(
    workspace: Path = WORKSPACE,
    *,
    profile: str = "final",
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    platform_probe: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    chunks = sample_chunk_sizes_by_l or DEFAULT_CHUNKS_BY_L
    if platform_probe is None:
        platform_probe = platform_profile
    merge = campaign.merge_shards(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
    payload = {
        "schema_version": 1,
        "status": "merge_completed" if merge.get("status") == "completed_profile" else "merge_partial",
        "mode": "merge",
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "paper_id": campaign.PAPER_ID,
        "target_id": campaign.TARGET_ID,
        "profile": profile,
        "platform": platform_probe(),
        "manifest": {
            "sample_chunk_sizes_by_l": chunks,
        },
        "merge": merge,
        "outputs": {
            "platform_result_json": PLATFORM_RESULT,
            "data_csv": "outputs/data/fig3_large_ed_campaign.csv",
            "result_json": "outputs/checks/paper_exact_campaign_result.json",
        },
    }
    _write_json(workspace / PLATFORM_RESULT, payload)
    return payload


def run_platform_campaign(
    workspace: Path = WORKSPACE,
    *,
    profile: str = "final",
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    start_index: int = 0,
    max_jobs: int | None = None,
    batch_size: int = DEFAULT_CAMPAIGN_BATCH_SIZE,
    max_batches: int | None = None,
    workers: int = 1,
    skip_existing: bool = True,
    allow_full: bool = False,
    package_results: bool = False,
    result_bundle_output: Path | None = None,
    platform_probe: Callable[[], dict[str, Any]] | None = None,
    result_packager: Callable[[Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if start_index < 0:
        raise ValueError("start_index must be non-negative")
    if max_jobs is not None and max_jobs <= 0:
        raise ValueError("max_jobs must be positive")
    if max_batches is not None and max_batches <= 0:
        raise ValueError("max_batches must be positive")
    if max_jobs is None and max_batches is None and not allow_full:
        raise ValueError("refusing unbounded campaign without allow_full=True, max_jobs, or max_batches")

    chunks = sample_chunk_sizes_by_l or DEFAULT_CHUNKS_BY_L
    if platform_probe is None:
        platform_probe = platform_profile
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    platform_data = platform_probe()
    manifest_summary: dict[str, Any] | None = None
    batches: list[dict[str, Any]] = []
    next_start_index = start_index
    stop_index = start_index
    try:
        manifest = campaign.write_manifest(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
        jobs_total = int(manifest["jobs_total"])
        manifest_summary = {
            "jobs_total": jobs_total,
            "sample_chunk_sizes_by_l": chunks,
            "manifest_json": "outputs/checks/fig3_large_ed_campaign_manifest.json",
        }
        stop_index = jobs_total if max_jobs is None else min(jobs_total, start_index + max_jobs)
        next_start_index = min(start_index, jobs_total)

        while next_start_index < stop_index:
            if max_batches is not None and len(batches) >= max_batches:
                break
            window_size = min(batch_size, stop_index - next_start_index)
            batch = campaign.run_shards(
                workspace,
                profile=profile,
                workers=workers,
                start_index=next_start_index,
                max_jobs=window_size,
                sample_chunk_sizes_by_l=chunks,
                skip_existing=skip_existing,
            )
            batches.append(batch)
            next_start_index += window_size
            _write_json(
                workspace / PLATFORM_RESULT,
                _campaign_payload(
                    status="campaign_running",
                    started_at=started_at,
                    finished_at=None,
                    profile=profile,
                    platform_data=platform_data,
                    manifest_summary=manifest_summary,
                    start_index=start_index,
                    stop_index=stop_index,
                    next_start_index=next_start_index,
                    max_jobs=max_jobs,
                    batch_size=batch_size,
                    max_batches=max_batches,
                    workers=workers,
                    allow_full=allow_full,
                    package_results=package_results,
                    batches=batches,
                    merge=None,
                    result_bundle=None,
                ),
            )

        merge = campaign.merge_shards(workspace, profile=profile, sample_chunk_sizes_by_l=chunks)
        status = "campaign_completed" if merge.get("status") == "completed_profile" else "campaign_partial"
        finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        payload = _campaign_payload(
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            profile=profile,
            platform_data=platform_data,
            manifest_summary=manifest_summary,
            start_index=start_index,
            stop_index=stop_index,
            next_start_index=next_start_index,
            max_jobs=max_jobs,
            batch_size=batch_size,
            max_batches=max_batches,
            workers=workers,
            allow_full=allow_full,
            package_results=package_results,
            batches=batches,
            merge=merge,
            result_bundle=None,
        )
        _write_json(workspace / PLATFORM_RESULT, payload)

        result_bundle: dict[str, Any] | None = None
        if package_results and status == "campaign_completed":
            output = result_bundle_output or Path("~/PRAgent-dtc-a100-results.tar.gz").expanduser()
            packager = result_packager or (lambda path: _package_result_bundle(workspace, path))
            result_bundle = packager(output)
        elif package_results:
            result_bundle = {"status": "skipped", "reason": "campaign_not_completed"}

        payload = _campaign_payload(
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            profile=profile,
            platform_data=platform_data,
            manifest_summary=manifest_summary,
            start_index=start_index,
            stop_index=stop_index,
            next_start_index=next_start_index,
            max_jobs=max_jobs,
            batch_size=batch_size,
            max_batches=max_batches,
            workers=workers,
            allow_full=allow_full,
            package_results=package_results,
            batches=batches,
            merge=merge,
            result_bundle=result_bundle,
        )
        _write_json(workspace / PLATFORM_RESULT, payload)
        return payload
    except Exception as exc:
        payload = _failure_payload(
            mode="campaign",
            started_at=started_at,
            profile=profile,
            platform_data=platform_data,
            manifest_summary=manifest_summary,
            error=exc,
        )
        payload["campaign"] = {
            "start_index": start_index,
            "stop_index": stop_index,
            "next_start_index": next_start_index,
            "max_jobs": max_jobs,
            "batch_size": batch_size,
            "max_batches": max_batches,
            "batches_run": len(batches),
        }
        payload["batches"] = batches
        _write_json(workspace / PLATFORM_RESULT, payload)
        raise


def platform_campaign_status(
    workspace: Path = WORKSPACE,
    *,
    profile: str = "final",
    sample_chunk_sizes_by_l: dict[int, int] | None = None,
    missing_head: int = 20,
) -> dict[str, Any]:
    chunks = sample_chunk_sizes_by_l or DEFAULT_CHUNKS_BY_L
    jobs = campaign.build_jobs(profile, sample_chunk_sizes_by_l=chunks)
    jobs_total = len(jobs)
    completed_indices = [
        job_index
        for job_index in range(jobs_total)
        if campaign._shard_exists(workspace, job_index)  # noqa: SLF001
    ]
    completed_set = set(completed_indices)
    missing_indices = [job_index for job_index in range(jobs_total) if job_index not in completed_set]
    next_start_index = missing_indices[0] if missing_indices else jobs_total

    campaign_result = _read_json_if_exists(workspace / "outputs" / "checks" / "paper_exact_campaign_result.json")
    platform_result = _read_json_if_exists(workspace / PLATFORM_RESULT)
    result_bundle = platform_result.get("result_bundle") if isinstance(platform_result.get("result_bundle"), dict) else None
    merge_status = campaign_result.get("status") if campaign_result else None
    platform_status = platform_result.get("status") if platform_result else None
    status = _status_label(
        jobs_total=jobs_total,
        jobs_completed=len(completed_indices),
        merge_status=merge_status,
        result_bundle=result_bundle,
    )

    return {
        "schema_version": 1,
        "status": status,
        "paper_id": campaign.PAPER_ID,
        "target_id": campaign.TARGET_ID,
        "profile": profile,
        "jobs_total": jobs_total,
        "jobs_completed": len(completed_indices),
        "missing_jobs": len(missing_indices),
        "completed_ratio": (len(completed_indices) / jobs_total) if jobs_total else 0.0,
        "next_start_index": next_start_index,
        "missing_job_indices_head": missing_indices[:missing_head],
        "platform_status": platform_status,
        "merge_status": merge_status,
        "result_bundle_status": result_bundle.get("status") if result_bundle else None,
        "recommended_next_command": _recommended_next_command(
            status=status,
            profile=profile,
            next_start_index=next_start_index,
            missing_jobs=len(missing_indices),
        ),
        "outputs": {
            "platform_result_json": PLATFORM_RESULT,
            "data_shards": "outputs/data/fig3_large_ed_campaign_shards/",
            "check_shards": "outputs/checks/fig3_large_ed_campaign_shards/",
            "data_csv": "outputs/data/fig3_large_ed_campaign.csv",
            "result_json": "outputs/checks/paper_exact_campaign_result.json",
        },
    }


def _status_label(
    *,
    jobs_total: int,
    jobs_completed: int,
    merge_status: str | None,
    result_bundle: dict[str, Any] | None,
) -> str:
    if result_bundle and result_bundle.get("status") == "result_bundle_created":
        return "result_packaged"
    if merge_status == "completed_profile":
        return "completed_profile"
    if merge_status == "partial_profile":
        return "merged_partial"
    if jobs_completed <= 0:
        return "shards_missing"
    if jobs_completed < jobs_total:
        return "shards_partial"
    return "shards_complete"


def _recommended_next_command(
    *,
    status: str,
    profile: str,
    next_start_index: int,
    missing_jobs: int,
) -> str:
    if status in {"shards_missing", "shards_partial"}:
        return (
            "python case/1608.02589/scripts/run_fig3_a100_platform.py "
            "--mode campaign "
            f"--profile {profile} "
            '--sample-chunk-sizes-by-l "$CHUNKS" '
            f"--start-index {next_start_index} "
            f"--max-jobs {missing_jobs} "
            "--workers <count> "
            "--batch-size <jobs> "
            "--package-results"
        )
    if status == "shards_complete":
        return (
            "python case/1608.02589/scripts/run_fig3_a100_platform.py "
            "--mode merge "
            f"--profile {profile} "
            '--sample-chunk-sizes-by-l "$CHUNKS"'
        )
    if status in {"completed_profile", "merged_partial"}:
        return "python PRAgent-workflow/scripts/package_dtc_a100_results.py build --output ~/PRAgent-dtc-a100-results.tar.gz"
    if status == "result_packaged":
        return "download ~/PRAgent-dtc-a100-results.tar.gz and run local package_dtc_a100_results.py verify"
    return ""


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def platform_profile() -> dict[str, Any]:
    compute_backend = os.environ.get("DTC_COMPUTE_BACKEND", "numpy")
    return {
        "hostname": _capture(["hostname"]),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "cpu_count": os.cpu_count(),
        "memory_total_bytes": _memory_total_bytes(),
        "nvidia_smi": _capture(["nvidia-smi", "-L"]),
        "compute_backend": compute_backend,
        "thread_env": {key: os.environ.get(key) for key in THREAD_ENV_KEYS},
    }


def _campaign_payload(
    *,
    status: str,
    started_at: str,
    finished_at: str | None,
    profile: str,
    platform_data: dict[str, Any],
    manifest_summary: dict[str, Any] | None,
    start_index: int,
    stop_index: int,
    next_start_index: int,
    max_jobs: int | None,
    batch_size: int,
    max_batches: int | None,
    workers: int,
    allow_full: bool,
    package_results: bool,
    batches: list[dict[str, Any]],
    merge: dict[str, Any] | None,
    result_bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "mode": "campaign",
        "started_at": started_at,
        "paper_id": campaign.PAPER_ID,
        "target_id": campaign.TARGET_ID,
        "profile": profile,
        "platform": platform_data,
        "manifest": manifest_summary,
        "campaign": {
            "start_index": start_index,
            "stop_index": stop_index,
            "next_start_index": next_start_index,
            "max_jobs": max_jobs,
            "batch_size": batch_size,
            "max_batches": max_batches,
            "workers": workers,
            "allow_full": allow_full,
            "package_results": package_results,
            "batches_run": len(batches),
            "jobs_completed_in_batches": sum(int(batch.get("jobs_completed", 0)) for batch in batches),
        },
        "batches": batches,
        "outputs": {
            "platform_result_json": PLATFORM_RESULT,
            "data_shards": "outputs/data/fig3_large_ed_campaign_shards/",
            "check_shards": "outputs/checks/fig3_large_ed_campaign_shards/",
            "data_csv": "outputs/data/fig3_large_ed_campaign.csv",
            "result_json": "outputs/checks/paper_exact_campaign_result.json",
        },
    }
    if finished_at is not None:
        payload["finished_at"] = finished_at
    if merge is not None:
        payload["merge"] = merge
    if result_bundle is not None:
        payload["result_bundle"] = result_bundle
    return payload


def _guarded_batch_payload(
    *,
    status: str,
    started_at: str,
    finished_at: str | None,
    profile: str,
    platform_data: dict[str, Any],
    status_before: dict[str, Any],
    selected_start_index: int,
    max_jobs: int | None,
    workers: int,
    resume_missing: bool,
    guard: dict[str, Any],
    batch: dict[str, Any] | None,
    status_after: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "mode": "guarded-batch",
        "started_at": started_at,
        "paper_id": campaign.PAPER_ID,
        "target_id": campaign.TARGET_ID,
        "profile": profile,
        "platform": platform_data,
        "status_before": status_before,
        "selected_start_index": selected_start_index,
        "max_jobs": max_jobs,
        "workers": workers,
        "resume_missing": resume_missing,
        "guard": guard,
        "status_after": status_after,
        "outputs": {
            "platform_result_json": PLATFORM_RESULT,
            "data_shards": "outputs/data/fig3_large_ed_campaign_shards/",
            "check_shards": "outputs/checks/fig3_large_ed_campaign_shards/",
        },
    }
    if finished_at is not None:
        payload["finished_at"] = finished_at
    if batch is not None:
        payload["batch"] = batch
    return payload


def _guarded_campaign_payload(
    *,
    status: str,
    started_at: str,
    finished_at: str | None,
    profile: str,
    platform_data: dict[str, Any],
    status_before: dict[str, Any],
    status_after: dict[str, Any],
    batch_size: int,
    max_batches: int | None,
    max_jobs: int | None,
    workers: int,
    guard_max_wait_seconds: float,
    guard_poll_seconds: float,
    gpu_max_memory_mib: int,
    idle_residual_gpu_memory_mib: int,
    batches: list[dict[str, Any]],
    stop_reason: str,
    jobs_ran: int,
    active_batch: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "mode": "guarded-campaign",
        "started_at": started_at,
        "paper_id": campaign.PAPER_ID,
        "target_id": campaign.TARGET_ID,
        "profile": profile,
        "platform": platform_data,
        "status_before": status_before,
        "status_after": status_after,
        "campaign": {
            "batch_size": batch_size,
            "max_batches": max_batches,
            "max_jobs": max_jobs,
            "workers": workers,
            "guard_max_wait_seconds": guard_max_wait_seconds,
            "guard_poll_seconds": guard_poll_seconds,
            "gpu_max_memory_mib": gpu_max_memory_mib,
            "idle_residual_gpu_memory_mib": idle_residual_gpu_memory_mib,
            "batches_run": len(batches),
            "jobs_ran": jobs_ran,
            "stop_reason": stop_reason,
        },
        "batches": batches,
        "outputs": {
            "platform_result_json": PLATFORM_RESULT,
            "data_shards": "outputs/data/fig3_large_ed_campaign_shards/",
            "check_shards": "outputs/checks/fig3_large_ed_campaign_shards/",
            "data_csv": "outputs/data/fig3_large_ed_campaign.csv",
            "result_json": "outputs/checks/paper_exact_campaign_result.json",
        },
    }
    if finished_at is not None:
        payload["finished_at"] = finished_at
    if active_batch is not None:
        payload["active_batch"] = active_batch
    return payload


def _package_result_bundle(workspace: Path, output: Path) -> dict[str, Any]:
    repo_root = _repo_root_for_workspace(workspace)
    script = repo_root / "agent" / "harness" / "scripts" / "package_dtc_a100_results.py"
    if not script.is_file():
        raise FileNotFoundError(f"missing result packager: {script}")
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "build",
            "--repo-root",
            str(repo_root),
            "--output",
            str(output.expanduser()),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "result packaging failed")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"result packager returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("result packager returned a non-object JSON payload")
    return payload


def _repo_root_for_workspace(workspace: Path) -> Path:
    for candidate in [workspace, *workspace.parents]:
        if (candidate / "agent" / "harness" / "scripts" / "package_dtc_a100_results.py").is_file():
            return candidate
    raise FileNotFoundError("could not locate repository root from workspace")


def _failure_payload(
    *,
    mode: str,
    started_at: str,
    profile: str,
    platform_data: dict[str, Any],
    manifest_summary: dict[str, Any] | None,
    error: Exception,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": f"{mode}_failed",
        "mode": mode,
        "started_at": started_at,
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "paper_id": campaign.PAPER_ID,
        "target_id": campaign.TARGET_ID,
        "profile": profile,
        "platform": platform_data,
        "manifest": manifest_summary,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        },
        "outputs": {
            "platform_result_json": PLATFORM_RESULT,
        },
    }


def _capture(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        return {"status": "missing_command", "command": command}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "command": command}
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _parse_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _memory_total_bytes() -> int | None:
    if not hasattr(os, "sysconf"):
        return None
    try:
        pages = int(os.sysconf("SC_PHYS_PAGES"))
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
    except (OSError, ValueError):
        return None
    return pages * page_size


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_heartbeat(
    workspace: Path,
    payload: dict[str, Any],
    heartbeat_writer: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    if heartbeat_writer is not None:
        heartbeat_writer(payload)
        return
    _write_json(workspace / PLATFORM_RESULT, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or inspect the DTC Fig. 3 A100 platform campaign.")
    parser.add_argument(
        "--mode",
        choices=["canary", "batch", "guarded-batch", "guarded-campaign", "campaign", "merge", "status"],
        default="canary",
    )
    parser.add_argument("--profile", choices=sorted(campaign.PROFILE_SAMPLE_COUNTS), default="final")
    parser.add_argument("--sample-chunk-sizes-by-l", default="8:500,10:500,12:100,14:10")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_CAMPAIGN_BATCH_SIZE)
    parser.add_argument("--max-batches", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--no-skip-existing", action="store_true")
    parser.add_argument("--allow-full", action="store_true")
    parser.add_argument("--package-results", action="store_true")
    parser.add_argument("--result-bundle-output", default=None)
    parser.add_argument("--resume-missing", action="store_true")
    parser.add_argument("--guard-max-wait-seconds", type=float, default=0.0)
    parser.add_argument("--guard-poll-seconds", type=float, default=DEFAULT_GUARD_POLL_SECONDS)
    parser.add_argument("--gpu-max-memory-mib", type=int, default=DEFAULT_GPU_FREE_MEMORY_MIB)
    parser.add_argument("--idle-residual-gpu-memory-mib", type=int, default=DEFAULT_IDLE_RESIDUAL_GPU_MEMORY_MIB)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chunks = campaign.parse_chunk_sizes_by_l(args.sample_chunk_sizes_by_l)
    if args.mode == "merge":
        payload = run_platform_merge(WORKSPACE, profile=args.profile, sample_chunk_sizes_by_l=chunks)
    elif args.mode == "status":
        payload = platform_campaign_status(WORKSPACE, profile=args.profile, sample_chunk_sizes_by_l=chunks)
    elif args.mode == "campaign":
        payload = run_platform_campaign(
            WORKSPACE,
            profile=args.profile,
            sample_chunk_sizes_by_l=chunks,
            start_index=args.start_index,
            max_jobs=args.max_jobs,
            batch_size=args.batch_size,
            max_batches=args.max_batches,
            workers=args.workers,
            skip_existing=not args.no_skip_existing,
            allow_full=args.allow_full,
            package_results=args.package_results,
            result_bundle_output=Path(args.result_bundle_output).expanduser() if args.result_bundle_output else None,
        )
    elif args.mode == "guarded-batch":
        payload = run_platform_guarded_batch(
            WORKSPACE,
            profile=args.profile,
            sample_chunk_sizes_by_l=chunks,
            start_index=args.start_index,
            max_jobs=args.max_jobs,
            workers=args.workers,
            skip_existing=not args.no_skip_existing,
            allow_full=args.allow_full,
            resume_missing=args.resume_missing,
            guard_max_wait_seconds=args.guard_max_wait_seconds,
            guard_poll_seconds=args.guard_poll_seconds,
            gpu_max_memory_mib=args.gpu_max_memory_mib,
        )
    elif args.mode == "guarded-campaign":
        payload = run_platform_guarded_campaign(
            WORKSPACE,
            profile=args.profile,
            sample_chunk_sizes_by_l=chunks,
            batch_size=args.batch_size,
            max_batches=args.max_batches,
            max_jobs=args.max_jobs,
            workers=args.workers,
            skip_existing=not args.no_skip_existing,
            allow_full=args.allow_full,
            guard_max_wait_seconds=args.guard_max_wait_seconds,
            guard_poll_seconds=args.guard_poll_seconds,
            gpu_max_memory_mib=args.gpu_max_memory_mib,
            idle_residual_gpu_memory_mib=args.idle_residual_gpu_memory_mib,
        )
    else:
        payload = run_platform_batch(
            WORKSPACE,
            mode=args.mode,
            profile=args.profile,
            sample_chunk_sizes_by_l=chunks,
            start_index=args.start_index,
            max_jobs=args.max_jobs,
            workers=args.workers,
            skip_existing=not args.no_skip_existing,
            allow_full=args.allow_full,
        )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
