from __future__ import annotations

from collections import deque
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing
from pathlib import Path
import time
from typing import Any, NamedTuple

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
import torch


ROOT = Path(__file__).resolve().parents[1]
EDGE_TYPE_NAMES = ("atom_to_target", "atom_to_atom", "target_to_target")
EDGE_ATOM_TO_TARGET = 0
EDGE_ATOM_TO_ATOM = 1
EDGE_TARGET_TO_TARGET = 2


class GraphSample(NamedTuple):
    atom_positions: np.ndarray
    target_positions: np.ndarray
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: np.ndarray
    edge_labels: np.ndarray
    edge_types: np.ndarray
    optimal_assignment: np.ndarray
    target_count: int
    edge_type_names: tuple[str, ...] = EDGE_TYPE_NAMES


class TrainingGraphBatch(NamedTuple):
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: np.ndarray
    edge_labels: np.ndarray
    edge_types: np.ndarray


def generate_path_planning_sample(
    *,
    initial_side: int,
    target_side: int,
    loading_probability: float,
    k_neighbors: int,
    seed: int,
    graph_backend: str = "auto",
    target_lattice_spacing: float | None = None,
) -> GraphSample:
    sample, _timings = generate_path_planning_sample_with_timing(
        initial_side=initial_side,
        target_side=target_side,
        loading_probability=loading_probability,
        k_neighbors=k_neighbors,
        seed=seed,
        graph_backend=graph_backend,
        target_lattice_spacing=target_lattice_spacing,
    )
    return sample


def generate_path_planning_sample_with_timing(
    *,
    initial_side: int,
    target_side: int,
    loading_probability: float,
    k_neighbors: int,
    seed: int,
    graph_backend: str = "auto",
    target_lattice_spacing: float | None = None,
) -> tuple[GraphSample, dict[str, float]]:
    started = time.monotonic()
    if initial_side < target_side:
        raise ValueError("initial_side must be at least target_side")
    if not 0.0 < loading_probability <= 1.0:
        raise ValueError("loading_probability must be in (0, 1]")
    lattice_started = time.monotonic()
    target_positions = centered_square_lattice(
        initial_side,
        target_side,
        target_lattice_spacing=target_lattice_spacing,
    )
    atom_started = time.monotonic()
    atom_positions = sample_loaded_atoms(initial_side, loading_probability, len(target_positions), seed)
    assignment_started = time.monotonic()
    optimal_assignment = hungarian_assignment(atom_positions, target_positions)
    graph_started = time.monotonic()
    builder = select_graph_builder(graph_backend, len(atom_positions), len(target_positions))
    sample = builder(
        atom_positions=atom_positions,
        target_positions=target_positions,
        optimal_assignment=optimal_assignment,
        k_neighbors=k_neighbors,
    )
    finished = time.monotonic()
    timings = {
        "lattice_seconds": atom_started - lattice_started,
        "atom_sampling_seconds": assignment_started - atom_started,
        "assignment_seconds": graph_started - assignment_started,
        "graph_seconds": finished - graph_started,
        "total_generate_seconds": finished - started,
    }
    return sample, timings


def generate_ground_truth_dataset_shard(
    *,
    output_dir: Path,
    shard_id: str,
    sample_count: int,
    initial_side: int,
    target_side: int,
    loading_probability: float,
    k_neighbors: int,
    seed_start: int,
    graph_backend: str = "auto",
    workers: int = 1,
    target_lattice_spacing: float | None = None,
) -> dict[str, object]:
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    worker_count = max(1, int(workers))
    output_dir = Path(output_dir)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    started = time.monotonic()
    samples: list[dict[str, object] | None] = [None] * sample_count
    timing_totals: dict[str, float] = {}
    reused_samples = 0
    expected_target_count = target_side * target_side
    expected_target_positions = centered_square_lattice(
        initial_side,
        target_side,
        target_lattice_spacing=target_lattice_spacing,
    )
    missing_jobs = []
    for sample_index in range(sample_count):
        seed = seed_start + sample_index
        sample_path = sample_dir / f"sample_{sample_index:08d}.npz"
        if sample_path.exists():
            sample = load_graph_sample_npz(sample_path)
            reused_samples += 1
            if sample.target_count != expected_target_count:
                raise ValueError(f"sample target_count mismatch: {sample_path}")
            if not np.allclose(sample.target_positions, expected_target_positions):
                raise ValueError(
                    f"sample target_positions mismatch for requested target_lattice_spacing: {sample_path}"
                )
            samples[sample_index] = dataset_sample_manifest_row(
                output_dir=output_dir,
                sample_path=sample_path,
                sample=sample,
                sample_index=sample_index,
                seed=seed,
            )
        else:
            missing_jobs.append(
                {
                    "output_dir": output_dir,
                    "sample_path": sample_path,
                    "sample_index": sample_index,
                    "seed": seed,
                    "initial_side": initial_side,
                    "target_side": target_side,
                    "loading_probability": loading_probability,
                    "k_neighbors": k_neighbors,
                    "graph_backend": graph_backend,
                    "expected_target_count": expected_target_count,
                    "target_lattice_spacing": target_lattice_spacing,
                }
            )

    if missing_jobs:
        if worker_count == 1:
            generated_results = [_generate_dataset_sample_from_job(job) for job in missing_jobs]
        else:
            context = multiprocessing.get_context("spawn")
            with ProcessPoolExecutor(max_workers=worker_count, mp_context=context) as executor:
                generated_results = list(executor.map(_generate_dataset_sample_from_job, missing_jobs))
        for sample_index, row, timings in generated_results:
            samples[int(sample_index)] = row
            for key, value in timings.items():
                timing_totals[key] = timing_totals.get(key, 0.0) + float(value)

    missing_rows = [index for index, row in enumerate(samples) if row is None]
    if missing_rows:
        raise ValueError(f"dataset sample rows missing after generation: {missing_rows[:5]}")
    if not missing_jobs and manifest_path.exists():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing_manifest_matches_request(
            existing_manifest,
            shard_id=shard_id,
            sample_count=sample_count,
            initial_side=initial_side,
            target_side=target_side,
            loading_probability=loading_probability,
            k_neighbors=k_neighbors,
            seed_start=seed_start,
            graph_backend=graph_backend,
            workers=worker_count,
            target_lattice_spacing=target_lattice_spacing,
        ):
            return existing_manifest

    generated_samples = len(missing_jobs)
    sample_rows = [row for row in samples if row is not None]

    manifest = {
        "artifact_type": "ground_truth_dataset_shard",
        "format": "npz_graph_sample_v1",
        "graph_backend": graph_backend,
        "generated_samples": generated_samples,
        "initial_side": initial_side,
        "k_neighbors": k_neighbors,
        "loading_probability": loading_probability,
        "manifest_path": manifest_path_value(manifest_path),
        "sample_count": sample_count,
        "samples": sample_rows,
        "seed_start": seed_start,
        "shard_id": shard_id,
        "status": "completed",
        "target_side": target_side,
        "target_lattice_spacing": target_lattice_spacing,
        "reused_samples": reused_samples,
        "timing_mean": (
            {key: value / generated_samples for key, value in sorted(timing_totals.items())}
            if generated_samples
            else {}
        ),
        "wall_time_seconds": time.monotonic() - started,
        "workers": worker_count,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def existing_manifest_matches_request(
    manifest: dict[str, object],
    *,
    shard_id: str,
    sample_count: int,
    initial_side: int,
    target_side: int,
    loading_probability: float,
    k_neighbors: int,
    seed_start: int,
    graph_backend: str,
    workers: int,
    target_lattice_spacing: float | None,
) -> bool:
    return (
        manifest.get("shard_id") == shard_id
        and int(manifest.get("sample_count", -1)) == sample_count
        and int(manifest.get("initial_side", -1)) == initial_side
        and int(manifest.get("target_side", -1)) == target_side
        and float(manifest.get("loading_probability", -1.0)) == float(loading_probability)
        and int(manifest.get("k_neighbors", -1)) == k_neighbors
        and int(manifest.get("seed_start", -1)) == seed_start
        and manifest.get("graph_backend") == graph_backend
        and int(manifest.get("workers", -1)) == workers
        and manifest.get("target_lattice_spacing") == target_lattice_spacing
        and len(manifest.get("samples", [])) == sample_count
    )


def manifest_path_value(manifest_path: Path) -> str:
    manifest_path = Path(manifest_path)
    try:
        return str(manifest_path.relative_to(ROOT))
    except ValueError:
        return str(manifest_path)


def dataset_sample_manifest_row(
    *,
    output_dir: Path,
    sample_path: Path,
    sample: GraphSample,
    sample_index: int,
    seed: int,
) -> dict[str, object]:
    checksum = sha256_file(sample_path)
    return {
        "edge_count": int(sample.edge_index.shape[1]),
        "path": str(sample_path.relative_to(output_dir)),
        "positive_edges": float(sample.edge_labels.sum()),
        "sample_index": sample_index,
        "seed": seed,
        "sha256": checksum,
    }


def _generate_dataset_sample_from_job(job: dict[str, Any]) -> tuple[int, dict[str, object], dict[str, float]]:
    sample_path = Path(job["sample_path"])
    output_dir = Path(job["output_dir"])
    sample_index = int(job["sample_index"])
    seed = int(job["seed"])
    sample, timings = generate_path_planning_sample_with_timing(
        initial_side=int(job["initial_side"]),
        target_side=int(job["target_side"]),
        loading_probability=float(job["loading_probability"]),
        k_neighbors=int(job["k_neighbors"]),
        seed=seed,
        graph_backend=str(job["graph_backend"]),
        target_lattice_spacing=job.get("target_lattice_spacing"),
    )
    if sample.target_count != int(job["expected_target_count"]):
        raise ValueError(f"sample target_count mismatch: {sample_path}")
    save_graph_sample_npz(sample, sample_path)
    row = dataset_sample_manifest_row(
        output_dir=output_dir,
        sample_path=sample_path,
        sample=sample,
        sample_index=sample_index,
        seed=seed,
    )
    return sample_index, row, timings


def save_graph_sample_npz(sample: GraphSample, sample_path: Path) -> None:
    sample_path = Path(sample_path)
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        sample_path,
        atom_positions=sample.atom_positions,
        target_positions=sample.target_positions,
        node_features=sample.node_features,
        edge_index=sample.edge_index,
        edge_features=sample.edge_features,
        edge_labels=sample.edge_labels,
        edge_types=sample.edge_types,
        optimal_assignment=sample.optimal_assignment,
        target_count=np.asarray([sample.target_count], dtype=np.int64),
    )


def load_graph_sample_npz(sample_path: Path) -> GraphSample:
    with np.load(Path(sample_path), allow_pickle=False) as data:
        return GraphSample(
            atom_positions=np.asarray(data["atom_positions"], dtype=np.float32),
            target_positions=np.asarray(data["target_positions"], dtype=np.float32),
            node_features=np.asarray(data["node_features"], dtype=np.float32),
            edge_index=np.asarray(data["edge_index"], dtype=np.int64),
            edge_features=np.asarray(data["edge_features"], dtype=np.float32),
            edge_labels=np.asarray(data["edge_labels"], dtype=np.float32),
            edge_types=np.asarray(data["edge_types"], dtype=np.int64),
            optimal_assignment=np.asarray(data["optimal_assignment"], dtype=np.int64),
            target_count=int(np.asarray(data["target_count"], dtype=np.int64)[0]),
        )


