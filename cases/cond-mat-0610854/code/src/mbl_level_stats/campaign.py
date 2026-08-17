"""Checkpointed exact-diagonalization campaign and evidence aggregation."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .hamiltonian import FermionChain
from .statistics import (
    GOE_MEAN_PAPER,
    POISSON_MEAN,
    adjacent_gap_ratios,
    crossing_estimates,
    poisson_density,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def _seed(base_seed: int, *coordinates: int) -> int:
    sequence = np.random.SeedSequence([base_seed, *coordinates])
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def _w_key(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".").replace("-", "m").replace(".", "p")


def _condition_key(length: int, strength: float) -> str:
    return f"L{length}_W{_w_key(strength)}"


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    parameters = payload.get("parameters")
    if parameters is not None:
        if not isinstance(parameters, dict) or not parameters:
            raise ValueError("parameters must be a non-empty object")
        overlap = sorted(set(payload) & set(parameters))
        if overlap:
            raise ValueError(f"parameters duplicate top-level keys: {overlap}")
        payload = {**payload, **parameters}
    required = {"paper_id", "run_profile", "model", "w_values", "sizes", "histogram", "goe", "seed"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"config missing required keys: {missing}")
    if payload["paper_id"] != "cond-mat-0610854":
        raise ValueError("config paper_id mismatch")
    values = [float(value) for value in payload["w_values"]]
    if values != sorted(set(values)):
        raise ValueError("w_values must be unique and sorted")
    for row in payload["sizes"]:
        length = int(row["length"])
        if length % 2 or length < 8:
            raise ValueError("paper sizes must be even and at least eight")
        if samples_for(row, values[0], payload) < 1:
            raise ValueError("every size requires at least one sample")
    return payload


def samples_for(size_row: dict[str, Any], strength: float, config: dict[str, Any]) -> int:
    if "samples" in size_row:
        return int(size_row["samples"])
    critical = config.get("critical_window", {})
    in_critical = float(critical.get("minimum", math.inf)) <= strength <= float(
        critical.get("maximum", -math.inf)
    )
    field = "critical_samples" if in_critical else "default_samples"
    return int(size_row[field])


def enumerate_conditions(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "key": _condition_key(int(size["length"]), float(strength)),
            "length": int(size["length"]),
            "strength": float(strength),
            "samples": samples_for(size, float(strength), config),
            "sample_provenance": str(size.get("sample_provenance", "declared_reproduction_choice")),
        }
        for size in config["sizes"]
        for strength in config["w_values"]
    ]


@dataclass
class DiagonalizationBackend:
    name: str

    def eigvalsh(self, matrix: np.ndarray) -> np.ndarray:
        if self.name == "numpy":
            return np.linalg.eigvalsh(matrix)
        if self.name == "cupy":
            try:
                import cupy as cp
            except ImportError as exc:  # pragma: no cover - optional A100 path
                raise RuntimeError("CuPy backend requested but cupy is unavailable") from exc
            device_matrix = cp.asarray(matrix)
            values = cp.linalg.eigvalsh(device_matrix)
            return cp.asnumpy(values)
        raise ValueError(f"unsupported backend: {self.name}")


def _empty_accumulator(histogram_bins: int) -> dict[str, Any]:
    return {
        "completed_sample_ids": [],
        "sample_count": 0,
        "sample_mean_sum": 0.0,
        "sample_mean_square_sum": 0.0,
        "ratio_count": 0,
        "histogram_counts": [0] * histogram_bins,
    }


def _update_accumulator(accumulator: dict[str, Any], sample_id: int, ratios: np.ndarray, edges: np.ndarray) -> None:
    sample_mean = float(np.mean(ratios))
    accumulator["completed_sample_ids"].append(sample_id)
    accumulator["sample_count"] += 1
    accumulator["sample_mean_sum"] += sample_mean
    accumulator["sample_mean_square_sum"] += sample_mean * sample_mean
    accumulator["ratio_count"] += int(ratios.size)
    histogram = np.histogram(ratios, bins=edges)[0]
    accumulator["histogram_counts"] = (
        np.asarray(accumulator["histogram_counts"], dtype=np.int64) + histogram
    ).tolist()


def _checkpoint_path(output_root: Path, profile: str, shard_index: int) -> Path:
    return output_root / "checkpoints" / profile / f"shard-{shard_index:04d}.json"


def run_shard(
    config: dict[str, Any],
    *,
    config_path: Path,
    output_root: Path,
    shard_index: int,
    shard_count: int,
    resume: bool,
) -> dict[str, Any]:
    if not 0 <= shard_index < shard_count:
        raise ValueError("shard_index must lie in [0, shard_count)")
    config_sha = sha256_file(config_path)
    profile = str(config["run_profile"])
    checkpoint_path = _checkpoint_path(output_root, profile, shard_index)
    histogram_bins = int(config["histogram"]["bins"])
    edges = np.linspace(0.0, 1.0, histogram_bins + 1)
    state: dict[str, Any] = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_profile": profile,
        "config_sha256": config_sha,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "conditions": {},
        "goe": _empty_accumulator(histogram_bins),
    }
    if resume and checkpoint_path.is_file():
        loaded = json.loads(checkpoint_path.read_text())
        if loaded.get("config_sha256") != config_sha or loaded.get("shard_count") != shard_count:
            raise RuntimeError("checkpoint does not match config or shard topology")
        state = loaded

    model = config["model"]
    backend = DiagonalizationBackend(str(config.get("backend", "numpy")))
    distribution_length = int(config["histogram"]["model_length"])
    distribution_strengths = {float(value) for value in config["histogram"]["model_strengths"]}
    base_seed = int(config["seed"])
    checkpoint_interval = max(1, int(config.get("checkpoint_interval", 1)))
    chain_cache: dict[int, tuple[FermionChain, np.ndarray, np.ndarray, float]] = {}

    for condition in enumerate_conditions(config):
        length = int(condition["length"])
        strength = float(condition["strength"])
        key = str(condition["key"])
        accumulator = state["conditions"].setdefault(key, _empty_accumulator(histogram_bins))
        completed = set(int(value) for value in accumulator["completed_sample_ids"])
        assigned_ids = list(range(shard_index, int(condition["samples"]), shard_count))
        if length not in chain_cache:
            chain = FermionChain(
                length=length,
                particles=length // 2,
                interaction=float(model["interaction"]),
                nearest_hopping=float(model["nearest_hopping"]),
                next_nearest_hopping=float(model["next_nearest_hopping"]),
                periodic=bool(model["periodic"]),
            )
            clean = chain.clean_hamiltonian()
            occupations = chain.occupations()
            hermitian_residual = float(np.max(np.abs(clean - clean.T)))
            chain_cache[length] = (chain, clean, occupations, hermitian_residual)
        chain, clean, occupations, _ = chain_cache[length]
        for local_counter, sample_id in enumerate(assigned_ids):
            if sample_id in completed:
                continue
            disorder_seed = _seed(base_seed, length, int(round(strength * 1000.0)), sample_id)
            disorder = chain.disorder_vector(strength=strength, seed=disorder_seed)
            matrix = clean.copy()
            diagonal = np.diag_indices_from(matrix)
            matrix[diagonal] += occupations @ disorder
            ratios = adjacent_gap_ratios(backend.eigvalsh(matrix))
            histogram_ratios = (
                ratios
                if length == distribution_length and strength in distribution_strengths
                else np.empty(0, dtype=np.float64)
            )
            _update_accumulator(accumulator, sample_id, ratios, edges)
            if histogram_ratios.size == 0:
                # Preserve the sample moments but remove histogram contributions for non-Fig.-1 conditions.
                accumulator["histogram_counts"] = (
                    np.asarray(accumulator["histogram_counts"], dtype=np.int64)
                    - np.histogram(ratios, bins=edges)[0]
                ).tolist()
                accumulator["ratio_count"] -= int(ratios.size)
            if (local_counter + 1) % checkpoint_interval == 0:
                _atomic_json(checkpoint_path, state)

    goe = config["goe"]
    goe_accumulator = state["goe"]
    goe_completed = set(int(value) for value in goe_accumulator["completed_sample_ids"])
    goe_size = int(goe["matrix_size"])
    for sample_id in range(shard_index, int(goe["samples"]), shard_count):
        if sample_id in goe_completed:
            continue
        rng = np.random.default_rng(_seed(base_seed, 99991, goe_size, sample_id))
        raw = rng.normal(size=(goe_size, goe_size))
        matrix = (raw + raw.T) / np.sqrt(2.0 * goe_size)
        ratios = adjacent_gap_ratios(backend.eigvalsh(matrix))
        _update_accumulator(goe_accumulator, sample_id, ratios, edges)
        _atomic_json(checkpoint_path, state)

    state["condition_plan"] = enumerate_conditions(config)
    state["hermitian_residuals"] = {
        str(length): residual for length, (_, _, _, residual) in chain_cache.items()
    }
    state["status"] = "shard_complete"
    _atomic_json(checkpoint_path, state)
    partial_path = output_root / "partials" / profile / f"shard-{shard_index:04d}.json"
    _atomic_json(partial_path, state)
    return state


def _merge_accumulators(rows: list[dict[str, Any]], histogram_bins: int) -> dict[str, Any]:
    result = _empty_accumulator(histogram_bins)
    for row in rows:
        result["completed_sample_ids"].extend(int(value) for value in row["completed_sample_ids"])
        result["sample_count"] += int(row["sample_count"])
        result["sample_mean_sum"] += float(row["sample_mean_sum"])
        result["sample_mean_square_sum"] += float(row["sample_mean_square_sum"])
        result["ratio_count"] += int(row["ratio_count"])
        result["histogram_counts"] = (
            np.asarray(result["histogram_counts"], dtype=np.int64)
            + np.asarray(row["histogram_counts"], dtype=np.int64)
        ).tolist()
    if len(result["completed_sample_ids"]) != len(set(result["completed_sample_ids"])):
        raise RuntimeError("overlapping sample ids detected across shards")
    result["completed_sample_ids"] = sorted(result["completed_sample_ids"])
    return result


def _mean_and_error(accumulator: dict[str, Any]) -> tuple[float, float]:
    count = int(accumulator["sample_count"])
    if count < 1:
        return float("nan"), float("nan")
    mean = float(accumulator["sample_mean_sum"]) / count
    if count == 1:
        return mean, float("nan")
    mean_square = float(accumulator["sample_mean_square_sum"]) / count
    stderr = math.sqrt(max(0.0, mean_square - mean * mean) / (count - 1))
    return mean, stderr


def aggregate(
    config: dict[str, Any],
    *,
    config_path: Path,
    output_root: Path,
    shard_count: int,
) -> dict[str, Any]:
    profile = str(config["run_profile"])
    config_sha = sha256_file(config_path)
    partials = []
    for shard_index in range(shard_count):
        path = output_root / "partials" / profile / f"shard-{shard_index:04d}.json"
        if not path.is_file():
            raise RuntimeError(f"missing completed shard: {path}")
        payload = json.loads(path.read_text())
        if payload.get("status") != "shard_complete" or payload.get("config_sha256") != config_sha:
            raise RuntimeError(f"invalid completed shard: {path}")
        partials.append(payload)

    histogram_bins = int(config["histogram"]["bins"])
    edges = np.linspace(0.0, 1.0, histogram_bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    conditions = enumerate_conditions(config)
    merged_conditions = {
        str(condition["key"]): _merge_accumulators(
            [partial["conditions"][str(condition["key"])] for partial in partials],
            histogram_bins,
        )
        for condition in conditions
    }
    for condition in conditions:
        accumulator = merged_conditions[str(condition["key"])]
        if int(accumulator["sample_count"]) != int(condition["samples"]):
            raise RuntimeError(f"condition {condition['key']} has incomplete sample coverage")
        if accumulator["completed_sample_ids"] != list(range(int(condition["samples"]))):
            raise RuntimeError(f"condition {condition['key']} has a sample-id gap")

    data_dir = output_root / "data"
    checks_dir = output_root / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    curve_path = data_dir / "level_ratio_curves.csv"
    with curve_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["length", "strength", "samples", "mean_r", "stderr_r", "sample_provenance"],
        )
        writer.writeheader()
        for condition in conditions:
            accumulator = merged_conditions[str(condition["key"])]
            mean, stderr = _mean_and_error(accumulator)
            writer.writerow(
                {
                    "length": condition["length"],
                    "strength": condition["strength"],
                    "samples": accumulator["sample_count"],
                    "mean_r": f"{mean:.17g}",
                    "stderr_r": f"{stderr:.17g}",
                    "sample_provenance": condition["sample_provenance"],
                }
            )

    merged_goe = _merge_accumulators([partial["goe"] for partial in partials], histogram_bins)
    expected_goe_samples = int(config["goe"]["samples"])
    if merged_goe["sample_count"] != expected_goe_samples:
        raise RuntimeError("GOE sample coverage is incomplete")
    goe_mean, goe_stderr = _mean_and_error(merged_goe)
    histogram_path = data_dir / "level_ratio_histograms.csv"
    distribution_length = int(config["histogram"]["model_length"])
    distribution_strengths = [float(value) for value in config["histogram"]["model_strengths"]]
    histogram_rows: list[dict[str, Any]] = []
    poisson = poisson_density(centers)
    poisson /= float(np.sum(poisson * widths))
    goe_density = np.asarray(merged_goe["histogram_counts"], dtype=float)
    goe_density /= float(max(1, merged_goe["ratio_count"])) * widths
    for index, center in enumerate(centers):
        histogram_rows.extend(
            [
                {"series": "poisson", "strength": "", "ratio": center, "density": poisson[index]},
                {"series": "goe", "strength": "", "ratio": center, "density": goe_density[index]},
            ]
        )
    model_distribution_means: dict[str, float] = {}
    for strength in distribution_strengths:
        accumulator = merged_conditions[_condition_key(distribution_length, strength)]
        density = np.asarray(accumulator["histogram_counts"], dtype=float)
        density /= float(max(1, accumulator["ratio_count"])) * widths
        mean, _ = _mean_and_error(accumulator)
        model_distribution_means[str(strength)] = mean
        for index, center in enumerate(centers):
            histogram_rows.append(
                {"series": "model", "strength": strength, "ratio": center, "density": density[index]}
            )
    with histogram_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["series", "strength", "ratio", "density"])
        writer.writeheader()
        for row in histogram_rows:
            writer.writerow(
                {
                    "series": row["series"],
                    "strength": row["strength"],
                    "ratio": f"{float(row['ratio']):.17g}",
                    "density": f"{float(row['density']):.17g}",
                }
            )

    sizes = sorted(int(row["length"]) for row in config["sizes"])
    strengths = np.asarray(config["w_values"], dtype=float)
    curve_map = {
        length: np.asarray(
            [_mean_and_error(merged_conditions[_condition_key(length, float(strength))])[0] for strength in strengths]
        )
        for length in sizes
    }
    crossing_rows = []
    crossing_window = config["crossing_window"]
    mask = (strengths >= float(crossing_window["minimum"])) & (
        strengths <= float(crossing_window["maximum"])
    )
    for lower, upper in zip(sizes[:-1], sizes[1:]):
        estimates = crossing_estimates(strengths[mask], curve_map[lower][mask], curve_map[upper][mask])
        chosen = min(estimates, key=lambda row: abs(float(row["w_cross"]) - 6.0))
        crossing_rows.append({"lower_length": lower, "upper_length": upper, **chosen})
    crossing_path = data_dir / "crossing_drift.csv"
    with crossing_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["lower_length", "upper_length", "w_cross", "r_cross", "method"])
        writer.writeheader()
        writer.writerows(crossing_rows)

    low_strength = min(distribution_strengths)
    mid_strength = sorted(distribution_strengths)[1]
    high_strength = max(distribution_strengths)
    low_mean = model_distribution_means[str(low_strength)]
    mid_mean = model_distribution_means[str(mid_strength)]
    high_mean = model_distribution_means[str(high_strength)]
    assertions = [
        _assertion("CHK_POISSON_MEAN", "T001", abs(POISSON_MEAN - (2 * math.log(2) - 1)), 1e-15, "max", "Poisson mean matches its analytic integral."),
        _assertion("CHK_GOE_MEAN", "T001", abs(goe_mean - GOE_MEAN_PAPER), float(config["acceptance"]["goe_mean_abs_error_max"]), "max", "Independent GOE samples reproduce the printed mean."),
        _assertion("CHK_DIFFUSIVE_CLOSER_GOE", "T001", abs(low_mean - GOE_MEAN_PAPER) - abs(low_mean - POISSON_MEAN), 0.0, "max", "Weak-disorder model statistics are closer to GOE than Poisson."),
        _assertion("CHK_LOCALIZED_CLOSER_POISSON", "T001", abs(high_mean - POISSON_MEAN) - abs(high_mean - GOE_MEAN_PAPER), 0.0, "max", "Strong-disorder model statistics are closer to Poisson than GOE."),
        _assertion("CHK_INTERMEDIATE_ORDER", "T001", max(high_mean - mid_mean, mid_mean - low_mean), 0.0, "max", "The intermediate-disorder mean lies between weak and strong disorder."),
        _assertion("CHK_CURVE_CROSSOVER", "T002", max(float(curve[-1] - curve[0]) for curve in curve_map.values()), 0.0, "max", "Every size crosses from GOE-like to Poisson-like statistics as disorder grows."),
        _assertion("CHK_CROSSING_ROWS", "T003", float(len(crossing_rows)), float(len(sizes) - 1), "min", "Every adjacent size pair has a crossing or nearest-approach estimate."),
        _assertion("CHK_CROSSING_DRIFT", "T004", float(np.ptp([row["w_cross"] for row in crossing_rows])) if len(crossing_rows) > 1 else 0.0, float(config["acceptance"]["crossing_drift_min"]), "min", "Adjacent-size crossing positions are not stationary."),
    ]
    hermitian_residuals = {
        key: value for partial in partials for key, value in partial.get("hermitian_residuals", {}).items()
    }
    assertions.append(
        _assertion(
            "CHK_HERMITIAN",
            "T001,T002,T003,T004",
            max(float(value) for value in hermitian_residuals.values()),
            1e-13,
            "max",
            "Canonical fermionic signs yield an exactly Hermitian Hamiltonian.",
        )
    )
    checks_payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_profile": profile,
        "all_passed": all(row["passed"] for row in assertions),
        "assertions": assertions,
    }
    checks_path = checks_dir / "science_checks.json"
    _atomic_json(checks_path, checks_payload)

    claims = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_profile": profile,
        "poisson_mean": POISSON_MEAN,
        "goe_mean": goe_mean,
        "goe_mean_standard_error": goe_stderr,
        "model_distribution_means": model_distribution_means,
        "crossings": crossing_rows,
        "parameters_paper_exact": profile == "paper_scale_reconstructed" and bool(config.get("parameters_paper_exact", False)),
    }
    claims_path = data_dir / "quantitative_claims.json"
    _atomic_json(claims_path, claims)

    outputs = [curve_path, histogram_path, crossing_path, checks_path, claims_path]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_profile": profile,
        "config_sha256": config_sha,
        "shard_count": shard_count,
        "outputs": [
            {"path": str(path.relative_to(output_root)), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in outputs
        ],
    }
    manifest_path = checks_dir / "generated_data_manifest.json"
    _atomic_json(manifest_path, manifest)
    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_profile": profile,
        "status": "passed" if checks_payload["all_passed"] else "science_check_failed",
        "conditions": len(conditions),
        "disorder_samples": sum(int(condition["samples"]) for condition in conditions),
        "goe_samples": expected_goe_samples,
        "largest_dimension": max(math.comb(length, length // 2) for length in sizes),
        "all_science_checks_passed": checks_payload["all_passed"],
    }
    _atomic_json(checks_dir / "run_summary.json", summary)
    return summary


def _assertion(
    check_id: str,
    target_ids: str,
    value: float,
    threshold: float,
    comparator: str,
    description: str,
) -> dict[str, Any]:
    passed = value <= threshold if comparator == "max" else value >= threshold
    return {
        "check_id": check_id,
        "target_ids": target_ids.split(","),
        "description": description,
        "value": value,
        "threshold": threshold,
        "comparator": comparator,
        "passed": bool(passed),
    }


def validate_plan(config: dict[str, Any], *, shard_count: int) -> dict[str, Any]:
    conditions = enumerate_conditions(config)
    return {
        "paper_id": config["paper_id"],
        "run_profile": config["run_profile"],
        "conditions": len(conditions),
        "disorder_samples": sum(int(row["samples"]) for row in conditions),
        "goe_samples": int(config["goe"]["samples"]),
        "shard_count": shard_count,
        "sizes": [
            {"length": int(row["length"]), "dimension": math.comb(int(row["length"]), int(row["length"]) // 2)}
            for row in config["sizes"]
        ],
        "outputs": [
            "outputs/data/level_ratio_curves.csv",
            "outputs/data/level_ratio_histograms.csv",
            "outputs/data/crossing_drift.csv",
            "outputs/data/quantitative_claims.json",
            "outputs/checks/science_checks.json",
        ],
    }
