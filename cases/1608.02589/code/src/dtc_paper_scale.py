"""Paper-scale, source-independent numerical campaign for arXiv:1608.02589.

The module owns the complete numerical path for every data-bearing panel in
the main paper and supplement.  It never opens ``raw/`` or reference images.
Those assets belong to the post-freeze comparison/render-contract lane.
"""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from dtc_feature_sim import (
    apply_x_rotation,
    endpoint_mutual_information_from_eigenvectors,
    rx_product_matrix,
    z_table,
)

PAPER_ID = "1608.02589"
TARGET_IDS = ("T001", "T002", "T003", "T004")
FAMILY_OUTPUTS = {
    "rigidity": "main_fig1_rigidity.json",
    "level_statistics": "main_fig2_level_statistics.json",
    "nearest_variance": "main_fig2_variance.json",
    "mutual_information": "main_fig3_and_supp_s2.json",
    "long_range_variance": "main_fig4_long_range.json",
    "supplement_s1": "supp_fig_s1.json",
    "supplement_s3": "supp_fig_s3.json",
}


@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    condition_id: str
    family: str
    target_ids: tuple[str, ...]
    parameters: dict[str, Any]
    sample_start: int
    sample_count: int
    seed: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "condition_id": self.condition_id,
            "family": self.family,
            "target_ids": list(self.target_ids),
            "parameters": self.parameters,
            "sample_start": self.sample_start,
            "sample_count": self.sample_count,
            "seed": self.seed,
        }


@dataclass(frozen=True)
class CampaignPaths:
    data: Path
    figures: Path
    checks: Path
    shards: Path
    run_summary: Path
    manifest: Path


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("paper_id") != PAPER_ID:
        raise ValueError(f"expected paper_id {PAPER_ID}")
    return payload


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def implementation_sha256(workspace: Path) -> str:
    paths = [
        workspace / "src" / "dtc_feature_sim.py",
        workspace / "src" / "dtc_paper_scale.py",
        workspace / "scripts" / "run_paper_scale_all.py",
    ]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(workspace).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def expand_grid(spec: dict[str, Any]) -> list[float]:
    kind = spec["kind"]
    if kind == "linspace":
        values = np.linspace(
            float(spec["start"]), float(spec["stop"]), int(spec["count"])
        )
    elif kind == "geomspace":
        values = np.geomspace(
            float(spec["start"]), float(spec["stop"]), int(spec["count"])
        )
    else:
        raise ValueError(f"unsupported grid kind: {kind}")
    return [float(value) for value in values]


