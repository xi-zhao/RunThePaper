from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import time
from typing import Iterable

import numpy as np


def gaussian_target_amplitude(*, grid_size: int, centers: np.ndarray, sigma: float) -> np.ndarray:
    if grid_size <= 0:
        raise ValueError("grid_size must be positive")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    centers = np.asarray(centers, dtype=np.float64)
    if centers.ndim != 2 or centers.shape[1] != 2:
        raise ValueError("centers must have shape (n, 2)")

    yy, xx = np.mgrid[0:grid_size, 0:grid_size]
    amplitude = np.zeros((grid_size, grid_size), dtype=np.float64)
    for row, col in centers:
        dist2 = (yy - row) ** 2 + (xx - col) ** 2
        amplitude += np.exp(-0.5 * dist2 / (sigma * sigma))
    max_value = float(amplitude.max())
    if max_value > 0.0:
        amplitude /= max_value
    return amplitude


def phase_profile_aware_wgs(
    *,
    target_amplitude: np.ndarray,
    target_phase: np.ndarray,
    input_amplitude: np.ndarray,
    iterations: int,
    initial_slm_phase: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    target_amplitude = np.asarray(target_amplitude, dtype=np.float64)
    target_phase = np.asarray(target_phase, dtype=np.float64)
    input_amplitude = np.asarray(input_amplitude, dtype=np.float64)
    if target_amplitude.shape != target_phase.shape or target_amplitude.shape != input_amplitude.shape:
        raise ValueError("target_amplitude, target_phase, and input_amplitude must have the same shape")

    if initial_slm_phase is None:
        slm_phase = np.zeros_like(target_amplitude)
    else:
        slm_phase = np.asarray(initial_slm_phase, dtype=np.float64)
        if slm_phase.shape != target_amplitude.shape:
            raise ValueError("initial_slm_phase must match target shape")

    support = target_amplitude > 1e-4
    constrained_target = target_amplitude * np.exp(1j * target_phase)
    slm_field = input_amplitude * np.exp(1j * slm_phase)

    for _ in range(iterations):
        focal_field = np.fft.fftshift(np.fft.fft2(slm_field, norm="ortho"))
        constrained_focal = focal_field.copy()
        constrained_focal[support] = constrained_target[support]
        constrained_focal[~support] *= 0.2
        back_field = np.fft.ifft2(np.fft.ifftshift(constrained_focal), norm="ortho")
        slm_phase = np.angle(back_field)
        slm_field = input_amplitude * np.exp(1j * slm_phase)

    final_focal = np.fft.fftshift(np.fft.fft2(slm_field, norm="ortho"))
    return final_focal, slm_phase


def run_reduced_p2wgs_pilot(
    *,
    output_dir: Path,
    grid_size: int,
    initial_side: int,
    target_side: int,
    samples: int,
    frames: int,
    iterations: Iterable[int],
    sigma: float,
    seed: int,
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    iteration_values = [int(value) for value in iterations]
    if not iteration_values:
        raise ValueError("at least one iteration count is required")

    path_planner = load_path_planner_module()
    rows = []
    for sample_idx in range(samples):
        sample = path_planner.generate_path_planning_sample(
            initial_side=initial_side,
            target_side=target_side,
            loading_probability=0.75,
            k_neighbors=min(16, target_side * target_side),
            seed=seed + sample_idx,
        )
        centers_by_frame = linear_trajectory_centers(
            atom_positions=sample.atom_positions,
            target_positions=sample.target_positions,
            assignment=sample.optimal_assignment,
            initial_side=initial_side,
            grid_size=grid_size,
            frames=frames,
        )
        input_amplitude = np.ones((grid_size, grid_size), dtype=np.float64)
        target_phase = np.zeros((grid_size, grid_size), dtype=np.float64)
        for iteration_count in iteration_values:
            focal_fields = []
            slm_phase: np.ndarray | None = None
            for centers in centers_by_frame:
                target_amplitude = gaussian_target_amplitude(
                    grid_size=grid_size,
                    centers=centers,
                    sigma=sigma,
                )
                focal_field, slm_phase = phase_profile_aware_wgs(
                    target_amplitude=target_amplitude,
                    target_phase=target_phase,
                    input_amplitude=input_amplitude,
                    iterations=iteration_count,
                    initial_slm_phase=slm_phase,
                )
                focal_fields.append(focal_field)
            rows.append(
                {
                    "sample": sample_idx,
                    "iterations": iteration_count,
                    **continuity_metrics(focal_fields, centers_by_frame),
                }
            )

    metrics: dict[str, object] = {
        "status": "completed",
        "paper_id": "2604.08669",
        "target": "reduced_scale_p2wgs_continuity",
        "config": {
            "grid_size": grid_size,
            "initial_side": initial_side,
            "target_side": target_side,
            "samples": samples,
            "frames": frames,
            "iterations": iteration_values,
            "sigma": sigma,
            "seed": seed,
        },
        "summary": summarize_continuity_rows(rows),
        "rows": rows,
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def run_software_assembly_pipeline(
    *,
    output_dir: Path,
    grid_size: int,
    initial_side: int,
    target_side: int,
    frames: int,
    p2wgs_iterations: int,
    sigma: float,
    seed: int,
    loading_probability: float,
    k_neighbors: int,
    checkpoint_path: Path | None = None,
    assignment_strategy: str = "auto",
    device: str = "cpu",
    path_planning_ms: float | None = None,
    slm_refresh_ms: float,
    transfer_delay_ms: float,
    graph_backend: str = "auto",
) -> dict[str, object]:
    if p2wgs_iterations <= 0:
        raise ValueError("p2wgs_iterations must be positive")
    if frames < 2:
        raise ValueError("frames must be at least 2")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path_planner = load_path_planner_module()

    sample, sample_timings = path_planner.generate_path_planning_sample_with_timing(
        initial_side=initial_side,
        target_side=target_side,
        loading_probability=loading_probability,
        k_neighbors=k_neighbors,
        seed=seed,
        graph_backend=graph_backend,
    )
    assignment, assignment_source, assignment_decoder, assignment_wall_ms = select_pipeline_assignment(
        path_planner=path_planner,
        sample=sample,
        checkpoint_path=checkpoint_path,
        assignment_strategy=assignment_strategy,
        device=device,
        fallback_assignment_wall_ms=float(sample_timings["assignment_seconds"]) * 1000.0,
    )
    distance_metrics = path_planner.assignment_metrics(sample, assignment)

    centers_by_frame = linear_trajectory_centers(
        atom_positions=sample.atom_positions,
        target_positions=sample.target_positions,
        assignment=assignment,
        initial_side=initial_side,
        grid_size=grid_size,
        frames=frames,
    )
    input_amplitude = np.ones((grid_size, grid_size), dtype=np.float64)
    target_phase = np.zeros((grid_size, grid_size), dtype=np.float64)
    focal_fields = []
    generation_ms = []
    slm_phase: np.ndarray | None = None
    for centers in centers_by_frame:
        target_amplitude = gaussian_target_amplitude(grid_size=grid_size, centers=centers, sigma=sigma)
        frame_started = time.monotonic()
        focal_field, slm_phase = phase_profile_aware_wgs(
            target_amplitude=target_amplitude,
            target_phase=target_phase,
            input_amplitude=input_amplitude,
            iterations=p2wgs_iterations,
            initial_slm_phase=slm_phase,
        )
        generation_ms.append((time.monotonic() - frame_started) * 1000.0)
        focal_fields.append(focal_field)

    p2wgs_continuity = continuity_metrics(focal_fields, centers_by_frame)
    mean_generation_ms = float(np.mean(generation_ms))
    measured_path_planning_ms = assignment_wall_ms
    measured_path_planning_source = (
        "measured_local_hungarian_assignment"
        if assignment_source == "hungarian_ground_truth"
        else "measured_local_gnn_predict_decode"
    )
    effective_path_planning_ms = float(path_planning_ms) if path_planning_ms is not None else measured_path_planning_ms
    total_assembly_time = pipelined_assembly_time_ms(
        path_planning_ms=effective_path_planning_ms,
        per_frame_generation_ms=mean_generation_ms,
        slm_refresh_ms=slm_refresh_ms,
        frames=frames,
        transfer_delay_ms=transfer_delay_ms,
    )

    metrics: dict[str, object] = {
        "status": "completed",
        "paper_id": "2604.08669",
        "target": "software_end_to_end_assembly_pipeline",
        "interfaces": {
            "fig3_to_fig4": "decoded atom-target assignment is reused as moving-tweezer trajectories",
            "fig4_to_fig5": "measured P2WGS frame-generation time feeds the pipelined assembly model",
            "hardware_boundary": "SLM refresh, transfer latency, vacuum lifetime, and real camera/atom feedback are parameters here",
        },
        "config": {
            "grid_size": grid_size,
            "initial_side": initial_side,
            "target_side": target_side,
            "frames": frames,
            "p2wgs_iterations": p2wgs_iterations,
            "sigma": sigma,
            "seed": seed,
            "loading_probability": loading_probability,
            "k_neighbors": k_neighbors,
            "checkpoint_path": str(checkpoint_path) if checkpoint_path is not None else None,
            "assignment_strategy": resolve_assignment_strategy(assignment_strategy, checkpoint_path),
            "device": device,
            "graph_backend": graph_backend,
            "slm_refresh_ms": slm_refresh_ms,
            "transfer_delay_ms": transfer_delay_ms,
        },
        "path_planning": {
            "assignment_strategy": resolve_assignment_strategy(assignment_strategy, checkpoint_path),
            "assignment_source": assignment_source,
            "assignment_decoder": assignment_decoder,
            "atom_count": int(len(sample.atom_positions)),
            "target_count": int(sample.target_count),
            "sample_generation_timings_seconds": {key: float(value) for key, value in sample_timings.items()},
            "assignment_wall_ms": float(assignment_wall_ms),
            **distance_metrics,
        },
        "p2wgs": {
            "frames": frames,
            "iterations": p2wgs_iterations,
            "mean_generation_ms": mean_generation_ms,
            "max_generation_ms": float(np.max(generation_ms)),
            "min_generation_ms": float(np.min(generation_ms)),
            **p2wgs_continuity,
        },
        "timing": {
            "path_planning_ms": effective_path_planning_ms,
            "path_planning_ms_source": "configured" if path_planning_ms is not None else measured_path_planning_source,
            "measured_path_planning_ms": measured_path_planning_ms,
            "per_frame_generation_ms": mean_generation_ms,
            "slm_refresh_ms": float(slm_refresh_ms),
            "transfer_delay_ms": float(transfer_delay_ms),
            "frames": frames,
            "per_frame_bottleneck_ms": max(mean_generation_ms, float(slm_refresh_ms)),
            "total_assembly_time_ms": total_assembly_time,
        },
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def run_software_assembly_sweep(
    *,
    output_dir: Path,
    configs: Iterable[dict[str, object]],
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_values = [dict(config) for config in configs]
    if not config_values:
        raise ValueError("at least one sweep config is required")

    rows: list[dict[str, object]] = []
    for index, config in enumerate(config_values):
        config_id = sanitize_sweep_config_id(str(config.get("config_id") or f"config_{index:03d}"))
        run_dir = output_dir / "runs" / config_id
        pipeline_metrics = run_software_assembly_pipeline(
            output_dir=run_dir,
            grid_size=int(config["grid_size"]),
            initial_side=int(config["initial_side"]),
            target_side=int(config["target_side"]),
            frames=int(config["frames"]),
            p2wgs_iterations=int(config["p2wgs_iterations"]),
            sigma=float(config["sigma"]),
            seed=int(config["seed"]),
            loading_probability=float(config["loading_probability"]),
            k_neighbors=int(config["k_neighbors"]),
            checkpoint_path=optional_path(config.get("checkpoint_path")),
            assignment_strategy=str(config.get("assignment_strategy", "auto")),
            device=str(config.get("device", "cpu")),
            path_planning_ms=optional_float(config.get("path_planning_ms")),
            slm_refresh_ms=float(config["slm_refresh_ms"]),
            transfer_delay_ms=float(config["transfer_delay_ms"]),
            graph_backend=str(config.get("graph_backend", "auto")),
        )
        rows.append(flatten_software_assembly_row(config_id, output_dir, run_dir, pipeline_metrics))

    metrics: dict[str, object] = {
        "status": "completed",
        "paper_id": "2604.08669",
        "target": "software_assembly_reproduction_sweep",
        "summary": summarize_software_assembly_sweep_rows(rows),
        "rows": rows,
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def flatten_software_assembly_row(
    config_id: str,
    output_dir: Path,
    run_dir: Path,
    pipeline_metrics: dict[str, object],
) -> dict[str, object]:
    config = pipeline_metrics["config"]
    path_planning = pipeline_metrics["path_planning"]
    p2wgs = pipeline_metrics["p2wgs"]
    timing = pipeline_metrics["timing"]
    return {
        "config_id": config_id,
        "status": pipeline_metrics["status"],
        "metrics_path": str((run_dir / "metrics.json").relative_to(output_dir)),
        "assignment_source": path_planning["assignment_source"],
        "assignment_strategy": path_planning["assignment_strategy"],
        "assignment_decoder": path_planning["assignment_decoder"],
        "initial_side": int(config["initial_side"]),
        "target_side": int(config["target_side"]),
        "target_count": int(path_planning["target_count"]),
        "frames": int(config["frames"]),
        "p2wgs_iterations": int(config["p2wgs_iterations"]),
        "average_distance_gap": float(path_planning["average_distance_gap"]),
        "max_distance_gap": float(path_planning["max_distance_gap"]),
        "mean_intensity_continuity": float(p2wgs["mean_intensity_continuity"]),
        "max_intensity_continuity": float(p2wgs["max_intensity_continuity"]),
        "mean_phase_continuity": float(p2wgs["mean_phase_continuity"]),
        "max_phase_continuity": float(p2wgs["max_phase_continuity"]),
        "mean_generation_ms": float(p2wgs["mean_generation_ms"]),
        "path_planning_ms": float(timing["path_planning_ms"]),
        "slm_refresh_ms": float(timing["slm_refresh_ms"]),
        "total_assembly_time_ms": float(timing["total_assembly_time_ms"]),
    }


def summarize_software_assembly_sweep_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    completed_rows = [row for row in rows if row["status"] == "completed"]
    total_times = np.asarray([row["total_assembly_time_ms"] for row in completed_rows], dtype=np.float64)
    generation_times = np.asarray([row["mean_generation_ms"] for row in completed_rows], dtype=np.float64)
    best_row = min(completed_rows, key=lambda row: float(row["total_assembly_time_ms"])) if completed_rows else None
    return {
        "config_count": len(rows),
        "completed_count": len(completed_rows),
        "assignment_sources": sorted({str(row["assignment_source"]) for row in completed_rows}),
        "assignment_strategies": sorted({str(row["assignment_strategy"]) for row in completed_rows}),
        "target_counts": sorted({int(row["target_count"]) for row in completed_rows}),
        "mean_generation_ms": float(np.mean(generation_times)) if completed_rows else None,
        "mean_total_assembly_time_ms": float(np.mean(total_times)) if completed_rows else None,
        "max_total_assembly_time_ms": float(np.max(total_times)) if completed_rows else None,
        "best_total_assembly_config_id": str(best_row["config_id"]) if best_row is not None else None,
        "max_average_distance_gap": (
            float(np.max([row["average_distance_gap"] for row in completed_rows])) if completed_rows else None
        ),
        "max_mean_intensity_continuity": (
            float(np.max([row["mean_intensity_continuity"] for row in completed_rows])) if completed_rows else None
        ),
    }


def sanitize_sweep_config_id(config_id: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in config_id.strip())
    return cleaned or "config"


def optional_path(value: object) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"", "none", "null"}:
        return None
    return Path(text)


def optional_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"", "none", "null"}:
        return None
    return float(text)


def resolve_assignment_strategy(strategy: str, checkpoint_path: Path | None) -> str:
    normalized = str(strategy).strip().lower()
    if normalized == "auto":
        return "gnn_score_hungarian" if checkpoint_path is not None else "hungarian_ground_truth"
    if normalized in {"hungarian_ground_truth", "gnn_score_hungarian", "modified_auction"}:
        return normalized
    raise ValueError(
        "assignment_strategy must be auto, hungarian_ground_truth, gnn_score_hungarian, or modified_auction"
    )


def select_pipeline_assignment(
    *,
    path_planner,
    sample,
    checkpoint_path: Path | None,
    assignment_strategy: str,
    device: str,
    fallback_assignment_wall_ms: float,
) -> tuple[np.ndarray, str, str, float]:
    resolved_strategy = resolve_assignment_strategy(assignment_strategy, checkpoint_path)
    if resolved_strategy == "hungarian_ground_truth":
        return (
            sample.optimal_assignment,
            "hungarian_ground_truth",
            "linear_sum_assignment_distance_labels",
            float(fallback_assignment_wall_ms),
        )
    if checkpoint_path is None:
        raise ValueError(f"{resolved_strategy} assignment_strategy requires checkpoint_path")
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"checkpoint_path does not exist: {checkpoint_path}")
    model = path_planner.load_edge_scoring_model(checkpoint_path, device=device)
    started = time.monotonic()
    edge_scores = path_planner.predict_edge_scores(model, sample)
    if resolved_strategy == "modified_auction":
        assignment = path_planner.decode_assignment_with_modified_auction(sample, edge_scores)
        return (
            assignment,
            "gnn_checkpoint_modified_auction",
            "modified_auction_bidding_on_predicted_edge_scores",
            (time.monotonic() - started) * 1000.0,
        )

    assignment = path_planner.decode_assignment_from_edge_scores(sample, edge_scores)
    return (
        assignment,
        "gnn_checkpoint_score_decoder",
        "linear_sum_assignment_on_predicted_edge_scores",
        (time.monotonic() - started) * 1000.0,
    )


def linear_trajectory_centers(
    *,
    atom_positions: np.ndarray,
    target_positions: np.ndarray,
    assignment: np.ndarray,
    initial_side: int,
    grid_size: int,
    frames: int,
) -> np.ndarray:
    if frames < 2:
        raise ValueError("frames must be at least 2")
    atom_idx = assignment[:, 0].astype(np.int64)
    target_idx = assignment[:, 1].astype(np.int64)
    start = lattice_to_pixel(atom_positions[atom_idx], initial_side=initial_side, grid_size=grid_size)
    end = lattice_to_pixel(target_positions[target_idx], initial_side=initial_side, grid_size=grid_size)
    time = np.linspace(0.0, 1.0, frames, dtype=np.float64)[:, None, None]
    return start[None, :, :] * (1.0 - time) + end[None, :, :] * time


def lattice_to_pixel(positions: np.ndarray, *, initial_side: int, grid_size: int, margin: float = 4.0) -> np.ndarray:
    if initial_side <= 1:
        raise ValueError("initial_side must be greater than 1")
    scale = (grid_size - 1.0 - 2.0 * margin) / float(initial_side - 1)
    return margin + np.asarray(positions, dtype=np.float64) * scale


def continuity_metrics(focal_fields: list[np.ndarray], centers_by_frame: np.ndarray) -> dict[str, float]:
    intensities = []
    phases = []
    for frame_idx, field in enumerate(focal_fields):
        intensity, phase = trap_properties(field, centers_by_frame[frame_idx])
        intensities.append(intensity)
        phases.append(phase)
    intensity_steps = []
    phase_steps = []
    for idx in range(len(focal_fields) - 1):
        current_i = intensities[idx]
        next_i = intensities[idx + 1]
        denominator = np.maximum((current_i + next_i) * 0.5, 1e-12)
        intensity_steps.append(float(np.mean(np.abs(next_i - current_i) / denominator)))
        phase_steps.append(float(np.mean(np.abs(wrapped_phase_delta(phases[idx + 1] - phases[idx])) / (2.0 * np.pi))))
    return {
        "mean_intensity_continuity": float(np.mean(intensity_steps)),
        "max_intensity_continuity": float(np.max(intensity_steps)),
        "mean_phase_continuity": float(np.mean(phase_steps)),
        "max_phase_continuity": float(np.max(phase_steps)),
    }


def trap_properties(field: np.ndarray, centers: np.ndarray, window_radius: int = 2) -> tuple[np.ndarray, np.ndarray]:
    field = np.asarray(field)
    centers = np.asarray(centers, dtype=np.float64)
    intensity = np.abs(field) ** 2
    total_intensity = []
    phase = []
    height, width = intensity.shape
    for row, col in centers:
        row_idx = int(np.clip(round(float(row)), 0, height - 1))
        col_idx = int(np.clip(round(float(col)), 0, width - 1))
        r0 = max(0, row_idx - window_radius)
        r1 = min(height, row_idx + window_radius + 1)
        c0 = max(0, col_idx - window_radius)
        c1 = min(width, col_idx + window_radius + 1)
        total_intensity.append(float(np.sum(intensity[r0:r1, c0:c1])))
        phase.append(float(np.angle(field[row_idx, col_idx])))
    return np.asarray(total_intensity, dtype=np.float64), np.asarray(phase, dtype=np.float64)


def wrapped_phase_delta(delta: np.ndarray) -> np.ndarray:
    return (np.asarray(delta, dtype=np.float64) + np.pi) % (2.0 * np.pi) - np.pi


def summarize_continuity_rows(rows: list[dict[str, float]]) -> dict[str, object]:
    summary: dict[str, object] = {
        "samples": len({int(row["sample"]) for row in rows}),
        "iteration_counts": sorted({int(row["iterations"]) for row in rows}),
        "mean_intensity_continuity_by_iteration": {},
        "mean_phase_continuity_by_iteration": {},
        "max_intensity_continuity_by_iteration": {},
        "max_phase_continuity_by_iteration": {},
    }
    for iteration_count in summary["iteration_counts"]:
        subset = [row for row in rows if int(row["iterations"]) == iteration_count]
        key = str(iteration_count)
        summary["mean_intensity_continuity_by_iteration"][key] = float(
            np.mean([row["mean_intensity_continuity"] for row in subset])
        )
        summary["mean_phase_continuity_by_iteration"][key] = float(
            np.mean([row["mean_phase_continuity"] for row in subset])
        )
        summary["max_intensity_continuity_by_iteration"][key] = float(
            np.mean([row["max_intensity_continuity"] for row in subset])
        )
        summary["max_phase_continuity_by_iteration"][key] = float(
            np.mean([row["max_phase_continuity"] for row in subset])
        )
    return summary


def pipelined_assembly_time_ms(
    *,
    path_planning_ms: float,
    per_frame_generation_ms: float,
    slm_refresh_ms: float,
    frames: int,
    transfer_delay_ms: float,
) -> float:
    if frames <= 0:
        raise ValueError("frames must be positive")
    per_frame_bottleneck = max(float(per_frame_generation_ms), float(slm_refresh_ms))
    return float(path_planning_ms) + float(transfer_delay_ms) + frames * per_frame_bottleneck


def load_path_planner_module():
    module_path = Path(__file__).resolve().with_name("atom_path_planner.py")
    spec = importlib.util.spec_from_file_location("atom_path_planner", module_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