def load_ground_truth_dataset_manifest(manifest_path: Path) -> dict[str, object]:
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("artifact_type") != "ground_truth_dataset_shard":
        raise ValueError("manifest is not a ground_truth_dataset_shard")
    if manifest.get("status") != "completed":
        raise ValueError("dataset shard is not completed")
    return manifest


def dataset_sample_paths(manifest_path: Path) -> list[Path]:
    manifest = load_ground_truth_dataset_manifest(manifest_path)
    base_dir = Path(manifest_path).parent
    paths = []
    for row in manifest["samples"]:
        sample_path = Path(row["path"])
        if not sample_path.is_absolute():
            sample_path = base_dir / sample_path
        if sha256_file(sample_path) != row["sha256"]:
            raise ValueError(f"sample checksum mismatch: {sample_path}")
        paths.append(sample_path)
    return paths


def iter_dataset_manifest_samples(manifest_path: Path):
    for sample_path in dataset_sample_paths(manifest_path):
        yield load_graph_sample_npz(sample_path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def centered_square_lattice(
    initial_side: int,
    target_side: int,
    target_lattice_spacing: float | None = None,
) -> np.ndarray:
    spacing = 1.0 if target_lattice_spacing is None else float(target_lattice_spacing)
    extent = (target_side - 1) * spacing
    offset = ((initial_side - 1) - extent) / 2.0
    coords = []
    for row in range(target_side):
        for col in range(target_side):
            coords.append((offset + row * spacing, offset + col * spacing))
    return np.asarray(coords, dtype=np.float32)


def sample_loaded_atoms(
    initial_side: int,
    loading_probability: float,
    min_atoms: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    sites = np.asarray([(row, col) for row in range(initial_side) for col in range(initial_side)], dtype=np.float32)
    for _ in range(1000):
        mask = rng.random(len(sites)) < loading_probability
        if int(mask.sum()) >= min_atoms:
            return sites[mask]
    order = rng.permutation(len(sites))[:min_atoms]
    return sites[np.sort(order)]


def hungarian_assignment(atom_positions: np.ndarray, target_positions: np.ndarray) -> np.ndarray:
    cost = squared_distances(atom_positions, target_positions)
    atom_indices, target_indices = linear_sum_assignment(cost)
    order = np.argsort(target_indices)
    return np.column_stack([atom_indices[order], target_indices[order]]).astype(np.int64)


def squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    delta = left[:, None, :] - right[None, :, :]
    return np.sum(delta * delta, axis=2)


def build_candidate_graph(
    *,
    atom_positions: np.ndarray,
    target_positions: np.ndarray,
    optimal_assignment: np.ndarray,
    k_neighbors: int,
) -> GraphSample:
    n_atoms = int(len(atom_positions))
    n_targets = int(len(target_positions))
    if n_atoms < n_targets:
        raise ValueError("there must be at least as many atoms as targets")
    if k_neighbors <= 0:
        raise ValueError("k_neighbors must be positive")

    node_positions = np.vstack([atom_positions, target_positions])
    scale = float(max(np.max(node_positions), 1.0))
    atom_flags = np.concatenate([np.ones(n_atoms), np.zeros(n_targets)])
    target_flags = 1.0 - atom_flags
    node_features = np.column_stack([node_positions / scale, atom_flags, target_flags]).astype(np.float32)

    optimal_pairs = {(int(atom), int(target)) for atom, target in optimal_assignment}
    edges: dict[tuple[int, int, int], float] = {}

    atom_target_d2 = squared_distances(atom_positions, target_positions)
    for atom_idx in range(n_atoms):
        for target_idx in nearest_indices(atom_target_d2[atom_idx], min(k_neighbors, n_targets)):
            label = 1.0 if (atom_idx, int(target_idx)) in optimal_pairs else 0.0
            edges[(atom_idx, n_atoms + int(target_idx), EDGE_ATOM_TO_TARGET)] = label
    for atom_idx, target_idx in optimal_pairs:
        edges[(atom_idx, n_atoms + target_idx, EDGE_ATOM_TO_TARGET)] = 1.0

    atom_atom_d2 = squared_distances(atom_positions, atom_positions)
    for atom_idx in range(n_atoms):
        limit = min(k_neighbors, max(n_atoms - 1, 0))
        for other_idx in nearest_indices(atom_atom_d2[atom_idx], limit + 1):
            if int(other_idx) != atom_idx:
                edges[(atom_idx, int(other_idx), EDGE_ATOM_TO_ATOM)] = 0.0

    target_target_d2 = squared_distances(target_positions, target_positions)
    for target_idx in range(n_targets):
        limit = min(k_neighbors, max(n_targets - 1, 0))
        for other_idx in nearest_indices(target_target_d2[target_idx], limit + 1):
            if int(other_idx) != target_idx:
                edges[(n_atoms + target_idx, n_atoms + int(other_idx), EDGE_TARGET_TO_TARGET)] = 0.0

    edge_rows = []
    edge_features = []
    edge_labels = []
    edge_types = []
    for (src, dst, edge_type), label in sorted(edges.items()):
        src_pos = node_positions[src]
        dst_pos = node_positions[dst]
        delta = (dst_pos - src_pos) / scale
        dist2 = float(np.sum((dst_pos - src_pos) ** 2)) / (scale * scale)
        type_one_hot = [1.0 if edge_type == i else 0.0 for i in range(len(EDGE_TYPE_NAMES))]
        edge_rows.append((src, dst))
        edge_features.append([float(delta[0]), float(delta[1]), dist2, *type_one_hot])
        edge_labels.append(label)
        edge_types.append(edge_type)

    return GraphSample(
        atom_positions=np.asarray(atom_positions, dtype=np.float32),
        target_positions=np.asarray(target_positions, dtype=np.float32),
        node_features=node_features,
        edge_index=np.asarray(edge_rows, dtype=np.int64).T,
        edge_features=np.asarray(edge_features, dtype=np.float32),
        edge_labels=np.asarray(edge_labels, dtype=np.float32),
        edge_types=np.asarray(edge_types, dtype=np.int64),
        optimal_assignment=np.asarray(optimal_assignment, dtype=np.int64),
        target_count=n_targets,
    )


def build_candidate_graph_kdtree(
    *,
    atom_positions: np.ndarray,
    target_positions: np.ndarray,
    optimal_assignment: np.ndarray,
    k_neighbors: int,
) -> GraphSample:
    n_atoms = int(len(atom_positions))
    n_targets = int(len(target_positions))
    if n_atoms < n_targets:
        raise ValueError("there must be at least as many atoms as targets")
    if k_neighbors <= 0:
        raise ValueError("k_neighbors must be positive")

    node_positions = np.vstack([atom_positions, target_positions])
    scale = float(max(np.max(node_positions), 1.0))
    atom_flags = np.concatenate([np.ones(n_atoms), np.zeros(n_targets)])
    target_flags = 1.0 - atom_flags
    node_features = np.column_stack([node_positions / scale, atom_flags, target_flags]).astype(np.float32)

    optimal_pairs = {(int(atom), int(target)) for atom, target in optimal_assignment}
    edges: dict[tuple[int, int, int], float] = {}

    target_tree = cKDTree(target_positions)
    atom_target_neighbors = query_neighbor_indices(target_tree, atom_positions, min(k_neighbors, n_targets))
    for atom_idx, target_indices in enumerate(atom_target_neighbors):
        for target_idx in target_indices:
            label = 1.0 if (atom_idx, int(target_idx)) in optimal_pairs else 0.0
            edges[(atom_idx, n_atoms + int(target_idx), EDGE_ATOM_TO_TARGET)] = label
    for atom_idx, target_idx in optimal_pairs:
        edges[(int(atom_idx), n_atoms + int(target_idx), EDGE_ATOM_TO_TARGET)] = 1.0

    atom_limit = min(k_neighbors + 1, n_atoms)
    if atom_limit > 1:
        atom_tree = cKDTree(atom_positions)
        atom_neighbors = query_neighbor_indices(atom_tree, atom_positions, atom_limit)
        for atom_idx, other_indices in enumerate(atom_neighbors):
            for other_idx in other_indices:
                if int(other_idx) != atom_idx:
                    edges[(atom_idx, int(other_idx), EDGE_ATOM_TO_ATOM)] = 0.0

    target_limit = min(k_neighbors + 1, n_targets)
    if target_limit > 1:
        target_target_neighbors = query_neighbor_indices(target_tree, target_positions, target_limit)
        for target_idx, other_indices in enumerate(target_target_neighbors):
            for other_idx in other_indices:
                if int(other_idx) != target_idx:
                    edges[(n_atoms + target_idx, n_atoms + int(other_idx), EDGE_TARGET_TO_TARGET)] = 0.0

    return graph_sample_from_edges(
        atom_positions=atom_positions,
        target_positions=target_positions,
        node_positions=node_positions,
        node_features=node_features,
        optimal_assignment=optimal_assignment,
        edges=edges,
        scale=scale,
    )


def graph_sample_from_edges(
    *,
    atom_positions: np.ndarray,
    target_positions: np.ndarray,
    node_positions: np.ndarray,
    node_features: np.ndarray,
    optimal_assignment: np.ndarray,
    edges: dict[tuple[int, int, int], float],
    scale: float,
) -> GraphSample:
    n_atoms = int(len(atom_positions))
    n_targets = int(len(target_positions))
    edge_rows = []
    edge_features = []
    edge_labels = []
    edge_types = []
    for (src, dst, edge_type), label in sorted(edges.items()):
        src_pos = node_positions[src]
        dst_pos = node_positions[dst]
        delta = (dst_pos - src_pos) / scale
        dist2 = float(np.sum((dst_pos - src_pos) ** 2)) / (scale * scale)
        type_one_hot = [1.0 if edge_type == i else 0.0 for i in range(len(EDGE_TYPE_NAMES))]
        edge_rows.append((src, dst))
        edge_features.append([float(delta[0]), float(delta[1]), dist2, *type_one_hot])
        edge_labels.append(label)
        edge_types.append(edge_type)

    return GraphSample(
        atom_positions=np.asarray(atom_positions, dtype=np.float32),
        target_positions=np.asarray(target_positions, dtype=np.float32),
        node_features=node_features,
        edge_index=np.asarray(edge_rows, dtype=np.int64).T,
        edge_features=np.asarray(edge_features, dtype=np.float32),
        edge_labels=np.asarray(edge_labels, dtype=np.float32),
        edge_types=np.asarray(edge_types, dtype=np.int64),
        optimal_assignment=np.asarray(optimal_assignment, dtype=np.int64),
        target_count=n_targets,
    )


def query_neighbor_indices(tree: cKDTree, points: np.ndarray, count: int) -> np.ndarray:
    if count <= 0:
        return np.empty((len(points), 0), dtype=np.int64)
    _distances, indices = tree.query(points, k=count)
    indices = np.asarray(indices, dtype=np.int64)
    if indices.ndim == 1:
        indices = indices[:, None]
    return indices


def select_graph_builder(graph_backend: str, n_atoms: int, n_targets: int):
    if graph_backend == "dense":
        return build_candidate_graph
    if graph_backend == "kdtree":
        return build_candidate_graph_kdtree
    if graph_backend != "auto":
        raise ValueError("graph_backend must be dense, kdtree, or auto")
    if n_atoms * n_targets >= 2_000_000:
        return build_candidate_graph_kdtree
    return build_candidate_graph


def nearest_indices(distances: np.ndarray, count: int) -> np.ndarray:
    if count <= 0:
        return np.asarray([], dtype=np.int64)
    count = min(int(count), len(distances))
    return np.argsort(distances, kind="stable")[:count].astype(np.int64)


def decode_assignment_from_edge_scores(sample: GraphSample, edge_scores: np.ndarray) -> np.ndarray:
    score_matrix = atom_target_score_matrix(sample, edge_scores)
    atom_indices, target_indices = linear_sum_assignment(-score_matrix)
    order = np.argsort(target_indices)
    return np.column_stack([atom_indices[order], target_indices[order]]).astype(np.int64)


def decode_assignment_with_modified_auction(
    sample: GraphSample,
    edge_scores: np.ndarray,
    *,
    epsilon: float = 1e-6,
    max_rounds: int | None = None,
) -> np.ndarray:
    score_matrix = atom_target_score_matrix(sample, edge_scores)
    target_to_atom = auction_assignment_targets_to_atoms(score_matrix.T, epsilon=epsilon, max_rounds=max_rounds)
    target_indices = np.arange(len(target_to_atom), dtype=np.int64)
    return np.column_stack([target_to_atom, target_indices]).astype(np.int64)


def atom_target_score_matrix(sample: GraphSample, edge_scores: np.ndarray) -> np.ndarray:
    n_atoms = len(sample.atom_positions)
    n_targets = len(sample.target_positions)
    score_matrix = np.full((n_atoms, n_targets), -1e9, dtype=np.float64)
    edge_scores = np.asarray(edge_scores, dtype=np.float64)
    for edge_pos, (src, dst) in enumerate(sample.edge_index.T):
        if int(sample.edge_types[edge_pos]) != EDGE_ATOM_TO_TARGET:
            continue
        target_idx = int(dst) - n_atoms
        if 0 <= int(src) < n_atoms and 0 <= target_idx < n_targets:
            score_matrix[int(src), target_idx] = max(score_matrix[int(src), target_idx], edge_scores[edge_pos])
    return score_matrix


def auction_assignment_targets_to_atoms(
    target_atom_values: np.ndarray,
    *,
    epsilon: float = 1e-6,
    max_rounds: int | None = None,
) -> np.ndarray:
    values = np.asarray(target_atom_values, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError("target_atom_values must have shape (n_targets, n_atoms)")
    n_targets, n_atoms = values.shape
    if n_targets == 0:
        return np.empty(0, dtype=np.int64)
    if n_atoms < n_targets:
        raise ValueError("auction decoder requires at least as many atoms as targets")
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")

    prices = np.zeros(n_atoms, dtype=np.float64)
    target_assignment = np.full(n_targets, -1, dtype=np.int64)
    atom_owner = np.full(n_atoms, -1, dtype=np.int64)
    unassigned = deque(range(n_targets))
    round_limit = int(max_rounds) if max_rounds is not None else max(100, n_targets * n_atoms * 20)
    rounds = 0

    while unassigned:
        rounds += 1
        if rounds > round_limit:
            return auction_fallback_assignment(values)
        target_idx = int(unassigned.popleft())
        net_values = values[target_idx] - prices
        best_atom = int(np.argmax(net_values))
        best_value = float(net_values[best_atom])
        if n_atoms == 1:
            second_best_value = best_value - epsilon
        else:
            net_without_best = net_values.copy()
            net_without_best[best_atom] = -np.inf
            second_best_value = float(np.max(net_without_best))
        bid_increment = best_value - second_best_value + epsilon
        if not np.isfinite(bid_increment) or bid_increment <= 0.0:
            bid_increment = epsilon
        prices[best_atom] += bid_increment

        previous_owner = int(atom_owner[best_atom])
        atom_owner[best_atom] = target_idx
        target_assignment[target_idx] = best_atom
        if previous_owner >= 0:
            target_assignment[previous_owner] = -1
            unassigned.append(previous_owner)

    return target_assignment.astype(np.int64)


def auction_fallback_assignment(target_atom_values: np.ndarray) -> np.ndarray:
    target_indices, atom_indices = linear_sum_assignment(-np.asarray(target_atom_values, dtype=np.float64))
    order = np.argsort(target_indices)
    return atom_indices[order].astype(np.int64)


def oracle_decoder_audit(sample: GraphSample) -> dict[str, object]:
    oracle_scores = sample.edge_labels.astype(np.float64)
    score_hungarian = decode_assignment_from_edge_scores(sample, oracle_scores)
    modified_auction = decode_assignment_with_modified_auction(sample, oracle_scores)
    return {
        "status": "completed",
        "target_count": int(sample.target_count),
        "atom_count": int(len(sample.atom_positions)),
        "decoders": {
            "score_hungarian": assignment_metrics(sample, score_hungarian),
            "modified_auction": assignment_metrics(sample, modified_auction),
        },
    }


def assignment_metrics(sample: GraphSample, assignment: np.ndarray) -> dict[str, float]:
    predicted_distances = assignment_distances(sample.atom_positions, sample.target_positions, assignment)
    optimal_distances = assignment_distances(sample.atom_positions, sample.target_positions, sample.optimal_assignment)
    return {
        "predicted_average_distance": float(np.mean(predicted_distances)),
        "optimal_average_distance": float(np.mean(optimal_distances)),
        "average_distance_gap": float(np.mean(predicted_distances) - np.mean(optimal_distances)),
        "predicted_max_distance": float(np.max(predicted_distances)),
        "optimal_max_distance": float(np.max(optimal_distances)),
        "max_distance_gap": float(np.max(predicted_distances) - np.max(optimal_distances)),
    }


def assignment_distances(atom_positions: np.ndarray, target_positions: np.ndarray, assignment: np.ndarray) -> np.ndarray:
    atom_idx = assignment[:, 0].astype(np.int64)
    target_idx = assignment[:, 1].astype(np.int64)
    delta = atom_positions[atom_idx] - target_positions[target_idx]
    return np.sqrt(np.sum(delta * delta, axis=1))


def run_reduced_training_pilot(
    *,
    output_dir: Path,
    train_samples: int,
    eval_samples: int,
    initial_side: int,
    target_side: int,
    k_neighbors: int,
    epochs: int,
    hidden_dim: int,
    seed: int,
    message_passes: int = 2,
    device: str = "cpu",
) -> dict[str, object]:
    metrics = run_model_training_reproduction(
        output_dir=output_dir,
        train_samples=train_samples,
        eval_samples=eval_samples,
        initial_side=initial_side,
        target_side=target_side,
        k_neighbors=k_neighbors,
        epochs=epochs,
        hidden_dim=hidden_dim,
        message_passes=message_passes,
        seed=seed,
        device=device,
        target="retrained_gnn_path_planner",
    )
    return metrics


def run_model_training_reproduction(
    *,
    output_dir: Path,
    train_samples: int,
    eval_samples: int,
    initial_side: int,
    target_side: int,
    k_neighbors: int,
    epochs: int,
    hidden_dim: int,
    message_passes: int,
    seed: int,
    model_arch: str = "plain",
    score_head: str = "shallow",
    device: str = "cpu",
    learning_rate: float = 0.01,
    loading_probability: float = 0.75,
    target: str = "retrained_gnn_path_planner",
    graph_backend: str = "auto",
    target_lattice_spacing: float | None = None,
    stream_samples: bool = False,
    checkpoint_every_updates: int = 0,
    max_updates: int | None = None,
    history_stride: int = 1,
    prefetch_workers: int = 0,
    prefetch_buffer: int = 0,
    progress_every_updates: int = 0,
    batch_size: int = 1,
    dataset_manifest_path: Path | None = None,
    eval_dataset_manifest_path: Path | None = None,
    resume_checkpoint_path: Path | None = None,
    resume_optimizer_state: bool = True,
    loss_mode: str = "bce",
    source_ce_weight: float = 0.1,
    margin: float = 1.0,
    temperature: float = 0.25,
    hard_negative_k: int = 3,
    sinkhorn_iterations: int = 30,
    max_grad_norm: float | None = None,
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    torch_device = resolve_torch_device(device)
    torch.manual_seed(seed)
    model = EdgeScoringGNN(
        node_dim=4,
        edge_dim=6,
        hidden_dim=hidden_dim,
        message_passes=message_passes,
        model_arch=model_arch,
        score_head=score_head,
    )
    if resume_checkpoint_path is not None:
        checkpoint = load_torch_checkpoint(Path(resume_checkpoint_path), torch_device)
        model.load_state_dict(checkpoint["state_dict"])
    model.to(torch_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    if resume_checkpoint_path is not None and resume_optimizer_state and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    loss_initial: float | None = None
    loss_final: float | None = None
    loss_records: list[dict[str, float | int]] = []

    model_config = {
        "class": "EdgeScoringGNN",
        "node_dim": 4,
        "edge_dim": 6,
        "hidden_dim": hidden_dim,
        "message_passes": message_passes,
        "model_arch": model_arch,
        "score_head": score_head,
    }
    config = {
        "train_samples": train_samples,
        "eval_samples": eval_samples,
        "initial_side": initial_side,
        "target_side": target_side,
        "loading_probability": loading_probability,
        "k_neighbors": k_neighbors,
        "epochs": epochs,
        "hidden_dim": hidden_dim,
        "message_passes": message_passes,
        "model_arch": model_arch,
        "score_head": score_head,
        "learning_rate": learning_rate,
        "seed": seed,
        "device": str(torch_device),
        "graph_backend": graph_backend,
        "target_lattice_spacing": target_lattice_spacing,
        "stream_samples": stream_samples,
        "checkpoint_every_updates": checkpoint_every_updates,
        "max_updates": max_updates,
        "history_stride": history_stride,
        "prefetch_workers": prefetch_workers,
        "prefetch_buffer": prefetch_buffer,
        "progress_every_updates": progress_every_updates,
        "batch_size": batch_size,
        "dataset_manifest_path": str(dataset_manifest_path) if dataset_manifest_path else None,
        "eval_dataset_manifest_path": str(eval_dataset_manifest_path) if eval_dataset_manifest_path else None,
        "resume_checkpoint_path": str(resume_checkpoint_path) if resume_checkpoint_path else None,
        "resume_optimizer_state": bool(resume_optimizer_state),
        "loss_mode": loss_mode,
        "source_ce_weight": source_ce_weight,
        "margin": margin,
        "temperature": temperature,
        "hard_negative_k": hard_negative_k,
        "sinkhorn_iterations": sinkhorn_iterations,
        "max_grad_norm": max_grad_norm,
    }
    checkpoint_dir = output_dir / "checkpoints"
    if checkpoint_every_updates > 0:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "training_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")

    train_set = None
    dataset_paths = None
    if dataset_manifest_path is not None:
        dataset_paths = dataset_sample_paths(dataset_manifest_path)
        if not dataset_paths:
            raise ValueError("dataset manifest does not contain samples")
    elif not stream_samples:
        train_set = [
            generate_path_planning_sample(
                initial_side=initial_side,
                target_side=target_side,
                loading_probability=loading_probability,
                k_neighbors=k_neighbors,
                seed=seed + idx,
                graph_backend=graph_backend,
                target_lattice_spacing=target_lattice_spacing,
            )
            for idx in range(train_samples)
        ]

    updates = 0
    optimizer_steps = 0
    target_updates = train_samples * epochs
    if max_updates is not None:
        target_updates = min(target_updates, int(max_updates))
    started = time.monotonic()

    def write_progress(
        event: str,
        update: int,
        loss: float | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        if progress_every_updates <= 0 and event == "update":
            return
        elapsed = max(time.monotonic() - started, 1e-9)
        payload = {
            "event": event,
            "update": update,
            "target_updates": target_updates,
            "loss": loss,
            "elapsed_seconds": elapsed,
            "updates_per_second": update / elapsed if update else None,
        }
        if extra:
            payload.update(extra)
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    write_progress("started", 0, None)
    stream_iter = None
    if stream_samples and dataset_paths is None:
        stream_iter = iter_streamed_training_samples(
            total_updates=target_updates,
            initial_side=initial_side,
            target_side=target_side,
            loading_probability=loading_probability,
            k_neighbors=k_neighbors,
            seed=seed,
            graph_backend=graph_backend,
            target_lattice_spacing=target_lattice_spacing,
            prefetch_workers=prefetch_workers,
            prefetch_buffer=prefetch_buffer,
        )
    next_history_update = 1
    last_checkpoint_update = 0
    batch_size = max(1, int(batch_size))
    next_progress_update = 1
    while updates < target_updates:
        current_batch_size = min(batch_size, target_updates - updates)
        batch_samples = []
        batch_generate_started = time.monotonic()
        for _ in range(current_batch_size):
            update_index = updates + len(batch_samples)
            if dataset_paths is not None:
                sample = load_graph_sample_npz(dataset_paths[update_index % len(dataset_paths)])
            elif stream_samples:
                assert stream_iter is not None
                sample = next(stream_iter)
            else:
                assert train_set is not None
                sample = train_set[update_index % train_samples]
            batch_samples.append(sample)
        batch_generate_seconds = time.monotonic() - batch_generate_started
        if len(batch_samples) == 1:
            training_input = batch_samples[0]
        else:
            training_input = batch_training_samples(batch_samples)
        train_started = time.monotonic()
        loss_value = train_one_batch(
            model,
            training_input,
            optimizer,
            torch_device,
            loss_mode=loss_mode,
            source_ce_weight=source_ce_weight,
            margin=margin,
            temperature=temperature,
            hard_negative_k=hard_negative_k,
            sinkhorn_iterations=sinkhorn_iterations,
            max_grad_norm=max_grad_norm,
        )
        train_seconds = time.monotonic() - train_started
        optimizer_steps += 1
        actual_batch_size = len(batch_samples)
        updates += actual_batch_size
        if stream_samples:
            del batch_samples
        if loss_initial is None:
            loss_initial = loss_value
        loss_final = loss_value
        if history_stride <= 1 or updates >= next_history_update or updates == target_updates:
            loss_records.append({"update": updates, "loss": loss_value})
            if history_stride > 1:
                while next_history_update <= updates:
                    next_history_update = history_stride if next_history_update == 1 else next_history_update + history_stride
        if progress_every_updates > 0 and (updates >= next_progress_update or updates == target_updates):
            write_progress(
                "update",
                updates,
                loss_value,
                {
                    "batch_generate_seconds": batch_generate_seconds,
                    "batch_size": actual_batch_size,
                    "optimizer_steps": optimizer_steps,
                    "train_seconds": train_seconds,
                },
            )
            while next_progress_update <= updates:
                next_progress_update = (
                    max(2, progress_every_updates)
                    if next_progress_update == 1
                    else next_progress_update + progress_every_updates
                )
        if checkpoint_every_updates > 0 and updates - last_checkpoint_update >= checkpoint_every_updates:
            save_edge_scoring_checkpoint(
                model=model,
                optimizer=optimizer,
                checkpoint_path=checkpoint_dir / f"update_{updates:08d}.pt",
                model_config=model_config,
                config=config,
                training_state={"updates": updates, "optimizer_steps": optimizer_steps, "last_loss": loss_value},
            )
            last_checkpoint_update = updates

    eval_rows = []
    model.eval()
    if eval_dataset_manifest_path is not None:
        eval_paths = dataset_sample_paths(eval_dataset_manifest_path)
        if not eval_paths:
            raise ValueError("eval dataset manifest does not contain samples")
        eval_iter = (load_graph_sample_npz(eval_paths[idx % len(eval_paths)]) for idx in range(eval_samples))
    else:
        eval_iter = iter_eval_samples(
            eval_samples=eval_samples,
            initial_side=initial_side,
            target_side=target_side,
            loading_probability=loading_probability,
            k_neighbors=k_neighbors,
            seed=seed + 1000,
            graph_backend=graph_backend,
            target_lattice_spacing=target_lattice_spacing,
            stream_samples=stream_samples,
            prefetch_workers=prefetch_workers,
            prefetch_buffer=prefetch_buffer,
        )
    with torch.no_grad():
        for idx, sample in enumerate(eval_iter):
            eval_started = time.monotonic()
            scores = predict_edge_scores(model, sample)
            decoded = decode_assignment_from_edge_scores(sample, scores)
            eval_rows.append(assignment_metrics(sample, decoded))
            write_progress(
                "eval",
                updates,
                loss_final,
                {
                    "eval_index": idx + 1,
                    "eval_samples": eval_samples,
                    "eval_seconds": time.monotonic() - eval_started,
                },
            )

    summary = summarize_eval_rows(eval_rows)
    write_progress("completed", updates, loss_final)
    checkpoint_path = output_dir / "model_state.pt"
    history_path = output_dir / "training_history.json"
    save_edge_scoring_checkpoint(
        model=model,
        optimizer=optimizer,
        checkpoint_path=checkpoint_path,
        model_config=model_config,
        config=config,
        training_state={"updates": updates, "optimizer_steps": optimizer_steps, "last_loss": loss_final},
    )
    history = {
        "losses": loss_records,
        "loss_initial": loss_initial,
        "loss_final": loss_final,
        "updates": updates,
        "optimizer_steps": optimizer_steps,
        "recorded_losses": len(loss_records),
    }
    history_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics: dict[str, object] = {
        "status": "completed",
        "paper_id": "2604.08669",
        "target": target,
        "model": model_config,
        "config": config,
        "training": {
            "loss_initial": loss_initial,
            "loss_final": loss_final,
            "updates": updates,
            "optimizer_steps": optimizer_steps,
            "recorded_losses": len(loss_records),
        },
        "summary": summary,
        "eval_rows": eval_rows,
        "artifacts": {
            "checkpoint_path": str(checkpoint_path),
            "training_history_path": str(history_path),
            "progress_path": str(progress_path),
        },
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def iter_streamed_training_samples(
    *,
    total_updates: int,
    initial_side: int,
    target_side: int,
    loading_probability: float,
    k_neighbors: int,
    seed: int,
    graph_backend: str,
    target_lattice_spacing: float | None,
    prefetch_workers: int,
    prefetch_buffer: int,
):
    if prefetch_workers <= 0:
        for update_index in range(total_updates):
            yield generate_path_planning_sample(
                initial_side=initial_side,
                target_side=target_side,
                loading_probability=loading_probability,
                k_neighbors=k_neighbors,
                seed=seed + update_index,
                graph_backend=graph_backend,
                target_lattice_spacing=target_lattice_spacing,
            )
        return

    worker_count = int(prefetch_workers)
    max_pending = max(worker_count, int(prefetch_buffer) if prefetch_buffer > 0 else worker_count * 2)
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=worker_count, mp_context=context) as executor:
        pending = deque()
        next_update = 0

        def submit_one() -> None:
            nonlocal next_update
            if next_update >= total_updates:
                return
            job = {
                "initial_side": initial_side,
                "target_side": target_side,
                "loading_probability": loading_probability,
                "k_neighbors": k_neighbors,
                "seed": seed + next_update,
                "graph_backend": graph_backend,
                "target_lattice_spacing": target_lattice_spacing,
            }
            pending.append(executor.submit(_generate_training_sample_from_job, job))
            next_update += 1

        for _ in range(min(max_pending, total_updates)):
            submit_one()
        while pending:
            future = pending.popleft()
            yield future.result()
            submit_one()


def iter_eval_samples(
    *,
    eval_samples: int,
    initial_side: int,
    target_side: int,
    loading_probability: float,
    k_neighbors: int,
    seed: int,
    graph_backend: str,
    target_lattice_spacing: float | None,
    stream_samples: bool,
    prefetch_workers: int,
    prefetch_buffer: int,
):
    if eval_samples <= 0:
        return
    if stream_samples and prefetch_workers > 0:
        yield from iter_streamed_training_samples(
            total_updates=eval_samples,
            initial_side=initial_side,
            target_side=target_side,
            loading_probability=loading_probability,
            k_neighbors=k_neighbors,
            seed=seed,
            graph_backend=graph_backend,
            target_lattice_spacing=target_lattice_spacing,
            prefetch_workers=prefetch_workers,
            prefetch_buffer=prefetch_buffer,
        )
        return
    for idx in range(eval_samples):
        yield generate_path_planning_sample(
            initial_side=initial_side,
            target_side=target_side,
            loading_probability=loading_probability,
            k_neighbors=k_neighbors,
            seed=seed + idx,
            graph_backend=graph_backend,
            target_lattice_spacing=target_lattice_spacing,
        )


def _generate_training_sample_from_job(job: dict[str, Any]) -> GraphSample:
    return generate_path_planning_sample(
        initial_side=int(job["initial_side"]),
        target_side=int(job["target_side"]),
        loading_probability=float(job["loading_probability"]),
        k_neighbors=int(job["k_neighbors"]),
        seed=int(job["seed"]),
        graph_backend=str(job["graph_backend"]),
        target_lattice_spacing=job.get("target_lattice_spacing"),
    )


def train_one_sample(
    model: "EdgeScoringGNN",
    sample: GraphSample,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    return train_one_batch(model, sample, optimizer, device)


def batch_training_samples(samples: list[GraphSample]) -> TrainingGraphBatch:
    if not samples:
        raise ValueError("samples must not be empty")
    node_features = []
    edge_features = []
    edge_labels = []
    edge_types = []
    edge_indices = []
    node_offset = 0
    for sample in samples:
        node_features.append(sample.node_features)
        edge_features.append(sample.edge_features)
        edge_labels.append(sample.edge_labels)
        edge_types.append(sample.edge_types)
        edge_indices.append(sample.edge_index + node_offset)
        node_offset += sample.node_features.shape[0]
    return TrainingGraphBatch(
        node_features=np.concatenate(node_features, axis=0).astype(np.float32),
        edge_index=np.concatenate(edge_indices, axis=1).astype(np.int64),
        edge_features=np.concatenate(edge_features, axis=0).astype(np.float32),
        edge_labels=np.concatenate(edge_labels, axis=0).astype(np.float32),
        edge_types=np.concatenate(edge_types, axis=0).astype(np.int64),
    )


def train_one_batch(
    model: "EdgeScoringGNN",
    sample: GraphSample | TrainingGraphBatch,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    *,
    loss_mode: str = "bce",
    source_ce_weight: float = 0.1,
    margin: float = 1.0,
    temperature: float = 0.25,
    hard_negative_k: int = 3,
    sinkhorn_iterations: int = 30,
    max_grad_norm: float | None = None,
) -> float:
    optimizer.zero_grad()
    logits = model(sample)
    mask = torch.as_tensor(sample.edge_types == EDGE_ATOM_TO_TARGET, device=device)
    labels = torch.as_tensor(sample.edge_labels, dtype=torch.float32, device=device)
    if loss_mode == "bce":
        loss = binary_atom_target_cross_entropy(logits=logits, labels=labels, mask=mask, device=device)
    elif loss_mode == "target_ce":
        loss = target_assignment_cross_entropy(logits=logits, labels=labels, sample=sample, mask=mask, device=device)
    elif loss_mode == "target_temperature_ce":
        loss = target_temperature_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            temperature=float(temperature),
        )
    elif loss_mode == "source_ce":
        loss = source_assignment_cross_entropy(logits=logits, labels=labels, sample=sample, mask=mask, device=device)
    elif loss_mode == "source_temperature_ce":
        loss = source_temperature_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            temperature=float(temperature),
        )
    elif loss_mode == "source_target_temperature_ce":
        source_loss = source_temperature_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            temperature=float(temperature),
        )
        target_loss = target_temperature_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            temperature=float(temperature),
        )
        loss = source_loss + target_loss
    elif loss_mode == "source_topk_hard_negative_ce":
        loss = source_topk_hard_negative_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            hard_negative_k=int(hard_negative_k),
            temperature=float(temperature),
        )
    elif loss_mode == "target_topk_hard_negative_ce":
        loss = target_topk_hard_negative_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            hard_negative_k=int(hard_negative_k),
            temperature=float(temperature),
        )
    elif loss_mode == "source_target_topk_hard_negative_ce":
        source_loss = source_topk_hard_negative_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            hard_negative_k=int(hard_negative_k),
            temperature=float(temperature),
        )
        target_loss = target_topk_hard_negative_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            hard_negative_k=int(hard_negative_k),
            temperature=float(temperature),
        )
        loss = source_loss + target_loss
    elif loss_mode == "assignment_sinkhorn_ce":
        loss = assignment_sinkhorn_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            temperature=float(temperature),
            iterations=int(sinkhorn_iterations),
        )
    elif loss_mode == "assignment_log_sinkhorn_ce":
        loss = assignment_log_sinkhorn_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            temperature=float(temperature),
            iterations=int(sinkhorn_iterations),
        )
    elif loss_mode == "source_target_ce":
        source_loss = source_assignment_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
        )
        target_loss = target_assignment_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
        )
        loss = source_loss + target_loss
    elif loss_mode == "bce_source_ce":
        bce_loss = binary_atom_target_cross_entropy(logits=logits, labels=labels, mask=mask, device=device)
        source_loss = source_assignment_cross_entropy(logits=logits, labels=labels, sample=sample, mask=mask, device=device)
        loss = bce_loss + float(source_ce_weight) * source_loss
    elif loss_mode == "source_margin":
        loss = source_hard_negative_margin_loss(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            margin=float(margin),
        )
    elif loss_mode == "source_ce_margin":
        source_loss = source_assignment_cross_entropy(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
        )
        margin_loss = source_hard_negative_margin_loss(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            margin=float(margin),
        )
        loss = source_loss + margin_loss
    elif loss_mode == "target_margin":
        loss = target_hard_negative_margin_loss(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            margin=float(margin),
        )
    elif loss_mode == "source_target_margin":
        source_margin_loss = source_hard_negative_margin_loss(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            margin=float(margin),
        )
        target_margin_loss = target_hard_negative_margin_loss(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            margin=float(margin),
        )
        loss = source_margin_loss + target_margin_loss
    elif loss_mode == "assignment_margin":
        loss = assignment_structured_margin_loss(
            logits=logits,
            labels=labels,
            sample=sample,
            mask=mask,
            device=device,
            margin=float(margin),
        )
    else:
        raise ValueError(f"unsupported loss_mode: {loss_mode}")
    if not bool(torch.isfinite(loss.detach()).item()):
        raise ValueError(f"{loss_mode} produced a non-finite loss")
    loss.backward()
    if max_grad_norm is not None:
        grad_clip = float(max_grad_norm)
        if grad_clip <= 0.0:
            raise ValueError("max_grad_norm must be positive when provided")
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        if not bool(torch.isfinite(torch.as_tensor(grad_norm, device=device)).item()):
            raise ValueError(f"{loss_mode} produced non-finite gradients")
    optimizer.step()
    return float(loss.detach().item())