def build_work_units(config: dict[str, Any], profile: str = "paper") -> list[WorkUnit]:
    if profile not in {"paper", "smoke"}:
        raise ValueError("profile must be paper or smoke")
    smoke = config["smoke"]
    families = config["families"]
    seed_base = int(config["parameters"]["seed_base"])
    units: list[WorkUnit] = []

    def add_condition(
        family: str,
        target_ids: Iterable[str],
        parameters: dict[str, Any],
        samples: int,
        shard_size: int,
    ) -> None:
        effective_samples = 1 if profile == "smoke" else int(samples)
        effective_shard = 1 if profile == "smoke" else int(shard_size)
        condition_hash = canonical_sha256({"family": family, "parameters": parameters})[
            :16
        ]
        condition_id = f"{family}-{condition_hash}"
        condition_seed = seed_base ^ int(condition_hash, 16)
        for sample_start in range(0, effective_samples, effective_shard):
            sample_count = min(effective_shard, effective_samples - sample_start)
            units.append(
                WorkUnit(
                    unit_id=f"{condition_id}-s{sample_start:06d}",
                    condition_id=condition_id,
                    family=family,
                    target_ids=tuple(target_ids),
                    parameters=parameters,
                    sample_start=sample_start,
                    sample_count=sample_count,
                    seed=condition_seed,
                )
            )

    rigidity = families["rigidity"]
    rigidity_l = int(
        smoke["system_size"] if profile == "smoke" else rigidity["system_size"]
    )
    rigidity_steps = int(smoke["steps"] if profile == "smoke" else rigidity["steps"])
    rigidity_eps = _profile_grid(
        rigidity["epsilon_grid"], profile, smoke, anchors=[0.0, 0.1]
    )
    for j_z in rigidity["interaction_strengths"]:
        for epsilon in rigidity_eps:
            add_condition(
                "rigidity",
                rigidity["target_ids"],
                {
                    "system_size": rigidity_l,
                    "interaction_strength": float(j_z),
                    "epsilon": float(epsilon),
                    "steps": rigidity_steps,
                    "initial_state": rigidity["initial_state"],
                    "coupling_mode": "paper_narrow",
                    "field_mode": "random_uniform",
                    "fourier_window": config["parameters"]["fourier_window"],
                },
                rigidity["samples"],
                rigidity["sample_shard_size"],
            )

    level = families["level_statistics"]
    if profile == "smoke":
        level_specs = [
            ("main", 0.1, int(smoke["system_size"]), 0.1, "paper_narrow"),
            ("main", 0.1, int(smoke["system_size"]), 0.1, "paper_broad"),
            ("phase", 0.02, int(smoke["system_size"]), 0.1, "paper_narrow"),
            ("phase", 0.30, int(smoke["system_size"]), 0.2, "paper_narrow"),
        ]
        for purpose, epsilon, size, j_z, coupling_mode in level_specs:
            add_condition(
                "level_statistics",
                level["target_ids"],
                {
                    "purpose": purpose,
                    "epsilon": epsilon,
                    "system_size": size,
                    "interaction_strength": j_z,
                    "coupling_mode": coupling_mode,
                    "field_mode": "random_uniform",
                },
                1,
                1,
            )
    else:
        for purpose, block_name in (("main", "main_panel"), ("phase", "phase_map")):
            block = level[block_name]
            epsilons = block.get("epsilon_values") or expand_grid(block["epsilon_grid"])
            for coupling_mode in block["coupling_modes"]:
                for size in block["system_sizes"]:
                    for epsilon in epsilons:
                        for j_z in expand_grid(block["jz_grid"]):
                            add_condition(
                                "level_statistics",
                                level["target_ids"],
                                {
                                    "purpose": purpose,
                                    "epsilon": float(epsilon),
                                    "system_size": int(size),
                                    "interaction_strength": float(j_z),
                                    "coupling_mode": coupling_mode,
                                    "field_mode": "random_uniform",
                                },
                                int(block["samples_by_size"][str(size)]),
                                int(level["sample_shard_size"]),
                            )

    nearest = families["nearest_variance"]
    nearest_sizes = (
        [int(smoke["system_size"])] if profile == "smoke" else nearest["system_sizes"]
    )
    nearest_jz = (
        [0.03, 0.10] if profile == "smoke" else nearest["interaction_strengths"]
    )
    nearest_eps = _profile_grid(nearest["epsilon_grid"], profile, smoke)
    for size in nearest_sizes:
        samples = (
            1 if profile == "smoke" else int(nearest["samples_by_size"][str(size)])
        )
        for j_z in nearest_jz:
            for epsilon in nearest_eps:
                add_condition(
                    "nearest_variance",
                    nearest["target_ids"],
                    {
                        "system_size": int(size),
                        "interaction_strength": float(j_z),
                        "epsilon": float(epsilon),
                        "steps": int(
                            smoke["steps"] if profile == "smoke" else nearest["steps"]
                        ),
                        "initial_state": nearest["initial_state"],
                        "coupling_mode": "paper_narrow",
                        "field_mode": "random_uniform",
                        "fourier_window": config["parameters"]["fourier_window"],
                    },
                    samples,
                    nearest["sample_shard_size"],
                )

    mutual = families["mutual_information"]
    dense_sizes = (
        [int(smoke["system_size"])] if profile == "smoke" else mutual["system_sizes"]
    )
    for panel in mutual["panels"]:
        for size in dense_sizes:
            if profile == "smoke":
                epsilons = [0.0, float(panel["epsilon_c"]), 0.45]
                samples = 1
            else:
                epsilons = _mutual_information_epsilons(mutual, panel, int(size))
                samples = int(mutual["samples_by_size"][str(size)])
            for epsilon in epsilons:
                add_condition(
                    "mutual_information",
                    mutual["target_ids"],
                    {
                        "panel": panel["panel"],
                        "system_size": int(size),
                        "interaction_strength": float(panel["interaction_strength"]),
                        "epsilon": float(epsilon),
                        "epsilon_c": float(panel["epsilon_c"]),
                        "beta": float(panel["beta"]),
                        "nu": float(panel["nu"]),
                        "backend": "dense_full_spectrum",
                        "coupling_mode": "paper_narrow",
                        "field_mode": "random_uniform",
                    },
                    samples,
                    mutual["sample_shard_size"],
                )
    if profile == "paper":
        large = mutual["large_size_subset"]
        panel = next(
            row
            for row in mutual["panels"]
            if row["interaction_strength"] == large["interaction_strength"]
        )
        for size in large["system_sizes"]:
            for epsilon in _mutual_information_epsilons(mutual, panel, int(size)):
                add_condition(
                    "mutual_information",
                    mutual["target_ids"],
                    {
                        "panel": panel["panel"],
                        "system_size": int(size),
                        "interaction_strength": float(panel["interaction_strength"]),
                        "epsilon": float(epsilon),
                        "epsilon_c": float(panel["epsilon_c"]),
                        "beta": float(panel["beta"]),
                        "nu": float(panel["nu"]),
                        "backend": large["method"],
                        "eigenpairs": int(large["eigenpairs_per_realization"]),
                        "eigenphase_anchors": int(large["eigenphase_anchors"]),
                        "coupling_mode": "paper_narrow",
                        "field_mode": "random_uniform",
                    },
                    int(large["samples_by_size"][str(size)]),
                    int(large["sample_shard_size"]),
                )

    long_range = families["long_range_variance"]
    lr_size = int(
        smoke["system_size"] if profile == "smoke" else long_range["system_size"]
    )
    lr_jz = [0.03, 0.07] if profile == "smoke" else long_range["interaction_strengths"]
    lr_eps = _profile_grid(long_range["epsilon_grid"], profile, smoke)
    for j_z in lr_jz:
        for epsilon in lr_eps:
            add_condition(
                "long_range_variance",
                long_range["target_ids"],
                {
                    "system_size": lr_size,
                    "interaction_strength": float(j_z),
                    "epsilon": float(epsilon),
                    "steps": int(
                        smoke["steps"] if profile == "smoke" else long_range["steps"]
                    ),
                    "initial_state": long_range["initial_state"],
                    "alpha": float(long_range["alpha"]),
                    "coupling_mode": "fixed",
                    "field_mode": "random_uniform",
                    "fourier_window": config["parameters"]["fourier_window"],
                },
                long_range["samples"],
                long_range["sample_shard_size"],
            )

    supp1 = families["supplement_s1"]
    supp1_size = int(
        smoke["system_size"] if profile == "smoke" else supp1["system_size"]
    )
    for scenario in supp1["trace_scenarios"]:
        add_condition(
            "supplement_s1",
            supp1["target_ids"],
            {
                "mode": "trace",
                "scenario": scenario["scenario"],
                "system_size": supp1_size,
                "interaction_strength": float(scenario["interaction_strength"]),
                "epsilon": float(scenario["epsilon"]),
                "steps": int(
                    smoke["steps"] if profile == "smoke" else supp1["trace_steps"]
                ),
                "initial_state": "random_z",
                "coupling_mode": "paper_narrow",
                "field_mode": "random_uniform",
                "fourier_window": [0, int(supp1["trace_steps"])],
            },
            supp1["trace_samples"],
            supp1["sample_shard_size"],
        )
    washout_eps = (
        supp1["washout_epsilons"]
        if profile == "paper"
        else supp1["washout_epsilons"][:2]
    )
    for epsilon in washout_eps:
        add_condition(
            "supplement_s1",
            supp1["target_ids"],
            {
                "mode": "washout",
                "scenario": f"washout_eps_{float(epsilon):.3f}",
                "system_size": supp1_size,
                "interaction_strength": float(supp1["washout_interaction_strength"]),
                "epsilon": float(epsilon),
                "steps": int(
                    smoke["steps"] if profile == "smoke" else supp1["washout_steps"]
                ),
                "initial_state": "random_z",
                "coupling_mode": "paper_narrow",
                "field_mode": "random_uniform",
                "fourier_window": [10, int(supp1["washout_steps"])],
            },
            supp1["washout_samples"],
            supp1["sample_shard_size"],
        )
    susceptibility = supp1["susceptibility"]
    susceptibility_size = int(
        smoke["system_size"] if profile == "smoke" else susceptibility["system_size"]
    )
    susceptibility_eps = _profile_grid(susceptibility["epsilon_grid"], profile, smoke)
    susceptibility_jz = (
        susceptibility["interaction_strengths"]
        if profile == "paper"
        else susceptibility["interaction_strengths"]
    )
    for j_z in susceptibility_jz:
        for epsilon in susceptibility_eps:
            add_condition(
                "supplement_s1",
                supp1["target_ids"],
                {
                    "mode": "susceptibility",
                    "system_size": susceptibility_size,
                    "interaction_strength": float(j_z),
                    "epsilon": float(epsilon),
                    "eta": float(susceptibility["eta"]),
                    "protocol_interpretation": susceptibility[
                        "protocol_interpretation"
                    ],
                    "coupling_mode": "paper_narrow",
                    "field_mode": "random_uniform",
                },
                susceptibility["samples"],
                susceptibility["sample_shard_size"],
            )

    supp3 = families["supplement_s3"]
    supp3_size = int(
        smoke["system_size"] if profile == "smoke" else supp3["system_size"]
    )
    supp3_steps = int(smoke["steps"] if profile == "smoke" else supp3["steps"])
    for interaction_kind, fields in (
        ("nearest", supp3["nearest_uniform_fields"]),
        ("long_range", supp3["long_range_uniform_fields"]),
    ):
        for field_value in fields:
            add_condition(
                "supplement_s3",
                supp3["target_ids"],
                {
                    "interaction_kind": interaction_kind,
                    "system_size": supp3_size,
                    "interaction_strength": float(supp3["interaction_strength"]),
                    "epsilon": float(supp3["epsilon"]),
                    "steps": supp3_steps,
                    "field_mode": "uniform",
                    "field_value": float(field_value),
                    "coupling_mode": "fixed",
                    "alpha": (
                        float(supp3["alpha"])
                        if interaction_kind == "long_range"
                        else None
                    ),
                    "initial_state": "random_z",
                    "fourier_window": supp3["fourier_window"],
                },
                supp3["uniform_samples"],
                supp3["sample_shard_size"],
            )
        add_condition(
            "supplement_s3",
            supp3["target_ids"],
            {
                "interaction_kind": interaction_kind,
                "system_size": supp3_size,
                "interaction_strength": float(supp3["interaction_strength"]),
                "epsilon": float(supp3["epsilon"]),
                "steps": supp3_steps,
                "field_mode": "random_uniform",
                "field_value": None,
                "coupling_mode": (
                    "paper_narrow" if interaction_kind == "nearest" else "fixed"
                ),
                "alpha": (
                    float(supp3["alpha"]) if interaction_kind == "long_range" else None
                ),
                "initial_state": "random_z",
                "fourier_window": supp3["fourier_window"],
            },
            supp3["disorder_samples"],
            supp3["sample_shard_size"],
        )

    unit_ids = [unit.unit_id for unit in units]
    if len(unit_ids) != len(set(unit_ids)):
        raise ValueError("work-unit ids are not unique")
    return units


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    numeric_ids = config.get("numeric_item_ids", [])
    paper_units = build_work_units(config, "paper")
    smoke_units = build_work_units(config, "smoke")
    families = sorted({unit.family for unit in paper_units})
    findings: list[str] = []
    if len(numeric_ids) != 38 or len(set(numeric_ids)) != 38:
        findings.append("numeric_item_ids must contain exactly 38 unique entries")
    if set(families) != set(FAMILY_OUTPUTS):
        findings.append("not every numerical family has a work-unit implementation")
    disclosures = config.get("disclosures", {})
    for forbidden_flag in (
        "author_code_used",
        "author_numerical_arrays_used",
        "source_pixels_used_as_numerical_input",
        "source_figures_used_to_choose_scientific_parameters",
    ):
        if disclosures.get(forbidden_flag) is not False:
            findings.append(f"{forbidden_flag} must be false")
    return {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "status": "passed" if not findings else "failed",
        "numeric_items": len(numeric_ids),
        "families": families,
        "paper_work_units": len(paper_units),
        "paper_sample_realizations": sum(unit.sample_count for unit in paper_units),
        "smoke_work_units": len(smoke_units),
        "target_ids": sorted(
            {target for unit in paper_units for target in unit.target_ids}
        ),
        "findings": findings,
    }