def binary_atom_target_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    mask: torch.Tensor,
    device: torch.device,
) -> torch.Tensor:
    pos = float(labels[mask].sum().item())
    neg = float(mask.sum().item() - pos)
    pos_weight = torch.tensor([max(1.0, neg / max(pos, 1.0))], dtype=torch.float32, device=device)
    return torch.nn.functional.binary_cross_entropy_with_logits(
        logits[mask],
        labels[mask],
        pos_weight=pos_weight,
    )


def target_assignment_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
) -> torch.Tensor:
    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    target_nodes = edge_index[1, mask]
    target_logits = logits[mask]
    target_labels = labels[mask]
    if target_logits.numel() == 0:
        raise ValueError("target_ce requires atom-to-target edges")

    _unique_targets, inverse = torch.unique(target_nodes, sorted=True, return_inverse=True)
    group_count = int(inverse.max().item()) + 1
    group_has_positive = torch.zeros(group_count, dtype=torch.float32, device=device)
    group_has_positive.index_add_(0, inverse, target_labels)
    positive_groups = group_has_positive > 0.5
    if not bool(positive_groups.any().item()):
        raise ValueError("target_ce requires at least one positive atom-to-target edge")

    group_max = torch.full((group_count,), -torch.inf, dtype=target_logits.dtype, device=device)
    if hasattr(group_max, "scatter_reduce_"):
        group_max.scatter_reduce_(0, inverse, target_logits, reduce="amax", include_self=True)
    else:
        for group_index in range(group_count):
            group_max[group_index] = target_logits[inverse == group_index].max()
    stabilized = torch.exp(target_logits - group_max[inverse])
    group_sum_exp = torch.zeros(group_count, dtype=target_logits.dtype, device=device)
    group_sum_exp.index_add_(0, inverse, stabilized)
    group_logsumexp = torch.log(group_sum_exp.clamp_min(torch.finfo(target_logits.dtype).tiny)) + group_max

    positive_logits = torch.zeros(group_count, dtype=target_logits.dtype, device=device)
    positive_logits.index_add_(0, inverse, target_logits * target_labels)
    return (group_logsumexp[positive_groups] - positive_logits[positive_groups]).mean()


def source_assignment_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
) -> torch.Tensor:
    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    source_nodes = edge_index[0, mask]
    source_logits = logits[mask]
    source_labels = labels[mask]
    if source_logits.numel() == 0:
        raise ValueError("source_ce requires atom-to-target edges")

    _unique_sources, inverse = torch.unique(source_nodes, sorted=True, return_inverse=True)
    group_count = int(inverse.max().item()) + 1
    group_has_positive = torch.zeros(group_count, dtype=torch.float32, device=device)
    group_has_positive.index_add_(0, inverse, source_labels)
    positive_groups = group_has_positive > 0.5
    if not bool(positive_groups.any().item()):
        raise ValueError("source_ce requires at least one positive atom-to-target edge")

    group_max = torch.full((group_count,), -torch.inf, dtype=source_logits.dtype, device=device)
    if hasattr(group_max, "scatter_reduce_"):
        group_max.scatter_reduce_(0, inverse, source_logits, reduce="amax", include_self=True)
    else:
        for group_index in range(group_count):
            group_max[group_index] = source_logits[inverse == group_index].max()
    stabilized = torch.exp(source_logits - group_max[inverse])
    group_sum_exp = torch.zeros(group_count, dtype=source_logits.dtype, device=device)
    group_sum_exp.index_add_(0, inverse, stabilized)
    group_logsumexp = torch.log(group_sum_exp.clamp_min(torch.finfo(source_logits.dtype).tiny)) + group_max

    positive_logits = torch.zeros(group_count, dtype=source_logits.dtype, device=device)
    positive_logits.index_add_(0, inverse, source_logits * source_labels)
    return (group_logsumexp[positive_groups] - positive_logits[positive_groups]).mean()