def run_units(
    workspace: Path,
    config_path: Path,
    *,
    profile: str,
    workers: int = 1,
    unit_index: int | None = None,
    shard_index: int | None = None,
    shard_count: int | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    config = load_config(config_path)
    all_units = build_work_units(config, profile)
    selected = _select_units(
        all_units,
        unit_index=unit_index,
        shard_index=shard_index,
        shard_count=shard_count,
    )
    paths = _campaign_paths(workspace, config, profile)
    shard_dir = paths.shards
    shard_dir.mkdir(parents=True, exist_ok=True)
    config_hash = file_sha256(config_path)
    implementation_hash = implementation_sha256(workspace)
    ran: list[str] = []
    skipped: list[str] = []

    def run_one(unit: WorkUnit) -> tuple[str, str]:
        path = shard_dir / f"{unit.unit_id}.json"
        unit_hash = canonical_sha256(unit.as_dict())
        if resume and _valid_existing_shard(
            path, config_hash, implementation_hash, unit_hash
        ):
            return unit.unit_id, "skipped"
        result = execute_unit(unit, config["parameters"])
        payload = {
            "schema_version": 1,
            "status": "passed",
            "paper_id": PAPER_ID,
            "profile": profile,
            "unit": unit.as_dict(),
            "unit_sha256": unit_hash,
            "config_path": config_path.relative_to(workspace).as_posix(),
            "config_sha256": config_hash,
            "implementation_sha256": implementation_hash,
            "result": result,
        }
        _atomic_write_json(path, payload)
        return unit.unit_id, "ran"

    if workers <= 1:
        outcomes = [run_one(unit) for unit in selected]
    else:
        outcomes = []
        with ThreadPoolExecutor(max_workers=int(workers)) as executor:
            future_map = {
                executor.submit(run_one, unit): unit.unit_id for unit in selected
            }
            for future in as_completed(future_map):
                outcomes.append(future.result())
    for unit_id, disposition in sorted(outcomes):
        (ran if disposition == "ran" else skipped).append(unit_id)

    summary = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": PAPER_ID,
        "profile": profile,
        "work_units_total": len(all_units),
        "work_units_selected": len(selected),
        "work_units_ran": len(ran),
        "work_units_resumed": len(skipped),
        "unit_ids_ran": ran,
        "unit_ids_resumed": skipped,
        "config_sha256": config_hash,
        "implementation_sha256": implementation_hash,
        "paper_parameters_executed": profile == "paper"
        and len(selected) == len(all_units),
    }
    summary_path = paths.run_summary
    if unit_index is not None:
        summary_path = paths.checks / "run_summaries" / f"unit-{unit_index:06d}.json"
    elif shard_index is not None and shard_count is not None:
        summary_path = (
            paths.checks
            / "run_summaries"
            / f"shard-{shard_index:06d}-of-{shard_count:06d}.json"
        )
    summary["summary_path"] = summary_path.relative_to(workspace).as_posix()
    _atomic_write_json(summary_path, summary)
    return summary


def aggregate_units(
    workspace: Path,
    config_path: Path,
    *,
    profile: str,
    render: bool = True,
) -> dict[str, Any]:
    config = load_config(config_path)
    units = build_work_units(config, profile)
    paths = _campaign_paths(workspace, config, profile)
    shard_dir = paths.shards
    config_hash = file_sha256(config_path)
    implementation_hash = implementation_sha256(workspace)
    shards: list[dict[str, Any]] = []
    missing: list[str] = []
    invalid: list[str] = []
    for unit in units:
        path = shard_dir / f"{unit.unit_id}.json"
        if not path.is_file():
            missing.append(unit.unit_id)
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            invalid.append(unit.unit_id)
            continue
        if not _valid_shard_payload(
            payload,
            config_hash,
            implementation_hash,
            canonical_sha256(unit.as_dict()),
        ):
            invalid.append(unit.unit_id)
            continue
        shards.append(payload)
    if missing or invalid:
        raise RuntimeError(
            f"aggregation refused: missing={len(missing)} invalid={len(invalid)}"
        )

    data_dir = paths.data
    figures_dir = paths.figures
    checks_dir = paths.checks
    for directory in (data_dir, checks_dir):
        directory.mkdir(parents=True, exist_ok=True)
    if render:
        figures_dir.mkdir(parents=True, exist_ok=True)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for payload in shards:
        by_family[payload["unit"]["family"]].append(payload)
    aggregates: dict[str, dict[str, Any]] = {}
    output_hashes: dict[str, str] = {}
    for family, filename in FAMILY_OUTPUTS.items():
        rows = _aggregate_family(by_family[family])
        artifact = {
            "schema_version": 1,
            "status": "passed",
            "paper_id": PAPER_ID,
            "profile": profile,
            "family": family,
            "rows": rows,
        }
        path = data_dir / filename
        _atomic_write_json(path, artifact)
        output_hashes[path.relative_to(workspace).as_posix()] = file_sha256(path)
        aggregates[family] = artifact

    figure_paths = render_aggregates(aggregates, figures_dir) if render else []
    for path in figure_paths:
        output_hashes[path.relative_to(workspace).as_posix()] = file_sha256(path)
    acceptance = assess_aggregates(config, aggregates, profile)
    acceptance_path = checks_dir / "paper_scale_acceptance.json"
    _atomic_write_json(acceptance_path, acceptance)
    output_hashes[acceptance_path.relative_to(workspace).as_posix()] = file_sha256(
        acceptance_path
    )
    manifest = {
        "schema_version": 1,
        "status": "passed" if acceptance["status"] == "passed" else "failed",
        "paper_id": PAPER_ID,
        "profile": profile,
        "artifact_stage": "smoke" if profile == "smoke" else config["artifact_stage"],
        "paper_parameters_executed": profile == "paper",
        "config_sha256": config_hash,
        "implementation_sha256": implementation_hash,
        "work_units": len(units),
        "sample_realizations": sum(unit.sample_count for unit in units),
        "numeric_items_implemented": len(config["numeric_item_ids"]),
        "numeric_item_ids": config["numeric_item_ids"],
        "rendering_performed": render,
        "output_sha256": output_hashes,
        "scientific_input_boundary": {
            "author_code_used": false_value(),
            "author_numerical_arrays_used": false_value(),
            "source_pixels_used": false_value(),
            "raw_or_reference_paths_read": false_value(),
        },
    }
    manifest_path = paths.manifest
    _atomic_write_json(manifest_path, manifest)
    return manifest


def false_value() -> bool:
    """Make boundary flags explicit and easy to grep in generated manifests."""

    return False


def _sample_seed(unit: WorkUnit, offset: int) -> int:
    global_sample_index = unit.sample_start + int(offset)
    return int(
        canonical_sha256(
            {
                "condition_seed": unit.seed,
                "global_sample_index": global_sample_index,
            }
        )[:32],
        16,
    )


def _sample_rng(unit: WorkUnit, offset: int) -> np.random.Generator:
    """Return a shard-independent RNG for one global disorder realization."""

    return np.random.default_rng(_sample_seed(unit, offset))