def source_temperature_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    temperature: float = 0.25,
) -> torch.Tensor:
    if float(temperature) <= 0.0:
        raise ValueError("source_temperature_ce requires temperature > 0")
    scaled_logits = logits / torch.as_tensor(float(temperature), dtype=logits.dtype, device=device)
    return source_assignment_cross_entropy(
        logits=scaled_logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
    )


def target_temperature_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    temperature: float = 0.25,
) -> torch.Tensor:
    if float(temperature) <= 0.0:
        raise ValueError("target_temperature_ce requires temperature > 0")
    scaled_logits = logits / torch.as_tensor(float(temperature), dtype=logits.dtype, device=device)
    return target_assignment_cross_entropy(
        logits=scaled_logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
    )


def source_topk_hard_negative_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    hard_negative_k: int = 3,
    temperature: float = 1.0,
) -> torch.Tensor:
    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    source_nodes = edge_index[0, mask]
    return _topk_hard_negative_cross_entropy(
        group_nodes=source_nodes,
        logits=logits[mask],
        labels=labels[mask],
        device=device,
        hard_negative_k=hard_negative_k,
        temperature=temperature,
        error_prefix="source_topk_hard_negative_ce",
    )


def target_topk_hard_negative_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    hard_negative_k: int = 3,
    temperature: float = 1.0,
) -> torch.Tensor:
    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    target_nodes = edge_index[1, mask]
    return _topk_hard_negative_cross_entropy(
        group_nodes=target_nodes,
        logits=logits[mask],
        labels=labels[mask],
        device=device,
        hard_negative_k=hard_negative_k,
        temperature=temperature,
        error_prefix="target_topk_hard_negative_ce",
    )


def _topk_hard_negative_cross_entropy(
    *,
    group_nodes: torch.Tensor,
    logits: torch.Tensor,
    labels: torch.Tensor,
    device: torch.device,
    hard_negative_k: int,
    temperature: float,
    error_prefix: str,
) -> torch.Tensor:
    if logits.numel() == 0:
        raise ValueError(f"{error_prefix} requires atom-to-target edges")
    if int(hard_negative_k) <= 0:
        raise ValueError(f"{error_prefix} requires hard_negative_k > 0")
    if float(temperature) <= 0.0:
        raise ValueError(f"{error_prefix} requires temperature > 0")

    order = torch.argsort(group_nodes)
    sorted_group_nodes = group_nodes[order]
    sorted_logits = logits[order]
    sorted_labels = labels[order]
    _unique_groups, group_counts = torch.unique_consecutive(sorted_group_nodes, return_counts=True)

    losses: list[torch.Tensor] = []
    target_index = torch.zeros(1, dtype=torch.long, device=device)
    temperature_tensor = torch.as_tensor(float(temperature), dtype=logits.dtype, device=device)
    start = 0
    for group_count in group_counts.tolist():
        end = start + int(group_count)
        group_logits = sorted_logits[start:end]
        group_labels = sorted_labels[start:end]
        start = end
        positive_logits = group_logits[group_labels > 0.5]
        negative_logits = group_logits[group_labels <= 0.5]
        if positive_logits.numel() == 0 or negative_logits.numel() == 0:
            continue
        positive_logit = positive_logits.max().view(1)
        k = min(int(hard_negative_k), int(negative_logits.numel()))
        hard_negative_logits = torch.topk(negative_logits, k=k).values
        candidates = torch.cat([positive_logit, hard_negative_logits]) / temperature_tensor
        losses.append(torch.nn.functional.cross_entropy(candidates.view(1, -1), target_index))
    if not losses:
        raise ValueError(f"{error_prefix} requires at least one group with positive and negative atom-to-target edges")
    return torch.stack(losses).mean()


def target_balanced_sinkhorn_assignment_matrix(
    *,
    logits: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    device: torch.device,
    temperature: float = 0.25,
    iterations: int = 30,
) -> torch.Tensor:
    if float(temperature) <= 0.0:
        raise ValueError("assignment_sinkhorn_ce requires temperature > 0")
    if int(iterations) <= 0:
        raise ValueError("assignment_sinkhorn_ce requires iterations > 0")
    n_atoms = int(len(sample.atom_positions))
    n_targets = int(len(sample.target_positions))
    if n_targets == 0:
        raise ValueError("assignment_sinkhorn_ce requires at least one target")

    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    edge_types = torch.as_tensor(sample.edge_types, dtype=torch.long, device=device)
    atom_target = edge_types == EDGE_ATOM_TO_TARGET
    atom_indices = edge_index[0, atom_target]
    target_indices = edge_index[1, atom_target] - int(n_atoms)
    valid = (atom_indices >= 0) & (atom_indices < n_atoms) & (target_indices >= 0) & (target_indices < n_targets)
    atom_indices = atom_indices[valid]
    target_indices = target_indices[valid]
    edge_logits = logits[atom_target][valid]
    if edge_logits.numel() == 0:
        raise ValueError("assignment_sinkhorn_ce requires atom-to-target edges")

    score_matrix = torch.full((n_atoms, n_targets), -torch.inf, dtype=logits.dtype, device=device)
    if hasattr(score_matrix, "index_put_"):
        score_matrix.index_put_((atom_indices, target_indices), edge_logits, accumulate=False)
    else:
        for atom_idx, target_idx, value in zip(atom_indices.tolist(), target_indices.tolist(), edge_logits):
            score_matrix[int(atom_idx), int(target_idx)] = value

    scaled = score_matrix / torch.as_tensor(float(temperature), dtype=logits.dtype, device=device)
    finite = torch.isfinite(scaled)
    if not bool(finite.any().item()):
        raise ValueError("assignment_sinkhorn_ce requires finite candidate logits")
    stabilized = torch.where(finite, scaled - torch.max(scaled[finite]), torch.as_tensor(-torch.inf, dtype=logits.dtype, device=device))
    matrix = torch.where(finite, torch.exp(stabilized), torch.zeros_like(stabilized))
    tiny = torch.as_tensor(torch.finfo(logits.dtype).tiny, dtype=logits.dtype, device=device)
    for _ in range(int(iterations)):
        row_sums = matrix.sum(dim=1, keepdim=True)
        row_scale = torch.minimum(torch.ones_like(row_sums), torch.reciprocal(row_sums.clamp_min(tiny)))
        matrix = matrix * row_scale
        column_sums = matrix.sum(dim=0, keepdim=True)
        matrix = matrix / column_sums.clamp_min(tiny)
    return matrix


def assignment_sinkhorn_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    temperature: float = 0.25,
    iterations: int = 30,
) -> torch.Tensor:
    del labels, mask
    matrix = target_balanced_sinkhorn_assignment_matrix(
        logits=logits,
        sample=sample,
        device=device,
        temperature=temperature,
        iterations=iterations,
    )
    n_atoms = int(len(sample.atom_positions))
    n_targets = int(len(sample.target_positions))
    pairs = torch.as_tensor(sample.optimal_assignment, dtype=torch.long, device=device)
    if pairs.numel() == 0:
        raise ValueError("assignment_sinkhorn_ce requires a non-empty oracle assignment")
    atom_indices = pairs[:, 0]
    target_indices = pairs[:, 1]
    valid = (atom_indices >= 0) & (atom_indices < n_atoms) & (target_indices >= 0) & (target_indices < n_targets)
    if not bool(valid.all().item()):
        raise ValueError("assignment_sinkhorn_ce oracle assignment contains invalid indices")
    probabilities = matrix[atom_indices, target_indices].clamp_min(torch.finfo(matrix.dtype).tiny)
    return -torch.log(probabilities).mean()


def target_balanced_log_sinkhorn_assignment_matrix(
    *,
    logits: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    device: torch.device,
    temperature: float = 0.25,
    iterations: int = 30,
) -> torch.Tensor:
    if float(temperature) <= 0.0:
        raise ValueError("assignment_log_sinkhorn_ce requires temperature > 0")
    if int(iterations) <= 0:
        raise ValueError("assignment_log_sinkhorn_ce requires iterations > 0")
    n_atoms = int(len(sample.atom_positions))
    n_targets = int(len(sample.target_positions))
    if n_targets == 0:
        raise ValueError("assignment_log_sinkhorn_ce requires at least one target")

    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    edge_types = torch.as_tensor(sample.edge_types, dtype=torch.long, device=device)
    atom_target = edge_types == EDGE_ATOM_TO_TARGET
    atom_indices = edge_index[0, atom_target]
    target_indices = edge_index[1, atom_target] - int(n_atoms)
    valid = (atom_indices >= 0) & (atom_indices < n_atoms) & (target_indices >= 0) & (target_indices < n_targets)
    atom_indices = atom_indices[valid]
    target_indices = target_indices[valid]
    edge_logits = logits[atom_target][valid]
    if edge_logits.numel() == 0:
        raise ValueError("assignment_log_sinkhorn_ce requires atom-to-target edges")

    log_matrix = torch.full((n_atoms, n_targets), -torch.inf, dtype=logits.dtype, device=device)
    if hasattr(log_matrix, "index_put_"):
        log_matrix.index_put_((atom_indices, target_indices), edge_logits, accumulate=False)
    else:
        for atom_idx, target_idx, value in zip(atom_indices.tolist(), target_indices.tolist(), edge_logits):
            log_matrix[int(atom_idx), int(target_idx)] = value

    log_matrix = log_matrix / torch.as_tensor(float(temperature), dtype=logits.dtype, device=device)
    finite = torch.isfinite(log_matrix)
    if not bool(finite.any().item()):
        raise ValueError("assignment_log_sinkhorn_ce requires finite candidate logits")
    negative_infinity = torch.as_tensor(-torch.inf, dtype=logits.dtype, device=device)
    log_matrix = torch.where(finite, log_matrix - torch.max(log_matrix[finite]), negative_infinity)

    for _ in range(int(iterations)):
        row_log_sums = torch.logsumexp(log_matrix, dim=1, keepdim=True)
        row_scales = torch.where(
            torch.isfinite(row_log_sums),
            torch.minimum(torch.zeros_like(row_log_sums), -row_log_sums),
            torch.zeros_like(row_log_sums),
        )
        log_matrix = log_matrix + row_scales
        column_log_sums = torch.logsumexp(log_matrix, dim=0, keepdim=True)
        column_scales = torch.where(
            torch.isfinite(column_log_sums),
            -column_log_sums,
            torch.zeros_like(column_log_sums),
        )
        log_matrix = log_matrix + column_scales
    return log_matrix


def assignment_log_sinkhorn_cross_entropy(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    temperature: float = 0.25,
    iterations: int = 30,
) -> torch.Tensor:
    del labels, mask
    log_matrix = target_balanced_log_sinkhorn_assignment_matrix(
        logits=logits,
        sample=sample,
        device=device,
        temperature=temperature,
        iterations=iterations,
    )
    n_atoms = int(len(sample.atom_positions))
    n_targets = int(len(sample.target_positions))
    pairs = torch.as_tensor(sample.optimal_assignment, dtype=torch.long, device=device)
    if pairs.numel() == 0:
        raise ValueError("assignment_log_sinkhorn_ce requires a non-empty oracle assignment")
    atom_indices = pairs[:, 0]
    target_indices = pairs[:, 1]
    valid = (atom_indices >= 0) & (atom_indices < n_atoms) & (target_indices >= 0) & (target_indices < n_targets)
    if not bool(valid.all().item()):
        raise ValueError("assignment_log_sinkhorn_ce oracle assignment contains invalid indices")
    log_tiny = torch.log(torch.as_tensor(torch.finfo(log_matrix.dtype).tiny, dtype=log_matrix.dtype, device=device))
    log_probabilities = torch.clamp(log_matrix[atom_indices, target_indices], min=log_tiny)
    return -log_probabilities.mean()


def source_hard_negative_margin_loss(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    margin: float = 1.0,
) -> torch.Tensor:
    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    source_nodes = edge_index[0, mask]
    source_logits = logits[mask]
    source_labels = labels[mask]
    if source_logits.numel() == 0:
        raise ValueError("source_margin requires atom-to-target edges")

    _unique_sources, inverse = torch.unique(source_nodes, sorted=True, return_inverse=True)
    group_count = int(inverse.max().item()) + 1
    neg_inf = torch.as_tensor(-torch.inf, dtype=source_logits.dtype, device=device)
    positive_values = torch.where(source_labels > 0.5, source_logits, neg_inf)
    negative_values = torch.where(source_labels <= 0.5, source_logits, neg_inf)
    positive_max = torch.full((group_count,), -torch.inf, dtype=source_logits.dtype, device=device)
    negative_max = torch.full((group_count,), -torch.inf, dtype=source_logits.dtype, device=device)
    if hasattr(positive_max, "scatter_reduce_"):
        positive_max.scatter_reduce_(0, inverse, positive_values, reduce="amax", include_self=True)
        negative_max.scatter_reduce_(0, inverse, negative_values, reduce="amax", include_self=True)
    else:
        for group_index in range(group_count):
            group = inverse == group_index
            positive_max[group_index] = positive_values[group].max()
            negative_max[group_index] = negative_values[group].max()
    valid = torch.isfinite(positive_max) & torch.isfinite(negative_max)
    if not bool(valid.any().item()):
        raise ValueError("source_margin requires at least one source with positive and negative atom-to-target edges")
    losses = torch.relu(
        torch.as_tensor(float(margin), dtype=source_logits.dtype, device=device)
        - positive_max[valid]
        + negative_max[valid]
    )
    return losses.mean()


def target_hard_negative_margin_loss(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    margin: float = 1.0,
) -> torch.Tensor:
    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    target_nodes = edge_index[1, mask]
    target_logits = logits[mask]
    target_labels = labels[mask]
    if target_logits.numel() == 0:
        raise ValueError("target_margin requires atom-to-target edges")

    _unique_targets, inverse = torch.unique(target_nodes, sorted=True, return_inverse=True)
    group_count = int(inverse.max().item()) + 1
    neg_inf = torch.as_tensor(-torch.inf, dtype=target_logits.dtype, device=device)
    positive_values = torch.where(target_labels > 0.5, target_logits, neg_inf)
    negative_values = torch.where(target_labels <= 0.5, target_logits, neg_inf)
    positive_max = torch.full((group_count,), -torch.inf, dtype=target_logits.dtype, device=device)
    negative_max = torch.full((group_count,), -torch.inf, dtype=target_logits.dtype, device=device)
    if hasattr(positive_max, "scatter_reduce_"):
        positive_max.scatter_reduce_(0, inverse, positive_values, reduce="amax", include_self=True)
        negative_max.scatter_reduce_(0, inverse, negative_values, reduce="amax", include_self=True)
    else:
        for group_index in range(group_count):
            group = inverse == group_index
            positive_max[group_index] = positive_values[group].max()
            negative_max[group_index] = negative_values[group].max()
    valid = torch.isfinite(positive_max) & torch.isfinite(negative_max)
    if not bool(valid.any().item()):
        raise ValueError("target_margin requires at least one target with positive and negative atom-to-target edges")
    losses = torch.relu(
        torch.as_tensor(float(margin), dtype=target_logits.dtype, device=device)
        - positive_max[valid]
        + negative_max[valid]
    )
    return losses.mean()