def execute_unit(unit: WorkUnit, global_parameters: dict[str, Any]) -> dict[str, Any]:
    family = unit.family
    parameters = dict(unit.parameters)
    if family in {"rigidity", "nearest_variance", "long_range_variance"}:
        return _execute_trace_statistics(unit, global_parameters)
    if family == "level_statistics":
        return _execute_level_statistics(unit, global_parameters)
    if family == "mutual_information":
        return _execute_mutual_information(unit, global_parameters)
    if family == "supplement_s1":
        if parameters["mode"] == "susceptibility":
            return _execute_susceptibility(unit, global_parameters)
        return _execute_trace_statistics(unit, global_parameters)
    if family == "supplement_s3":
        return _execute_trace_statistics(unit, global_parameters)
    raise ValueError(f"unsupported family: {family}")


def _execute_trace_statistics(
    unit: WorkUnit, global_parameters: dict[str, Any]
) -> dict[str, Any]:
    parameters = unit.parameters
    trace_sum: np.ndarray | None = None
    raw_spectrum_sum: np.ndarray | None = None
    normalized_spectrum_sum: np.ndarray | None = None
    frequencies: np.ndarray | None = None
    peak_sum = 0.0
    peak_sq_sum = 0.0
    peak_location_sum = 0.0
    for offset in range(unit.sample_count):
        rng = _sample_rng(unit, offset)
        trace = autocorrelation_trace_custom(parameters, global_parameters, rng)
        fourier_window = parameters.get(
            "fourier_window", global_parameters["fourier_window"]
        )
        freq, raw, normalized = spectrum(trace, fourier_window)
        peak_location, peak_height = half_frequency_observables(trace, fourier_window)
        trace_sum = trace.copy() if trace_sum is None else trace_sum + trace
        raw_spectrum_sum = (
            raw.copy() if raw_spectrum_sum is None else raw_spectrum_sum + raw
        )
        normalized_spectrum_sum = (
            normalized.copy()
            if normalized_spectrum_sum is None
            else normalized_spectrum_sum + normalized
        )
        frequencies = freq
        peak_sum += peak_height
        peak_sq_sum += peak_height * peak_height
        peak_location_sum += peak_location
    assert trace_sum is not None and raw_spectrum_sum is not None
    assert normalized_spectrum_sum is not None and frequencies is not None
    return {
        "kind": "trace_statistics",
        "samples": unit.sample_count,
        "trace_sum": trace_sum.tolist(),
        "frequencies": frequencies.tolist(),
        "raw_spectrum_sum": raw_spectrum_sum.tolist(),
        "normalized_spectrum_sum": normalized_spectrum_sum.tolist(),
        "half_peak_sum": peak_sum,
        "half_peak_sq_sum": peak_sq_sum,
        "peak_location_sum": peak_location_sum,
    }


def _execute_level_statistics(
    unit: WorkUnit, global_parameters: dict[str, Any]
) -> dict[str, Any]:
    ratio_sum = 0.0
    for offset in range(unit.sample_count):
        ratio_sum += level_ratio_sample(
            unit.parameters,
            global_parameters,
            _sample_rng(unit, offset),
        )
    return {
        "kind": "level_statistics",
        "samples": unit.sample_count,
        "ratio_sum": ratio_sum,
    }


def _execute_mutual_information(
    unit: WorkUnit, global_parameters: dict[str, Any]
) -> dict[str, Any]:
    value_sum = 0.0
    backend = unit.parameters["backend"]
    for offset in range(unit.sample_count):
        rng = _sample_rng(unit, offset)
        if backend == "dense_full_spectrum":
            matrix = floquet_matrix_custom(unit.parameters, global_parameters, rng)
            _, vectors = np.linalg.eig(matrix)
            values = endpoint_mutual_information_from_eigenvectors(
                vectors, int(unit.parameters["system_size"])
            )
        elif backend == "matrix_free_phase_stratified_subset":
            values = matrix_free_endpoint_mutual_information(
                unit.parameters, global_parameters, rng
            )
        else:
            raise ValueError(f"unknown mutual-information backend: {backend}")
        value_sum += float(np.mean(values))
    return {
        "kind": "mutual_information",
        "samples": unit.sample_count,
        "mutual_information_sum": value_sum,
        "backend": backend,
    }


def _execute_susceptibility(
    unit: WorkUnit, global_parameters: dict[str, Any]
) -> dict[str, Any]:
    value_sum = 0.0
    for offset in range(unit.sample_count):
        value_sum += susceptibility_sample(
            unit.parameters,
            global_parameters,
            _sample_rng(unit, offset),
        )
    return {
        "kind": "susceptibility",
        "samples": unit.sample_count,
        "susceptibility_sum": value_sum,
    }


def autocorrelation_trace_custom(
    parameters: dict[str, Any],
    global_parameters: dict[str, Any],
    rng: np.random.Generator,
) -> np.ndarray:
    n_spins = int(parameters["system_size"])
    steps = int(parameters["steps"])
    zs = z_table(n_spins)
    couplings, fields = sample_model_parameters(parameters, global_parameters, rng)
    energy = diagonal_energy_custom(zs, couplings, fields, parameters.get("alpha"))
    phases = np.exp(-1j * energy)
    theta = float(global_parameters["pulse_angle_center"]) - float(
        parameters["epsilon"]
    )
    if parameters.get("initial_state") == "all_up":
        bits = np.zeros(n_spins, dtype=int)
    else:
        bits = rng.integers(0, 2, size=n_spins)
    index = int("".join(str(int(bit)) for bit in bits), 2)
    state = np.zeros(2**n_spins, dtype=np.complex128)
    state[index] = 1.0
    initial_z = 1 - 2 * bits
    trace = np.empty(steps, dtype=float)
    for step in range(steps):
        probabilities = np.abs(state) ** 2
        trace[step] = float(np.mean(initial_z * (probabilities @ zs)))
        state = phases * apply_x_rotation(state, theta, n_spins)
    return trace