def assignment_structured_margin_loss(
    *,
    logits: torch.Tensor,
    labels: torch.Tensor,
    sample: GraphSample | TrainingGraphBatch,
    mask: torch.Tensor,
    device: torch.device,
    margin: float = 1.0,
) -> torch.Tensor:
    del labels, mask
    n_atoms = int(len(sample.atom_positions))
    n_targets = int(len(sample.target_positions))
    if n_targets == 0:
        raise ValueError("assignment_margin requires at least one target")

    detached_logits = logits.detach().cpu().numpy()
    score_matrix = np.full((n_atoms, n_targets), -1e9, dtype=np.float64)
    edge_lookup: dict[tuple[int, int], int] = {}
    for edge_pos, (src, dst) in enumerate(sample.edge_index.T):
        if int(sample.edge_types[edge_pos]) != EDGE_ATOM_TO_TARGET:
            continue
        atom_idx = int(src)
        target_idx = int(dst) - n_atoms
        if 0 <= atom_idx < n_atoms and 0 <= target_idx < n_targets:
            value = float(detached_logits[edge_pos])
            if value >= score_matrix[atom_idx, target_idx]:
                score_matrix[atom_idx, target_idx] = value
                edge_lookup[(atom_idx, target_idx)] = int(edge_pos)

    oracle_pairs = {(int(atom_idx), int(target_idx)) for atom_idx, target_idx in sample.optimal_assignment}
    oracle_edge_indices = []
    for pair in sample.optimal_assignment:
        key = (int(pair[0]), int(pair[1]))
        edge_idx = edge_lookup.get(key)
        if edge_idx is None:
            raise ValueError("assignment_margin requires oracle atom-to-target edges in the candidate graph")
        oracle_edge_indices.append(edge_idx)

    augmented_scores = score_matrix.copy()
    for atom_idx in range(n_atoms):
        for target_idx in range(n_targets):
            if augmented_scores[atom_idx, target_idx] <= -1e8:
                continue
            if (atom_idx, target_idx) not in oracle_pairs:
                augmented_scores[atom_idx, target_idx] += float(margin)
    atom_indices, target_indices = linear_sum_assignment(-augmented_scores)
    competitor_edge_indices = []
    wrong_pairs = 0
    for atom_idx, target_idx in zip(atom_indices.tolist(), target_indices.tolist()):
        key = (int(atom_idx), int(target_idx))
        edge_idx = edge_lookup.get(key)
        if edge_idx is None:
            raise ValueError("assignment_margin competitor used a missing candidate edge")
        competitor_edge_indices.append(edge_idx)
        if key not in oracle_pairs:
            wrong_pairs += 1

    oracle_index = torch.as_tensor(oracle_edge_indices, dtype=torch.long, device=device)
    competitor_index = torch.as_tensor(competitor_edge_indices, dtype=torch.long, device=device)
    oracle_score = logits[oracle_index].sum()
    competitor_score = logits[competitor_index].sum()
    structured_margin = torch.as_tensor(float(margin * wrong_pairs), dtype=logits.dtype, device=device)
    normalizer = max(1, n_targets)
    return torch.relu(competitor_score + structured_margin - oracle_score) / float(normalizer)


def save_edge_scoring_checkpoint(
    *,
    model: "EdgeScoringGNN",
    optimizer: torch.optim.Optimizer | None = None,
    checkpoint_path: Path,
    model_config: dict[str, object],
    config: dict[str, object],
    training_state: dict[str, object],
) -> None:
    checkpoint_path = Path(checkpoint_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    state_dict = {name: tensor.detach().cpu() for name, tensor in model.state_dict().items()}
    payload = {
        "paper_id": "2604.08669",
        "model": model_config,
        "training_config": config,
        "training_state": training_state,
        "state_dict": state_dict,
    }
    if optimizer is not None:
        payload["optimizer_state_dict"] = optimizer.state_dict()
    torch.save(payload, checkpoint_path)


def resolve_torch_device(device: str) -> torch.device:
    requested = torch.device(device)
    if requested.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    return requested


def load_edge_scoring_model(checkpoint_path: Path, device: str = "cpu") -> "EdgeScoringGNN":
    checkpoint_path = Path(checkpoint_path)
    torch_device = resolve_torch_device(device)
    checkpoint = load_torch_checkpoint(checkpoint_path, torch_device)
    model_config = checkpoint["model"]
    model = EdgeScoringGNN(
        node_dim=int(model_config["node_dim"]),
        edge_dim=int(model_config["edge_dim"]),
        hidden_dim=int(model_config["hidden_dim"]),
        message_passes=int(model_config["message_passes"]),
        model_arch=str(model_config.get("model_arch", "plain")),
        score_head=str(model_config.get("score_head", "shallow")),
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.to(torch_device)
    model.eval()
    return model


def load_torch_checkpoint(checkpoint_path: Path, device: torch.device) -> dict[str, Any]:
    try:
        return torch.load(checkpoint_path, map_location=device, weights_only=False)
    except TypeError:
        return torch.load(checkpoint_path, map_location=device)


def predict_edge_scores(model: "EdgeScoringGNN", sample: GraphSample) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(model(sample)).detach().cpu().numpy()


def predict_edge_logits(model: "EdgeScoringGNN", sample: GraphSample) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return model(sample).detach().cpu().numpy()


def transform_atom_target_scores(sample: GraphSample, edge_values: np.ndarray, *, method: str) -> np.ndarray:
    values = np.asarray(edge_values, dtype=np.float64)
    if values.shape[0] != sample.edge_index.shape[1]:
        raise ValueError("edge_values length must match sample edge count")
    if method == "sigmoid":
        return 1.0 / (1.0 + np.exp(-np.clip(values, -60.0, 60.0)))
    if method == "logits":
        return values.copy()
    if method == "source_softmax":
        return source_softmax_atom_target_scores(sample, values)
    if method == "source_rank":
        return source_rank_atom_target_scores(sample, values)
    raise ValueError(f"unknown score transform method: {method}")


def source_softmax_atom_target_scores(sample: GraphSample, edge_values: np.ndarray) -> np.ndarray:
    output = np.asarray(edge_values, dtype=np.float64).copy()
    atom_target = sample.edge_types == EDGE_ATOM_TO_TARGET
    output[atom_target] = 0.0
    for source in np.unique(sample.edge_index[0, atom_target]):
        group = atom_target & (sample.edge_index[0] == source)
        group_values = np.asarray(edge_values[group], dtype=np.float64)
        shifted = group_values - np.max(group_values)
        exp_values = np.exp(np.clip(shifted, -60.0, 60.0))
        output[group] = exp_values / np.sum(exp_values)
    return output


def source_rank_atom_target_scores(sample: GraphSample, edge_values: np.ndarray) -> np.ndarray:
    output = np.asarray(edge_values, dtype=np.float64).copy()
    atom_target = sample.edge_types == EDGE_ATOM_TO_TARGET
    output[atom_target] = 0.0
    for source in np.unique(sample.edge_index[0, atom_target]):
        group_indices = np.flatnonzero(atom_target & (sample.edge_index[0] == source))
        order = np.argsort(-np.asarray(edge_values[group_indices], dtype=np.float64), kind="stable")
        ranks = np.empty(len(group_indices), dtype=np.float64)
        ranks[order] = np.arange(1, len(group_indices) + 1, dtype=np.float64)
        output[group_indices] = 1.0 / ranks
    return output


def summarize_eval_rows(rows: list[dict[str, float]]) -> dict[str, float | int]:
    if not rows:
        return {"eval_samples": 0}
    keys = sorted(rows[0])
    summary: dict[str, float | int] = {"eval_samples": len(rows)}
    for key in keys:
        values = np.asarray([row[key] for row in rows], dtype=np.float64)
        summary[f"mean_{key}"] = float(np.mean(values))
    return summary


def diagnose_assignment_sample(sample: GraphSample, edge_scores: np.ndarray) -> dict[str, object]:
    edge_scores = np.asarray(edge_scores, dtype=np.float64)
    if edge_scores.shape[0] != sample.edge_index.shape[1]:
        raise ValueError("edge_scores length must match sample edge count")

    decoded = decode_assignment_from_edge_scores(sample, edge_scores)
    assignment = assignment_metrics(sample, decoded)
    candidate_coverage = atom_target_candidate_coverage(sample)
    source_rank = source_wise_positive_rank_diagnostics(sample, edge_scores)
    score_distribution = atom_target_score_distribution(sample, edge_scores)

    return {
        "atom_count": int(len(sample.atom_positions)),
        "target_count": int(sample.target_count),
        "edge_count": int(sample.edge_index.shape[1]),
        "atom_to_target_edge_count": int(np.sum(sample.edge_types == EDGE_ATOM_TO_TARGET)),
        "optimal_edge_count": int(sample.optimal_assignment.shape[0]),
        "assignment": assignment,
        "candidate_coverage": candidate_coverage,
        "source_rank": source_rank,
        "score_distribution": score_distribution,
    }


def atom_target_candidate_coverage(sample: GraphSample) -> dict[str, float | int]:
    n_atoms = len(sample.atom_positions)
    n_targets = len(sample.target_positions)
    atom_to_target_pairs = {
        (int(src), int(dst) - n_atoms)
        for edge_pos, (src, dst) in enumerate(sample.edge_index.T)
        if int(sample.edge_types[edge_pos]) == EDGE_ATOM_TO_TARGET
    }
    source_candidate_counts: dict[int, int] = {}
    for atom_idx, _target_idx in atom_to_target_pairs:
        source_candidate_counts[atom_idx] = source_candidate_counts.get(atom_idx, 0) + 1
    inferred_knn_budget = infer_source_neighbor_budget(source_candidate_counts)
    nearest_ranks = assigned_target_nearest_ranks(sample)
    covered = 0
    nearest_budget_covered = 0
    for pair_index, (atom_idx, target_idx) in enumerate(sample.optimal_assignment.astype(np.int64)):
        atom_int = int(atom_idx)
        target_int = int(target_idx)
        if (atom_int, target_int) in atom_to_target_pairs:
            covered += 1
        nearest_rank = int(nearest_ranks[pair_index])
        if nearest_rank <= max(1, min(inferred_knn_budget, n_targets)):
            nearest_budget_covered += 1

    optimal_count = int(sample.optimal_assignment.shape[0])
    return {
        "optimal_edges": optimal_count,
        "covered_optimal_edges": int(covered),
        "optimal_edge_coverage": covered / optimal_count if optimal_count else 0.0,
        "nearest_budget_covered_edges": int(nearest_budget_covered),
        "pure_knn_coverage": nearest_budget_covered / optimal_count if optimal_count else 0.0,
        "inferred_knn_budget": int(inferred_knn_budget),
        "mean_nearest_rank": float(np.mean(nearest_ranks)) if nearest_ranks else 0.0,
        "p90_nearest_rank": percentile(nearest_ranks, 90),
    }


def infer_source_neighbor_budget(source_candidate_counts: dict[int, int]) -> int:
    if not source_candidate_counts:
        return 0
    values = np.asarray(list(source_candidate_counts.values()), dtype=np.int64)
    unique, counts = np.unique(values, return_counts=True)
    return int(unique[np.argmax(counts)])


def assigned_target_nearest_ranks(sample: GraphSample, *, chunk_size: int = 256) -> list[int]:
    assignment = sample.optimal_assignment.astype(np.int64)
    if assignment.size == 0:
        return []
    atom_indices = assignment[:, 0]
    target_indices = assignment[:, 1]
    ranks: list[int] = []
    target_positions = np.asarray(sample.target_positions, dtype=np.float64)
    atom_positions = np.asarray(sample.atom_positions, dtype=np.float64)
    for start in range(0, len(assignment), max(1, int(chunk_size))):
        end = min(start + max(1, int(chunk_size)), len(assignment))
        atoms = atom_positions[atom_indices[start:end]]
        assigned_targets = target_indices[start:end]
        deltas = atoms[:, None, :] - target_positions[None, :, :]
        distances = np.sum(deltas * deltas, axis=2)
        assigned_distances = distances[np.arange(end - start), assigned_targets]
        ranks.extend((np.sum(distances < assigned_distances[:, None], axis=1) + 1).astype(np.int64).tolist())
    return ranks


def source_wise_positive_rank_diagnostics(
    sample: GraphSample,
    edge_scores: np.ndarray,
    *,
    tie_tolerance: float = 1e-12,
) -> dict[str, float | int]:
    n_atoms = len(sample.atom_positions)
    candidates_by_source: dict[int, list[tuple[int, float, float]]] = {}
    for edge_pos, (src, dst) in enumerate(sample.edge_index.T):
        if int(sample.edge_types[edge_pos]) != EDGE_ATOM_TO_TARGET:
            continue
        atom_idx = int(src)
        target_idx = int(dst) - n_atoms
        if 0 <= atom_idx < n_atoms and 0 <= target_idx < len(sample.target_positions):
            candidates_by_source.setdefault(atom_idx, []).append(
                (target_idx, float(edge_scores[edge_pos]), float(sample.edge_labels[edge_pos]))
            )

    ranks: list[int] = []
    optimistic_ranks: list[int] = []
    tie_counts: list[int] = []
    margins: list[float] = []
    missing = 0
    rank1 = 0
    optimistic_rank1 = 0
    for atom_idx, target_idx in sample.optimal_assignment.astype(np.int64):
        candidates = candidates_by_source.get(int(atom_idx), [])
        matching_scores = [score for candidate_target, score, _label in candidates if candidate_target == int(target_idx)]
        if not matching_scores:
            missing += 1
            continue
        positive_score = max(matching_scores)
        candidate_scores = [score for _target, score, _label in candidates]
        optimistic_rank = 1 + sum(1 for score in candidate_scores if score > positive_score + tie_tolerance)
        rank = sum(1 for score in candidate_scores if score >= positive_score - tie_tolerance)
        tie_count = sum(1 for score in candidate_scores if abs(score - positive_score) <= tie_tolerance)
        optimistic_ranks.append(int(optimistic_rank))
        ranks.append(int(rank))
        tie_counts.append(int(tie_count))
        if rank == 1:
            rank1 += 1
        if optimistic_rank == 1:
            optimistic_rank1 += 1
        negative_scores = [score for candidate_target, score, _label in candidates if candidate_target != int(target_idx)]
        if negative_scores:
            margins.append(float(positive_score - max(negative_scores)))

    optimal_count = int(sample.optimal_assignment.shape[0])
    valid_count = len(ranks)
    return {
        "optimal_edges": optimal_count,
        "ranked_positive_edges": int(valid_count),
        "missing_positive_edges": int(missing),
        "rank1_edges": int(rank1),
        "rank1_rate": rank1 / valid_count if valid_count else 0.0,
        "mean_positive_rank": float(np.mean(ranks)) if ranks else 0.0,
        "p50_positive_rank": percentile(ranks, 50),
        "p90_positive_rank": percentile(ranks, 90),
        "optimistic_rank1_edges": int(optimistic_rank1),
        "optimistic_rank1_rate": optimistic_rank1 / valid_count if valid_count else 0.0,
        "optimistic_mean_positive_rank": float(np.mean(optimistic_ranks)) if optimistic_ranks else 0.0,
        "tied_positive_edges": int(sum(1 for count in tie_counts if count > 1)),
        "mean_tie_count": float(np.mean(tie_counts)) if tie_counts else 0.0,
        "mean_positive_margin": float(np.mean(margins)) if margins else 0.0,
        "p10_positive_margin": percentile(margins, 10),
    }


def atom_target_score_distribution(sample: GraphSample, edge_scores: np.ndarray) -> dict[str, object]:
    atom_target_mask = sample.edge_types == EDGE_ATOM_TO_TARGET
    positive_mask = atom_target_mask & (sample.edge_labels > 0.5)
    negative_mask = atom_target_mask & (sample.edge_labels <= 0.5)
    return {
        "positive": numeric_distribution(edge_scores[positive_mask]),
        "negative": numeric_distribution(edge_scores[negative_mask]),
    }


def numeric_distribution(values: np.ndarray | list[float]) -> dict[str, float | int | None]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "min": None,
            "p10": None,
            "p50": None,
            "p90": None,
            "max": None,
        }
    return {
        "count": int(array.size),
        "mean": float(np.mean(array)),
        "std": float(np.std(array)),
        "min": float(np.min(array)),
        "p10": float(np.percentile(array, 10)),
        "p50": float(np.percentile(array, 50)),
        "p90": float(np.percentile(array, 90)),
        "max": float(np.max(array)),
    }


def summarize_assignment_diagnostics(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {"eval_samples": 0}

    average_gaps = [float(row["assignment"]["average_distance_gap"]) for row in rows]  # type: ignore[index]
    max_gaps = [float(row["assignment"]["max_distance_gap"]) for row in rows]  # type: ignore[index]
    optimal_coverages = [
        float(row["candidate_coverage"]["optimal_edge_coverage"]) for row in rows  # type: ignore[index]
    ]
    pure_knn_coverages = [float(row["candidate_coverage"]["pure_knn_coverage"]) for row in rows]  # type: ignore[index]
    rank1_rates = [float(row["source_rank"]["rank1_rate"]) for row in rows]  # type: ignore[index]
    mean_positive_ranks = [float(row["source_rank"]["mean_positive_rank"]) for row in rows]  # type: ignore[index]
    optimistic_rank1_rates = [
        float(row["source_rank"].get("optimistic_rank1_rate", row["source_rank"]["rank1_rate"]))  # type: ignore[index]
        for row in rows
    ]
    optimistic_mean_positive_ranks = [
        float(row["source_rank"].get("optimistic_mean_positive_rank", row["source_rank"]["mean_positive_rank"]))  # type: ignore[index]
        for row in rows
    ]
    tied_positive_edges = [int(row["source_rank"].get("tied_positive_edges", 0)) for row in rows]  # type: ignore[index]
    mean_tie_counts = [float(row["source_rank"].get("mean_tie_count", 1.0)) for row in rows]  # type: ignore[index]
    mean_positive_margins = [
        float(row["source_rank"].get("mean_positive_margin", 0.0)) for row in rows  # type: ignore[index]
    ]
    total_missing = sum(int(row["source_rank"]["missing_positive_edges"]) for row in rows)  # type: ignore[index]
    total_optimal = sum(int(row["source_rank"]["optimal_edges"]) for row in rows)  # type: ignore[index]
    positive_means = [
        float(row["score_distribution"]["positive"]["mean"])  # type: ignore[index]
        for row in rows
        if row["score_distribution"]["positive"]["mean"] is not None  # type: ignore[index]
    ]
    negative_means = [
        float(row["score_distribution"]["negative"]["mean"])  # type: ignore[index]
        for row in rows
        if row["score_distribution"]["negative"]["mean"] is not None  # type: ignore[index]
    ]

    return {
        "eval_samples": len(rows),
        "assignment_gap": {
            "mean_average_distance_gap": float(np.mean(average_gaps)),
            "p50_average_distance_gap": percentile(average_gaps, 50),
            "p75_average_distance_gap": percentile(average_gaps, 75),
            "p90_average_distance_gap": percentile(average_gaps, 90),
            "p95_average_distance_gap": percentile(average_gaps, 95),
            "mean_max_distance_gap": float(np.mean(max_gaps)),
            "p90_max_distance_gap": percentile(max_gaps, 90),
        },
        "candidate_coverage": {
            "mean_optimal_edge_coverage": float(np.mean(optimal_coverages)),
            "mean_pure_knn_coverage": float(np.mean(pure_knn_coverages)),
        },
        "source_rank": {
            "mean_rank1_rate": float(np.mean(rank1_rates)),
            "mean_positive_rank": float(np.mean(mean_positive_ranks)),
            "mean_optimistic_rank1_rate": float(np.mean(optimistic_rank1_rates)),
            "mean_optimistic_positive_rank": float(np.mean(optimistic_mean_positive_ranks)),
            "total_tied_positive_edges": int(sum(tied_positive_edges)),
            "mean_tie_count": float(np.mean(mean_tie_counts)),
            "mean_positive_margin": float(np.mean(mean_positive_margins)),
            "total_missing_positive_edges": int(total_missing),
            "total_optimal_edges": int(total_optimal),
            "missing_positive_edge_rate": total_missing / total_optimal if total_optimal else 0.0,
        },
        "score_distribution": {
            "mean_positive_score": float(np.mean(positive_means)) if positive_means else None,
            "mean_negative_score": float(np.mean(negative_means)) if negative_means else None,
            "mean_score_margin": (
                float(np.mean(positive_means) - np.mean(negative_means))
                if positive_means and negative_means
                else None
            ),
        },
    }


def percentile(values: list[float] | list[int] | np.ndarray, q: float) -> float:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        return 0.0
    return float(np.percentile(array, q))


class EdgeScoringGNN(torch.nn.Module):
    def __init__(
        self,
        node_dim: int,
        edge_dim: int,
        hidden_dim: int,
        message_passes: int,
        *,
        model_arch: str = "plain",
        score_head: str = "shallow",
    ) -> None:
        super().__init__()
        self.message_passes = int(message_passes)
        if model_arch not in {"plain", "residual_layernorm"}:
            raise ValueError(f"unsupported model_arch: {model_arch}")
        self.model_arch = model_arch
        if score_head not in {"shallow", "deep_edge_mlp"}:
            raise ValueError(f"unsupported score_head: {score_head}")
        self.score_head = score_head
        self.node_encoder = torch.nn.Sequential(
            torch.nn.Linear(node_dim, hidden_dim),
            torch.nn.ReLU(),
        )
        self.node_norm = torch.nn.LayerNorm(hidden_dim) if model_arch == "residual_layernorm" else torch.nn.Identity()
        self.message = torch.nn.Sequential(
            torch.nn.Linear(hidden_dim + edge_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim),
        )
        self.update = torch.nn.Sequential(
            torch.nn.Linear(hidden_dim * 2, hidden_dim),
            torch.nn.ReLU(),
        )
        self.update_norm = (
            torch.nn.LayerNorm(hidden_dim) if model_arch == "residual_layernorm" else torch.nn.Identity()
        )
        classifier_input_dim = hidden_dim * 2 + edge_dim
        if score_head == "deep_edge_mlp":
            self.classifier = torch.nn.Sequential(
                torch.nn.Linear(classifier_input_dim, hidden_dim * 2),
                torch.nn.LayerNorm(hidden_dim * 2),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim * 2, hidden_dim * 2),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim * 2, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, 1),
            )
        else:
            self.classifier = torch.nn.Sequential(
                torch.nn.Linear(classifier_input_dim, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, 1),
            )

    def forward(self, sample: GraphSample):
        device = next(self.parameters()).device
        node_features = torch.as_tensor(sample.node_features, dtype=torch.float32, device=device)
        edge_features = torch.as_tensor(sample.edge_features, dtype=torch.float32, device=device)
        edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
        src = edge_index[0]
        dst = edge_index[1]
        node_state = self.node_norm(self.node_encoder(node_features))
        for _ in range(self.message_passes):
            messages = self.message(torch.cat([node_state[src], edge_features], dim=1))
            aggregate = torch.zeros_like(node_state)
            aggregate.index_add_(0, dst, messages)
            degree = torch.zeros((node_state.shape[0], 1), dtype=torch.float32, device=device)
            degree.index_add_(0, dst, torch.ones((len(dst), 1), dtype=torch.float32, device=device))
            aggregate = aggregate / degree.clamp_min(1.0)
            updated = self.update(torch.cat([node_state, aggregate], dim=1))
            if self.model_arch == "residual_layernorm":
                node_state = self.update_norm(node_state + updated)
            else:
                node_state = updated
        logits = self.classifier(torch.cat([node_state[src], node_state[dst], edge_features], dim=1))
        return logits.squeeze(1)