def sample_model_parameters(
    parameters: dict[str, Any],
    global_parameters: dict[str, Any],
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    n_spins = int(parameters["system_size"])
    j_z = float(parameters["interaction_strength"])
    coupling_mode = parameters.get("coupling_mode", "paper_narrow")
    if coupling_mode == "paper_narrow":
        lo, hi = global_parameters["nearest_coupling_disorder_relative"]
        couplings = rng.uniform(float(lo) * j_z, float(hi) * j_z, size=n_spins - 1)
    elif coupling_mode == "paper_broad":
        couplings = rng.uniform(0.0, 2.0 * j_z, size=n_spins - 1)
    elif coupling_mode == "fixed":
        couplings = np.full(n_spins - 1, j_z, dtype=float)
    else:
        raise ValueError(f"unsupported coupling mode: {coupling_mode}")
    field_mode = parameters.get("field_mode", "random_uniform")
    if field_mode == "random_uniform":
        lo, hi = global_parameters["field_disorder"]
        fields = rng.uniform(float(lo), float(hi), size=n_spins)
    elif field_mode == "uniform":
        fields = np.full(n_spins, float(parameters["field_value"]), dtype=float)
    else:
        raise ValueError(f"unsupported field mode: {field_mode}")
    return couplings, fields


def diagonal_energy_custom(
    zs: np.ndarray,
    couplings: np.ndarray,
    fields: np.ndarray,
    alpha: float | None,
) -> np.ndarray:
    energy = zs @ fields
    if alpha is None:
        if len(couplings):
            energy = energy + (zs[:, :-1] * zs[:, 1:]) @ couplings
        return energy
    j_z = float(couplings[0]) if len(couplings) else 0.0
    for left in range(zs.shape[1]):
        for right in range(left + 1, zs.shape[1]):
            energy = energy + j_z * zs[:, left] * zs[:, right] / (
                (right - left) ** float(alpha)
            )
    return energy


def floquet_matrix_custom(
    parameters: dict[str, Any],
    global_parameters: dict[str, Any],
    rng: np.random.Generator,
) -> np.ndarray:
    n_spins = int(parameters["system_size"])
    zs = z_table(n_spins)
    couplings, fields = sample_model_parameters(parameters, global_parameters, rng)
    phases = np.exp(
        -1j * diagonal_energy_custom(zs, couplings, fields, parameters.get("alpha"))
    )
    rotation = rx_product_matrix(
        n_spins,
        float(global_parameters["pulse_angle_center"]) - float(parameters["epsilon"]),
    )
    return phases[:, None] * rotation


def level_ratio_sample(
    parameters: dict[str, Any],
    global_parameters: dict[str, Any],
    rng: np.random.Generator,
) -> float:
    eigenvalues = np.linalg.eigvals(
        floquet_matrix_custom(parameters, global_parameters, rng)
    )
    angles = np.sort(np.mod(np.angle(eigenvalues), 2 * np.pi))
    gaps = np.diff(np.r_[angles, angles[0] + 2 * np.pi])
    adjacent = np.roll(gaps, -1)
    denominator = np.maximum(gaps, adjacent)
    ratios = np.divide(
        np.minimum(gaps, adjacent),
        denominator,
        out=np.zeros_like(gaps),
        where=denominator > 0,
    )
    return float(np.mean(ratios))


def matrix_free_endpoint_mutual_information(
    parameters: dict[str, Any],
    global_parameters: dict[str, Any],
    rng: np.random.Generator,
) -> np.ndarray:
    from scipy.sparse.linalg import LinearOperator, eigsh

    n_spins = int(parameters["system_size"])
    dimension = 2**n_spins
    couplings, fields = sample_model_parameters(parameters, global_parameters, rng)
    phases = np.exp(
        -1j
        * diagonal_energy_custom(
            z_table(n_spins),
            couplings,
            fields,
            parameters.get("alpha"),
        )
    )
    theta = float(global_parameters["pulse_angle_center"]) - float(
        parameters["epsilon"]
    )

    def matvec(vector: np.ndarray) -> np.ndarray:
        return phases * apply_x_rotation(
            np.asarray(vector, dtype=np.complex128), theta, n_spins
        )

    def rmatvec(vector: np.ndarray) -> np.ndarray:
        phased = np.conj(phases) * np.asarray(vector, dtype=np.complex128)
        return apply_x_rotation(phased, -theta, n_spins)

    eigenpairs = min(int(parameters["eigenpairs"]), dimension - 2)
    anchors = int(parameters["eigenphase_anchors"])
    if anchors <= 0:
        raise ValueError("eigenphase_anchors must be positive")
    per_anchor = max(1, int(np.ceil(eigenpairs / anchors)))
    values: list[np.ndarray] = []
    for phi in np.linspace(0.0, 2.0 * np.pi, anchors, endpoint=False):
        phase = np.exp(-1j * phi)

        def hermitian_matvec(vector: np.ndarray, phase: complex = phase) -> np.ndarray:
            source = np.asarray(vector, dtype=np.complex128)
            return 0.5 * (phase * matvec(source) + np.conj(phase) * rmatvec(source))

        hermitian = LinearOperator(
            (dimension, dimension),
            matvec=hermitian_matvec,
            rmatvec=hermitian_matvec,
            dtype=np.complex128,
        )
        _, vectors = eigsh(
            hermitian,
            k=min(per_anchor, dimension - 2),
            which="LA",
            tol=1e-9,
            maxiter=max(5000, dimension // 2),
        )
        values.append(endpoint_mutual_information_from_eigenvectors(vectors, n_spins))
    return np.concatenate(values)[:eigenpairs]


def susceptibility_sample(
    parameters: dict[str, Any],
    global_parameters: dict[str, Any],
    rng: np.random.Generator,
) -> float:
    n_spins = int(parameters["system_size"])
    zs = z_table(n_spins)
    couplings, fields = sample_model_parameters(parameters, global_parameters, rng)
    theta = float(global_parameters["pulse_angle_center"]) - float(
        parameters["epsilon"]
    )
    rotation = rx_product_matrix(n_spins, theta)
    base_energy = diagonal_energy_custom(zs, couplings, fields, None)
    one_period = np.exp(-1j * base_energy)[:, None] * rotation
    eta = float(parameters["eta"])
    magnetization = np.sum(zs, axis=1)
    plus = np.exp(-1j * (base_energy + eta * magnetization))[:, None] * rotation
    minus = np.exp(-1j * (base_energy - eta * magnetization))[:, None] * rotation
    unperturbed_two_period = one_period @ one_period
    alternating_two_period = minus @ plus
    _, eigenvectors = np.linalg.eig(one_period)
    local_z = zs[:, n_spins // 2].astype(float)

    def eigenstate_correlations(evolution: np.ndarray) -> np.ndarray:
        evolved = evolution @ eigenvectors
        evolved_after_z = evolution @ (local_z[:, None] * eigenvectors)
        return np.sum(np.conj(evolved) * local_z[:, None] * evolved_after_z, axis=0)

    original = eigenstate_correlations(unperturbed_two_period)
    doubled = eigenstate_correlations(alternating_two_period)
    return float(np.mean(np.abs(doubled - original)))


def spectrum(
    trace: np.ndarray, window: list[int]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    start = min(int(window[0]), max(0, len(trace) // 4))
    stop = min(int(window[1]), len(trace))
    if stop - start < 4:
        start, stop = 0, len(trace)
    values = np.asarray(trace[start:stop], dtype=float)
    values = values - np.mean(values)
    raw = np.abs(np.fft.rfft(values)) / max(1, len(values))
    normalized = raw / np.max(raw) if np.max(raw) > 0 else raw.copy()
    return np.fft.rfftfreq(len(values), d=1.0), raw, normalized


def half_frequency_observables(
    trace: np.ndarray, window: list[int]
) -> tuple[float, float]:
    frequencies, raw, _ = spectrum(trace, window)
    search = np.where((frequencies >= 0.25) & (frequencies <= 0.5))[0]
    peak_index = int(search[np.argmax(raw[search])])
    start = min(int(window[0]), max(0, len(trace) // 4))
    stop = min(int(window[1]), len(trace))
    if stop - start < 4:
        start, stop = 0, len(trace)
    times = np.arange(start, stop)
    half_height = abs(np.mean(np.asarray(trace[start:stop]) * ((-1.0) ** times)))
    return float(frequencies[peak_index]), float(half_height)


def _aggregate_family(shards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for shard in shards:
        grouped[shard["unit"]["condition_id"]].append(shard)
    rows: list[dict[str, Any]] = []
    for condition_id, group in sorted(grouped.items()):
        first = group[0]
        kind = first["result"]["kind"]
        samples = sum(int(shard["result"]["samples"]) for shard in group)
        row = {
            "condition_id": condition_id,
            **first["unit"]["parameters"],
            "samples": samples,
        }
        if kind == "trace_statistics":
            trace_sum = _sum_arrays(group, "trace_sum")
            raw_sum = _sum_arrays(group, "raw_spectrum_sum")
            norm_sum = _sum_arrays(group, "normalized_spectrum_sum")
            row.update(
                {
                    "trace": (trace_sum / samples).tolist(),
                    "frequencies": first["result"]["frequencies"],
                    "raw_spectrum": (raw_sum / samples).tolist(),
                    "normalized_spectrum": (norm_sum / samples).tolist(),
                    "half_peak_mean": sum(
                        float(s["result"]["half_peak_sum"]) for s in group
                    )
                    / samples,
                    "half_peak_variance": max(
                        0.0,
                        sum(float(s["result"]["half_peak_sq_sum"]) for s in group)
                        / samples
                        - (
                            sum(float(s["result"]["half_peak_sum"]) for s in group)
                            / samples
                        )
                        ** 2,
                    ),
                    "peak_location_mean": sum(
                        float(s["result"]["peak_location_sum"]) for s in group
                    )
                    / samples,
                }
            )
        elif kind == "level_statistics":
            row["level_ratio_mean"] = (
                sum(float(s["result"]["ratio_sum"]) for s in group) / samples
            )
        elif kind == "mutual_information":
            row["endpoint_mutual_information"] = (
                sum(float(s["result"]["mutual_information_sum"]) for s in group)
                / samples
            )
            row["scaling_x"] = (float(row["epsilon"]) - float(row["epsilon_c"])) * (
                int(row["system_size"]) ** (1.0 / float(row["nu"]))
            )
            row["scaling_y"] = (int(row["system_size"]) ** float(row["beta"])) * float(
                row["endpoint_mutual_information"]
            )
        elif kind == "susceptibility":
            row["susceptibility"] = (
                sum(float(s["result"]["susceptibility_sum"]) for s in group) / samples
            )
        else:
            raise ValueError(f"unsupported result kind: {kind}")
        rows.append(row)
    return rows


def _sum_arrays(group: list[dict[str, Any]], key: str) -> np.ndarray:
    arrays = [np.asarray(shard["result"][key], dtype=float) for shard in group]
    lengths = {len(array) for array in arrays}
    if len(lengths) != 1:
        raise ValueError(f"incompatible shard arrays for {key}")
    return np.sum(np.stack(arrays), axis=0)


def assess_aggregates(
    config: dict[str, Any],
    aggregates: dict[str, dict[str, Any]],
    profile: str,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    feature_checks: list[dict[str, Any]] = []
    limits = config["acceptance"]
    for family, artifact in aggregates.items():
        if not artifact["rows"]:
            findings.append({"family": family, "code": "empty_family"})
        for row in artifact["rows"]:
            for key, value in row.items():
                if isinstance(value, float) and not np.isfinite(value):
                    findings.append(
                        {
                            "family": family,
                            "condition_id": row["condition_id"],
                            "code": "nonfinite",
                        }
                    )
            if "trace" in row and np.max(np.abs(row["trace"])) > float(
                limits["trace_absolute_bound"]
            ):
                findings.append(
                    {
                        "family": family,
                        "condition_id": row["condition_id"],
                        "code": "trace_bound",
                    }
                )
            if "level_ratio_mean" in row:
                lo, hi = limits["level_ratio_bounds"]
                if not float(lo) <= float(row["level_ratio_mean"]) <= float(hi):
                    findings.append(
                        {
                            "family": family,
                            "condition_id": row["condition_id"],
                            "code": "level_ratio_bound",
                        }
                    )
            if "endpoint_mutual_information" in row:
                lo, hi = limits["mutual_information_bounds"]
                if (
                    not float(lo) - 1e-9
                    <= float(row["endpoint_mutual_information"])
                    <= float(hi) + 1e-9
                ):
                    findings.append(
                        {
                            "family": family,
                            "condition_id": row["condition_id"],
                            "code": "mi_bound",
                        }
                    )
            if (
                "half_peak_variance" in row
                and float(row["half_peak_variance"]) < -1e-12
            ):
                findings.append(
                    {
                        "family": family,
                        "condition_id": row["condition_id"],
                        "code": "negative_variance",
                    }
                )
    if profile == "paper":
        feature_checks = _assess_paper_features(config, aggregates)
        findings.extend(
            {
                "family": check["family"],
                "code": check["check_id"],
                "actual": check["actual"],
                "criterion": check["criterion"],
                "threshold": check["threshold"],
            }
            for check in feature_checks
            if check["status"] != "passed"
        )
    return {
        "schema_version": 1,
        "status": "passed" if not findings else "failed",
        "paper_id": PAPER_ID,
        "profile": profile,
        "artifact_stage": "smoke" if profile == "smoke" else config["artifact_stage"],
        "paper_parameters_executed": profile == "paper",
        "families_checked": sorted(aggregates),
        "numeric_items_implemented": len(config["numeric_item_ids"]),
        "paper_feature_checks_applicable": profile == "paper",
        "paper_feature_checks": feature_checks,
        "paper_error_candidate_emitted": False,
        "findings": findings,
        "interpretation": "Execution and invariant checks cannot by themselves label a paper error; protocol-v2 fresh-context review remains mandatory.",
    }


def _assess_paper_features(
    config: dict[str, Any], aggregates: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    thresholds = config["acceptance"]["paper_feature_checks"]
    rigidity = aggregates["rigidity"]["rows"]
    level = aggregates["level_statistics"]["rows"]
    nearest = aggregates["nearest_variance"]["rows"]
    mutual = aggregates["mutual_information"]["rows"]
    long_range = aggregates["long_range_variance"]["rows"]
    supp1 = aggregates["supplement_s1"]["rows"]
    supp3 = aggregates["supplement_s3"]["rows"]
    checks: list[dict[str, Any]] = []

    free_errors = [
        abs(
            float(row["peak_location_mean"])
            - (0.5 - abs(float(row["epsilon"])) / np.pi)
        )
        for row in rigidity
        if float(row["interaction_strength"]) == 0.0
    ]
    checks.append(
        _maximum_check(
            "rigidity_free_peak_formula",
            "rigidity",
            free_errors,
            float(thresholds["free_peak_max_absolute_error"]),
        )
    )

    rigid_errors = [
        abs(float(row["peak_location_mean"]) - 0.5)
        for row in rigidity
        if float(row["interaction_strength"]) > 0.0
        and abs(float(row["epsilon"]))
        <= float(thresholds["rigid_epsilon_absolute_max"])
    ]
    checks.append(
        _maximum_check(
            "rigidity_interacting_peak_lock",
            "rigidity",
            rigid_errors,
            float(thresholds["rigid_peak_max_absolute_error"]),
        )
    )

    main_level = [
        row
        for row in level
        if row["purpose"] == "main" and row["coupling_mode"] == "paper_narrow"
    ]
    level_spans = [
        max(float(row["level_ratio_mean"]) for row in group)
        - min(float(row["level_ratio_mean"]) for row in group)
        for group in _group_rows(main_level, "system_size").values()
    ]
    checks.append(
        _minimum_check(
            "level_statistics_resolves_crossover",
            "level_statistics",
            level_spans,
            float(thresholds["minimum_level_ratio_span"]),
        )
    )

    checks.append(
        _minimum_check(
            "nearest_variance_has_transition_peak",
            "nearest_variance",
            _variance_prominences(nearest),
            float(thresholds["minimum_variance_peak_prominence"]),
        )
    )
    checks.append(
        _minimum_check(
            "long_range_variance_has_transition_peak",
            "long_range_variance",
            _variance_prominences(long_range),
            float(thresholds["minimum_variance_peak_prominence"]),
        )
    )

    ordered: list[float] = []
    trivial: list[float] = []
    drops: list[float] = []
    for group in _group_rows_multi(mutual, ("panel", "system_size")).values():
        ordered_row = min(group, key=lambda row: abs(float(row["epsilon"])))
        trivial_row = min(group, key=lambda row: abs(float(row["epsilon"]) - 0.45))
        ordered_value = float(ordered_row["endpoint_mutual_information"])
        trivial_value = float(trivial_row["endpoint_mutual_information"])
        ordered.append(ordered_value)
        trivial.append(trivial_value)
        drops.append(ordered_value - trivial_value)
    checks.append(
        _minimum_check(
            "mutual_information_ordered_limit",
            "mutual_information",
            ordered,
            float(thresholds["ordered_mutual_information_minimum"]),
        )
    )
    checks.append(
        _maximum_check(
            "mutual_information_trivial_limit",
            "mutual_information",
            trivial,
            float(thresholds["trivial_mutual_information_maximum"]),
        )
    )
    checks.append(
        _minimum_check(
            "mutual_information_finite_size_drop",
            "mutual_information",
            drops,
            float(thresholds["minimum_mutual_information_drop"]),
        )
    )

    susceptibility = [row for row in supp1 if row["mode"] == "susceptibility"]
    susceptibility_spans = [
        max(float(row["susceptibility"]) for row in group)
        - min(float(row["susceptibility"]) for row in group)
        for group in _group_rows(susceptibility, "interaction_strength").values()
    ]
    checks.append(
        _minimum_check(
            "susceptibility_resolves_epsilon_dependence",
            "supplement_s1",
            susceptibility_spans,
            float(thresholds["minimum_susceptibility_span"]),
        )
    )

    disordered_s3_errors = [
        abs(float(row["peak_location_mean"]) - 0.5)
        for row in supp3
        if row["field_mode"] == "random_uniform"
    ]
    checks.append(
        _maximum_check(
            "supplement_s3_disordered_subharmonic_peak",
            "supplement_s3",
            disordered_s3_errors,
            float(thresholds["s3_disordered_peak_max_absolute_error"]),
        )
    )
    return checks


def _variance_prominences(rows: list[dict[str, Any]]) -> list[float]:
    return [
        max(float(row["half_peak_variance"]) for row in group)
        - min(float(row["half_peak_variance"]) for row in group)
        for group in _group_rows_multi(
            rows, ("system_size", "interaction_strength")
        ).values()
    ]


def _minimum_check(
    check_id: str, family: str, values: list[float], threshold: float
) -> dict[str, Any]:
    actual = min(values) if values else None
    return _feature_check(
        check_id,
        family,
        actual,
        "minimum",
        threshold,
        actual is not None and np.isfinite(actual) and actual >= threshold,
    )


def _maximum_check(
    check_id: str, family: str, values: list[float], threshold: float
) -> dict[str, Any]:
    actual = max(values) if values else None
    return _feature_check(
        check_id,
        family,
        actual,
        "maximum",
        threshold,
        actual is not None and np.isfinite(actual) and actual <= threshold,
    )


def _feature_check(
    check_id: str,
    family: str,
    actual: float | None,
    criterion: str,
    threshold: float,
    passed: bool,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "family": family,
        "status": "passed" if passed else "failed",
        "actual": actual,
        "criterion": criterion,
        "threshold": threshold,
    }


def render_aggregates(
    aggregates: dict[str, dict[str, Any]],
    figures_dir: Path,
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    figures_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    rigidity = aggregates["rigidity"]["rows"]
    level = aggregates["level_statistics"]["rows"]
    nearest = aggregates["nearest_variance"]["rows"]
    mutual = aggregates["mutual_information"]["rows"]
    long_range = aggregates["long_range_variance"]["rows"]
    supp1 = aggregates["supplement_s1"]["rows"]
    supp3 = aggregates["supplement_s3"]["rows"]

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    _plot_phase_diagram(
        axes[0, 0], level, nearest, title="Main Fig. 1(a) reconstructed diagnostics"
    )
    for j_z, group in _group_rows(rigidity, "interaction_strength").items():
        rows = sorted(group, key=lambda row: row["epsilon"])
        axes[0, 1].plot(
            [r["epsilon"] for r in rows],
            [r["peak_location_mean"] for r in rows],
            "o-",
            label=f"Jz={j_z:g}",
        )
    axes[0, 1].set(xlabel="epsilon", ylabel="peak frequency", title="Main Fig. 1(b)")
    axes[0, 1].legend()
    _plot_spectra(
        axes[1, 0],
        [row for row in rigidity if float(row["interaction_strength"]) == 0.0],
        normalized=True,
        title="Main Fig. 1(c)",
    )
    _plot_spectra(
        axes[1, 1],
        [row for row in rigidity if float(row["interaction_strength"]) > 0.0],
        normalized=True,
        title="Main Fig. 1(d)",
    )
    paths.append(_save(fig, figures_dir / "main_fig1.png"))

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for coupling_mode, group in _group_rows(
        [r for r in level if r["purpose"] == "main"], "coupling_mode"
    ).items():
        target_ax = axes[0] if coupling_mode == "paper_narrow" else axes[1]
        for size, size_group in _group_rows(group, "system_size").items():
            rows = sorted(size_group, key=lambda row: row["interaction_strength"])
            target_ax.semilogx(
                [r["interaction_strength"] for r in rows],
                [r["level_ratio_mean"] for r in rows],
                "o-",
                label=f"L={size}",
            )
        target_ax.set(
            xlabel="Jz", ylabel="<r>", title=f"Main Fig. 2(a): {coupling_mode}"
        )
        target_ax.legend(fontsize=8)
    _plot_variance_curves(axes[2], nearest, "Main Fig. 2(b)")
    paths.append(_save(fig, figures_dir / "main_fig2.png"))

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for panel, group in _group_rows(mutual, "panel").items():
        for size, size_group in _group_rows(group, "system_size").items():
            rows = sorted(size_group, key=lambda row: row["epsilon"])
            axes[0, 0].plot(
                [r["epsilon"] for r in rows],
                [r["endpoint_mutual_information"] for r in rows],
                "o-",
                ms=3,
                label=f"{panel}, L={size}",
            )
    axes[0, 0].set(xlabel="epsilon", ylabel="I(endpoints)", title="Main Fig. 3(a)")
    axes[0, 0].legend(fontsize=6, ncol=2)
    for axis, panel in zip(
        (axes[0, 1], axes[1, 0], axes[1, 1]), ("Fig. 3b", "Fig. 3c", "Fig. 3d")
    ):
        group = [row for row in mutual if row["panel"] == panel]
        _plot_collapse(axis, group, panel, inset_axes)
    paths.append(_save(fig, figures_dir / "main_fig3.png"))

    fig, axis = plt.subplots(figsize=(7, 5))
    _plot_variance_curves(axis, long_range, "Main Fig. 4 numeric regions")
    inset = inset_axes(axis, width="38%", height="38%", loc="upper left")
    _plot_variance_boundaries(inset, long_range)
    inset.set_title("phase proxy", fontsize=8)
    paths.append(_save(fig, figures_dir / "main_fig4.png"))

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for row in [row for row in supp1 if row["mode"] == "trace"]:
        axes[0].plot(row["trace"], label=row["scenario"])
    axes[0].set(xlabel="period", ylabel="R(t)", title="Supplement Fig. S1(a)")
    axes[0].legend(fontsize=7)
    _plot_spectra(
        axes[1],
        [row for row in supp1 if row["mode"] == "washout"],
        normalized=False,
        title="Supplement Fig. S1(b)",
    )
    for j_z, group in _group_rows(
        [row for row in supp1 if row["mode"] == "susceptibility"],
        "interaction_strength",
    ).items():
        rows = sorted(group, key=lambda row: row["epsilon"])
        axes[2].semilogx(
            [r["epsilon"] for r in rows],
            [r["susceptibility"] for r in rows],
            "o-",
            label=f"Jz={j_z:g}",
        )
    axes[2].set(xlabel="epsilon", ylabel="chi", title="Supplement Fig. S1(c)")
    axes[2].legend(fontsize=7)
    paths.append(_save(fig, figures_dir / "supp_fig_s1.png"))

    fig, axes = plt.subplots(3, 3, figsize=(13, 11))
    for row_index, panel in enumerate(("Fig. 3b", "Fig. 3c", "Fig. 3d")):
        group = [row for row in mutual if row["panel"] == panel]
        for size, size_group in _group_rows(group, "system_size").items():
            rows = sorted(size_group, key=lambda row: row["epsilon"])
            axes[row_index, 0].plot(
                [r["epsilon"] for r in rows],
                [r["endpoint_mutual_information"] for r in rows],
                "o-",
                ms=3,
                label=f"L={size}",
            )
            axes[row_index, 1].plot(
                [r["scaling_x"] for r in rows],
                [r["scaling_y"] for r in rows],
                "o-",
                ms=3,
            )
            axes[row_index, 2].semilogy(
                [r["scaling_x"] for r in rows],
                np.maximum([r["scaling_y"] for r in rows], 1e-12),
                "o-",
                ms=3,
            )
        axes[row_index, 0].set_title(f"{panel}: raw")
        axes[row_index, 1].set_title(f"{panel}: collapse")
        axes[row_index, 2].set_title(f"{panel}: log collapse")
    axes[0, 0].legend(fontsize=7)
    paths.append(_save(fig, figures_dir / "supp_fig_s2.png"))

    fig, axes = plt.subplots(2, 5, figsize=(18, 7), sharex=True)
    for row_index, interaction_kind in enumerate(("nearest", "long_range")):
        rows = [row for row in supp3 if row["interaction_kind"] == interaction_kind]
        rows.sort(
            key=lambda row: (
                row["field_mode"] == "random_uniform",
                row.get("field_value") or 0.0,
            )
        )
        for axis, row in zip(axes[row_index], rows):
            axis.plot(row["frequencies"], row["raw_spectrum"])
            label = (
                "disorder"
                if row["field_mode"] == "random_uniform"
                else f"hz={row['field_value']:g}"
            )
            axis.set_title(f"{interaction_kind}\n{label}", fontsize=9)
            axis.set_xlabel("frequency")
    axes[0, 0].set_ylabel("FFT")
    axes[1, 0].set_ylabel("FFT")
    paths.append(_save(fig, figures_dir / "supp_fig_s3.png"))
    return paths


def _plot_phase_diagram(
    axis: Any, level: list[dict[str, Any]], nearest: list[dict[str, Any]], title: str
) -> None:
    _plot_variance_boundaries(axis, nearest)
    phase_rows = [
        row
        for row in level
        if row["purpose"] == "phase" and row["coupling_mode"] == "paper_narrow"
    ]
    by_epsilon = _group_rows(phase_rows, "epsilon")
    thermal_points = []
    for epsilon, group in by_epsilon.items():
        by_jz = _group_rows(group, "interaction_strength")
        candidates = []
        for j_z, rows in by_jz.items():
            values = [r["level_ratio_mean"] for r in rows]
            if len(values) >= 2:
                candidates.append((float(np.var(values)), float(j_z)))
        if candidates:
            thermal_points.append((min(candidates)[1], float(epsilon)))
    if thermal_points:
        axis.plot(
            [p[0] for p in thermal_points],
            [p[1] for p in thermal_points],
            "s--",
            label="level-statistics boundary",
        )
    axis.set(xlabel="Jz", ylabel="epsilon", title=title)
    axis.legend(fontsize=7)


def _plot_variance_boundaries(axis: Any, rows: list[dict[str, Any]]) -> None:
    by_jz = _group_rows(rows, "interaction_strength")
    points = []
    for j_z, group in by_jz.items():
        max_size = max(int(row["system_size"]) for row in group)
        size_rows = [row for row in group if int(row["system_size"]) == max_size]
        if size_rows:
            peak = max(size_rows, key=lambda row: float(row["half_peak_variance"]))
            points.append((float(j_z), float(peak["epsilon"])))
    points.sort()
    if points:
        axis.plot(
            [p[0] for p in points],
            [p[1] for p in points],
            "o-",
            label="variance-peak boundary",
        )


def _plot_variance_curves(axis: Any, rows: list[dict[str, Any]], title: str) -> None:
    for (size, j_z), group in _group_rows_multi(
        rows, ("system_size", "interaction_strength")
    ).items():
        ordered = sorted(group, key=lambda row: row["epsilon"])
        axis.semilogx(
            [r["epsilon"] for r in ordered],
            [r["half_peak_variance"] for r in ordered],
            "o-",
            ms=3,
            label=f"L={size}, Jz={j_z:g}",
        )
    axis.set(xlabel="epsilon", ylabel="Var(h)", title=title)
    axis.legend(fontsize=6, ncol=2)


def _plot_spectra(
    axis: Any, rows: list[dict[str, Any]], *, normalized: bool, title: str
) -> None:
    key = "normalized_spectrum" if normalized else "raw_spectrum"
    for row in sorted(rows, key=lambda item: item["epsilon"]):
        axis.plot(row["frequencies"], row[key], label=f"eps={row['epsilon']:.3g}")
    axis.set(xlabel="frequency", ylabel="FFT", title=title)
    if rows:
        axis.legend(fontsize=6)


def _plot_collapse(
    axis: Any, rows: list[dict[str, Any]], panel: str, inset_axes: Any
) -> None:
    for size, group in _group_rows(rows, "system_size").items():
        ordered = sorted(group, key=lambda row: row["scaling_x"])
        axis.plot(
            [r["scaling_x"] for r in ordered],
            [r["scaling_y"] for r in ordered],
            "o-",
            ms=3,
            label=f"L={size}",
        )
    axis.set(xlabel="(epsilon-ec)L^(1/nu)", ylabel="L^beta I", title=panel)
    axis.legend(fontsize=6)
    inset = inset_axes(axis, width="45%", height="42%", loc="upper right")
    for size, group in _group_rows(rows, "system_size").items():
        ordered = sorted(group, key=lambda row: row["scaling_x"])
        inset.semilogy(
            [r["scaling_x"] for r in ordered],
            np.maximum([r["scaling_y"] for r in ordered], 1e-12),
            "o-",
            ms=2,
        )
    inset.tick_params(labelsize=6)


def _save(figure: Any, path: Path) -> Path:
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    import matplotlib.pyplot as plt

    plt.close(figure)
    return path


def _group_rows(
    rows: list[dict[str, Any]], key: str
) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return dict(grouped)


def _group_rows_multi(
    rows: list[dict[str, Any]], keys: tuple[str, ...]
) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return dict(grouped)


def _profile_grid(
    spec: dict[str, Any],
    profile: str,
    smoke: dict[str, Any],
    anchors: list[float] | None = None,
) -> list[float]:
    if profile == "paper":
        return expand_grid(spec)
    anchors = anchors or [float(spec["start"]), float(spec["stop"])]
    count = int(smoke["grid_points_per_axis"])
    return [float(value) for value in anchors[:count]]


def _mutual_information_epsilons(
    mutual: dict[str, Any], panel: dict[str, Any], system_size: int
) -> list[float]:
    epsilon_c = float(panel["epsilon_c"])
    nu = float(panel["nu"])
    values = [
        epsilon_c + float(x) / (system_size ** (1.0 / nu))
        for x in mutual["scaled_x_grid"]
    ]
    values.extend(float(value) for value in mutual["epsilon_anchors"])
    return sorted({round(min(0.8, max(0.0, value)), 12) for value in values})


def _select_units(
    units: list[WorkUnit],
    *,
    unit_index: int | None,
    shard_index: int | None,
    shard_count: int | None,
) -> list[WorkUnit]:
    if unit_index is not None:
        if unit_index < 0 or unit_index >= len(units):
            raise ValueError("unit_index out of range")
        return [units[unit_index]]
    if shard_index is None and shard_count is None:
        return units
    if (
        shard_index is None
        or shard_count is None
        or shard_count <= 0
        or not 0 <= shard_index < shard_count
    ):
        raise ValueError("shard_index/shard_count must define a valid zero-based shard")
    return [
        unit for index, unit in enumerate(units) if index % shard_count == shard_index
    ]


def _campaign_paths(
    workspace: Path, config: dict[str, Any], profile: str
) -> CampaignPaths:
    namespace = str(config["execution"]["artifact_namespace"])
    if profile == "smoke":
        namespace = f"{namespace}_smoke"
    data = workspace / "outputs" / "data" / namespace
    figures = workspace / "outputs" / "figures" / namespace
    checks = workspace / "outputs" / "checks" / namespace
    return CampaignPaths(
        data=data,
        figures=figures,
        checks=checks,
        shards=data / "shards",
        run_summary=checks / "run_summary.json",
        manifest=checks / "manifest.json",
    )


def _valid_existing_shard(
    path: Path, config_hash: str, implementation_hash: str, unit_hash: str
) -> bool:
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return _valid_shard_payload(payload, config_hash, implementation_hash, unit_hash)


def _valid_shard_payload(
    payload: dict[str, Any], config_hash: str, implementation_hash: str, unit_hash: str
) -> bool:
    return (
        payload.get("status") == "passed"
        and payload.get("config_sha256") == config_hash
        and payload.get("implementation_sha256") == implementation_hash
        and payload.get("unit_sha256") == unit_hash
    )


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)
