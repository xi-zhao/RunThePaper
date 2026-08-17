"""Shardable all-target campaign for arXiv:1508.03344."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .analytic import PHASE_TO_CODE, free_phase_map
from .model import (
    floquet_eigensystem,
    log_drive_stages,
    micromotion_states,
    pi_drive_stages,
    sample_pi_angles,
)
from .observables import (
    adjacent_gap_ratio,
    count_absolute_crossings,
    distance_correlator,
    eigenstate_expectations,
    pauli_pair_operator,
    spectral_histogram,
    spin_glass_susceptibility,
)

PAPER_ID = "1508.03344"
TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 8))


@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    family: str
    condition_id: str
    target_ids: tuple[str, ...]
    parameters: dict[str, Any]
    sample_start: int
    sample_count: int
    seed: int

    def payload(self) -> dict[str, Any]:
        result = asdict(self)
        result["target_ids"] = list(self.target_ids)
        return result


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


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("paper_id") != PAPER_ID:
        raise ValueError(f"expected paper_id {PAPER_ID}")
    return payload


def implementation_sha256(workspace: Path) -> str:
    paths = [
        workspace / "src" / "driven_ising" / "analytic.py",
        workspace / "src" / "driven_ising" / "model.py",
        workspace / "src" / "driven_ising" / "observables.py",
        workspace / "src" / "driven_ising" / "campaign.py",
        workspace / "scripts" / "run_reproduction.py",
    ]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(workspace).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def expand_grid(spec: dict[str, Any]) -> list[float]:
    kind = spec["kind"]
    if kind == "values":
        values = np.asarray(spec["values"], dtype=float)
    elif kind == "linspace":
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


def build_work_units(config: dict[str, Any]) -> list[WorkUnit]:
    seed_base = int(config["seed_base"])
    units: list[WorkUnit] = []

    def add_condition(
        family: str,
        target_ids: Iterable[str],
        parameters: dict[str, Any],
        samples: int,
        shard_size: int,
    ) -> None:
        if samples < 1 or shard_size < 1:
            raise ValueError("samples and shard_size must be positive")
        condition_hash = canonical_sha256({"family": family, "parameters": parameters})[
            :16
        ]
        condition_id = f"{family}-{condition_hash}"
        condition_seed = seed_base ^ int(condition_hash, 16)
        for sample_start in range(0, samples, shard_size):
            count = min(shard_size, samples - sample_start)
            units.append(
                WorkUnit(
                    unit_id=f"{condition_id}-s{sample_start:07d}",
                    family=family,
                    condition_id=condition_id,
                    target_ids=tuple(target_ids),
                    parameters=parameters,
                    sample_start=sample_start,
                    sample_count=count,
                    seed=condition_seed,
                )
            )

    fig1 = config["families"]["fig1"]
    for size in fig1["system_sizes"]:
        for mean_log_j in expand_grid(fig1["mean_log_j_grid"]):
            add_condition(
                "fig1",
                fig1["target_ids"],
                {
                    "system_size": int(size),
                    "mean_log_j": mean_log_j,
                    "interaction": float(fig1["interaction"]),
                    "parity": int(fig1["parity"]),
                    "periodic": bool(fig1["periodic"]),
                    "eigenstate_stride": int(
                        fig1["eigenstate_stride_by_size"][str(size)]
                    ),
                },
                int(fig1["samples_by_size"][str(size)]),
                int(fig1["shard_size_by_size"][str(size)]),
            )

    level = config["families"]["fig2_level"]
    for size in level["system_sizes"]:
        for interaction in expand_grid(level["interaction_grid"]):
            add_condition(
                "fig2_level",
                level["target_ids"],
                {
                    "system_size": int(size),
                    "interaction": interaction,
                    "parity": int(level["parity"]),
                    "t1": float(level["t1"]),
                    "t2": float(level["t2"]),
                    "phase": "pi",
                },
                int(level["samples_by_size"][str(size)]),
                int(level["shard_size_by_size"][str(size)]),
            )

    spectral = config["families"]["fig2_spectral"]
    for phase in spectral["phases"]:
        for interaction in spectral["interaction_values"]:
            add_condition(
                "fig2_spectral",
                spectral["target_ids"],
                {
                    "system_size": int(spectral["system_size"]),
                    "interaction": float(interaction),
                    "phase": phase,
                    "t1": float(spectral["t1"]),
                    "t2": float(spectral["t2"]),
                    "site": int(spectral["site"]),
                    "bins": int(spectral["bins"]),
                    "gaussian_sigma_bins": float(spectral["gaussian_sigma_bins"]),
                },
                int(spectral["samples"]),
                int(spectral["shard_size"]),
            )

    motion = config["families"]["fig2_micromotion"]
    add_condition(
        "fig2_micromotion",
        motion["target_ids"],
        {
            "system_size": int(motion["system_size"]),
            "interaction": float(motion["interaction"]),
            "phase": "pi",
            "t1": float(motion["t1"]),
            "t2": float(motion["t2"]),
            "time_points": int(motion["time_points"]),
            "selection_rule": motion["selection_rule"],
        },
        1,
        1,
    )
    ids = [unit.unit_id for unit in units]
    if len(ids) != len(set(ids)):
        raise ValueError("work-unit ids are not unique")
    return units


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    if config.get("numeric_item_ids") != [
        "Main Figure 1 level statistics",
        "Main Figure 1 spin-glass inset",
        "Main Figure 2(a) free phase diagram",
        "Main Figure 2(b) pi-phase level statistics",
        "Main Figure 2(c) operator spectral function",
        "Main Figure 2(d) correlator micromotion",
        "Quantitative localization and phase claims",
    ]:
        findings.append("numeric_item_ids do not match the frozen seven-item inventory")
    if set(config.get("target_ids", [])) != set(TARGET_IDS):
        findings.append("target_ids must cover T001-T007")
    for key in (
        "author_code_used",
        "author_numeric_arrays_used",
        "source_pixels_used_as_numerical_input",
        "source_figures_used_to_choose_scientific_parameters",
    ):
        if config.get("disclosures", {}).get(key) is not False:
            findings.append(f"{key} must be false")
    units = build_work_units(config)
    return {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "status": "passed" if not findings else "failed",
        "work_units": len(units),
        "sample_realizations": sum(unit.sample_count for unit in units),
        "families": sorted({unit.family for unit in units}),
        "target_ids": list(config["target_ids"]),
        "findings": findings,
    }


def execute_unit(unit: WorkUnit, backend: str) -> dict[str, Any]:
    if unit.family == "fig1":
        return _execute_fig1(unit, backend)
    if unit.family == "fig2_level":
        return _execute_fig2_level(unit, backend)
    if unit.family == "fig2_spectral":
        return _execute_fig2_spectral(unit, backend)
    if unit.family == "fig2_micromotion":
        return _execute_fig2_micromotion(unit, backend)
    raise ValueError(f"unsupported family: {unit.family}")


def run_units(
    workspace: Path,
    config_path: Path,
    output_root: Path,
    *,
    shard_index: int | None = None,
    shard_count: int | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    config = load_config(config_path)
    validation = validate_config(config)
    if validation["status"] != "passed":
        raise ValueError(validation["findings"])
    all_units = build_work_units(config)
    selected = _select_units(all_units, shard_index, shard_count)
    config_hash = file_sha256(config_path)
    implementation_hash = implementation_sha256(workspace)
    checkpoint_dir = output_root / "checkpoints" / config_hash[:16]
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    ran: list[str] = []
    resumed: list[str] = []
    for unit in selected:
        path = checkpoint_dir / f"{unit.unit_id}.json"
        unit_hash = canonical_sha256(unit.payload())
        if resume and _valid_checkpoint(
            path, config_hash, implementation_hash, unit_hash
        ):
            resumed.append(unit.unit_id)
            continue
        result = execute_unit(unit, str(config["backend"]))
        payload = {
            "schema_version": 1,
            "status": "passed",
            "paper_id": PAPER_ID,
            "config_sha256": config_hash,
            "implementation_sha256": implementation_hash,
            "unit_sha256": unit_hash,
            "unit": unit.payload(),
            "result": result,
        }
        _atomic_json(path, payload)
        ran.append(unit.unit_id)
    summary = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": PAPER_ID,
        "config_sha256": config_hash,
        "implementation_sha256": implementation_hash,
        "work_units_total": len(all_units),
        "work_units_selected": len(selected),
        "work_units_ran": len(ran),
        "work_units_resumed": len(resumed),
        "paper_parameters_executed": config["artifact_stage"]
        == "paper_scale_reconstructed"
        and len(selected) == len(all_units),
    }
    checks = output_root / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    name = (
        "run_summary.json"
        if shard_index is None
        else f"run_summary_{shard_index}_of_{shard_count}.json"
    )
    _atomic_json(checks / name, summary)
    return summary


def aggregate_units(
    workspace: Path, config_path: Path, output_root: Path
) -> dict[str, Any]:
    config = load_config(config_path)
    units = build_work_units(config)
    config_hash = file_sha256(config_path)
    implementation_hash = implementation_sha256(workspace)
    checkpoint_dir = output_root / "checkpoints" / config_hash[:16]
    payloads: list[dict[str, Any]] = []
    missing: list[str] = []
    invalid: list[str] = []
    for unit in units:
        path = checkpoint_dir / f"{unit.unit_id}.json"
        unit_hash = canonical_sha256(unit.payload())
        if not path.is_file():
            missing.append(unit.unit_id)
        elif not _valid_checkpoint(path, config_hash, implementation_hash, unit_hash):
            invalid.append(unit.unit_id)
        else:
            payloads.append(json.loads(path.read_text(encoding="utf-8")))
    if missing or invalid:
        raise RuntimeError(
            f"aggregation refused: missing={len(missing)} invalid={len(invalid)}"
        )

    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for payload in payloads:
        by_condition[payload["unit"]["condition_id"]].append(payload)
    conditions = [_aggregate_condition(group) for group in by_condition.values()]
    data_dir = output_root / "data"
    checks_dir = output_root / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    outputs = _write_aggregates(config, conditions, data_dir)
    science = _science_checks(config, conditions, outputs)
    _atomic_json(checks_dir / "science_checks.json", science)
    output_paths = [*outputs, checks_dir / "science_checks.json"]
    manifest = {
        "schema_version": 1,
        "status": "passed" if science["status"] == "passed" else "failed",
        "paper_id": PAPER_ID,
        "artifact_stage": config["artifact_stage"],
        "parameters_paper_exact": bool(config["parameters_paper_exact"]),
        "config_sha256": config_hash,
        "implementation_sha256": implementation_hash,
        "work_units": len(units),
        "sample_realizations": sum(unit.sample_count for unit in units),
        "target_ids": list(TARGET_IDS),
        "outputs": {
            _display_path(path, workspace): file_sha256(path) for path in output_paths
        },
    }
    _atomic_json(checks_dir / "generated_data_manifest.json", manifest)
    return manifest


def _execute_fig1(unit: WorkUnit, backend: str) -> dict[str, Any]:
    parameters = unit.parameters
    sums = defaultdict(float)
    for offset in range(unit.sample_count):
        rng = _sample_rng(unit.seed, unit.sample_start + offset)
        stages, basis = log_drive_stages(
            system_size=parameters["system_size"],
            mean_log_j=parameters["mean_log_j"],
            interaction=parameters["interaction"],
            rng=rng,
            parity=parameters["parity"],
            periodic=parameters["periodic"],
        )
        eigensystem = floquet_eigensystem(stages, backend=backend, return_vectors=True)
        ratio = adjacent_gap_ratio(eigensystem.angles)
        ratio_linear = adjacent_gap_ratio(eigensystem.angles, circular=False)
        chi = spin_glass_susceptibility(
            eigensystem.vectors,
            basis,
            parameters["system_size"],
            eigenstate_stride=parameters["eigenstate_stride"],
        )
        sums["sum_r"] += ratio
        sums["sum_r2"] += ratio**2
        sums["sum_r_linear"] += ratio_linear
        sums["sum_chi"] += chi
        sums["sum_chi2"] += chi**2
        sums["max_unitary_residual"] = max(
            sums["max_unitary_residual"], eigensystem.unitary_residual
        )
    return {"count": unit.sample_count, **dict(sums)}


def _execute_fig2_level(unit: WorkUnit, backend: str) -> dict[str, Any]:
    parameters = unit.parameters
    sums = defaultdict(float)
    for offset in range(unit.sample_count):
        rng = _sample_rng(unit.seed, unit.sample_start + offset)
        h_t1, j_t2 = sample_pi_angles(parameters["system_size"], rng, phase="pi")
        stages, _ = pi_drive_stages(
            system_size=parameters["system_size"],
            interaction=parameters["interaction"],
            h_t1=h_t1,
            j_t2=j_t2,
            t1=parameters["t1"],
            t2=parameters["t2"],
            parity=parameters["parity"],
        )
        eigensystem = floquet_eigensystem(stages, backend=backend, return_vectors=False)
        ratio = adjacent_gap_ratio(eigensystem.angles)
        sums["sum_r"] += ratio
        sums["sum_r2"] += ratio**2
        sums["sum_r_linear"] += adjacent_gap_ratio(eigensystem.angles, circular=False)
        sums["max_unitary_residual"] = max(
            sums["max_unitary_residual"], eigensystem.unitary_residual
        )
    return {"count": unit.sample_count, **dict(sums)}


def _execute_fig2_spectral(unit: WorkUnit, backend: str) -> dict[str, Any]:
    parameters = unit.parameters
    density_sum: np.ndarray | None = None
    raw_sum: np.ndarray | None = None
    omega: np.ndarray | None = None
    weight_sum = 0.0
    literal_imag_abs_sum = 0.0
    literal_imag_rms_sum = 0.0
    maximum_residual = 0.0
    for offset in range(unit.sample_count):
        rng = _sample_rng(unit.seed, unit.sample_start + offset)
        h_t1, j_t2 = sample_pi_angles(
            parameters["system_size"], rng, phase=parameters["phase"]
        )
        even_stages, even_basis = pi_drive_stages(
            system_size=parameters["system_size"],
            interaction=parameters["interaction"],
            h_t1=h_t1,
            j_t2=j_t2,
            t1=parameters["t1"],
            t2=parameters["t2"],
            parity=1,
        )
        odd_stages, odd_basis = pi_drive_stages(
            system_size=parameters["system_size"],
            interaction=parameters["interaction"],
            h_t1=h_t1,
            j_t2=j_t2,
            t1=parameters["t1"],
            t2=parameters["t2"],
            parity=-1,
        )
        even = floquet_eigensystem(even_stages, backend=backend, return_vectors=True)
        odd = floquet_eigensystem(odd_stages, backend=backend, return_vectors=True)
        spectrum = spectral_histogram(
            even,
            odd,
            even_basis,
            odd_basis,
            site=parameters["site"],
            bins=parameters["bins"],
            gaussian_sigma_bins=parameters["gaussian_sigma_bins"],
        )
        omega = np.asarray(spectrum["omega"])
        density = np.asarray(spectrum["density"])
        raw = np.asarray(spectrum["raw_density"])
        density_sum = density.copy() if density_sum is None else density_sum + density
        raw_sum = raw.copy() if raw_sum is None else raw_sum + raw
        weight_sum += float(spectrum["integrated_weight"])
        literal_imag_abs_sum += abs(float(spectrum["literal_unsquared_sum_imag"]))
        literal_imag_rms_sum += float(spectrum["literal_unsquared_imag_rms"])
        maximum_residual = max(
            maximum_residual, even.unitary_residual, odd.unitary_residual
        )
    assert density_sum is not None and raw_sum is not None and omega is not None
    return {
        "count": unit.sample_count,
        "omega": omega.tolist(),
        "sum_density": density_sum.tolist(),
        "sum_raw_density": raw_sum.tolist(),
        "sum_integrated_weight": weight_sum,
        "sum_literal_imag_abs": literal_imag_abs_sum,
        "sum_literal_imag_rms": literal_imag_rms_sum,
        "max_unitary_residual": maximum_residual,
    }


def _execute_fig2_micromotion(unit: WorkUnit, backend: str) -> dict[str, Any]:
    parameters = unit.parameters
    rng = _sample_rng(unit.seed, unit.sample_start)
    h_t1, j_t2 = sample_pi_angles(parameters["system_size"], rng, phase="pi")
    stages, basis = pi_drive_stages(
        system_size=parameters["system_size"],
        interaction=parameters["interaction"],
        h_t1=h_t1,
        j_t2=j_t2,
        t1=parameters["t1"],
        t2=parameters["t2"],
        parity=1,
    )
    eigensystem = floquet_eigensystem(stages, backend=backend, return_vectors=True)
    if eigensystem.vectors is None:
        raise RuntimeError("micromotion requires eigenvectors")
    x_operator = _average_distance_operator(basis, parameters["system_size"], "x")
    y_operator = _average_distance_operator(basis, parameters["system_size"], "y")
    x_values = eigenstate_expectations(eigensystem.vectors, x_operator).real
    y_values = eigenstate_expectations(eigensystem.vectors, y_operator).real
    if parameters["selection_rule"] != "maximum_long_range_order":
        raise ValueError("unsupported eigenstate selection rule")
    selected = int(np.argmax(np.maximum(np.abs(x_values), np.abs(y_values))))
    times = np.linspace(0.0, eigensystem.total_period, parameters["time_points"])
    states = micromotion_states(stages, eigensystem.vectors[:, selected], times)
    cxx = [
        distance_correlator(state, basis, parameters["system_size"], axis="x")
        for state in states
    ]
    cyy = [
        distance_correlator(state, basis, parameters["system_size"], axis="y")
        for state in states
    ]
    return {
        "count": 1,
        "times": times.tolist(),
        "cxx": cxx,
        "cyy": cyy,
        "crossings": count_absolute_crossings(cxx, cyy),
        "selected_eigenstate": selected,
        "selected_angle": float(eigensystem.angles[selected]),
        "max_unitary_residual": eigensystem.unitary_residual,
    }


def _aggregate_condition(group: list[dict[str, Any]]) -> dict[str, Any]:
    first = group[0]
    family = first["unit"]["family"]
    parameters = first["unit"]["parameters"]
    count = sum(int(payload["result"]["count"]) for payload in group)
    result: dict[str, Any] = {"count": count}
    if family in {"fig1", "fig2_level"}:
        for key in ("sum_r", "sum_r2", "sum_r_linear"):
            result[key] = sum(float(payload["result"][key]) for payload in group)
        if family == "fig1":
            for key in ("sum_chi", "sum_chi2"):
                result[key] = sum(float(payload["result"][key]) for payload in group)
    elif family == "fig2_spectral":
        result["omega"] = first["result"]["omega"]
        for key in ("sum_density", "sum_raw_density"):
            result[key] = np.sum(
                [np.asarray(payload["result"][key], dtype=float) for payload in group],
                axis=0,
            ).tolist()
        for key in (
            "sum_integrated_weight",
            "sum_literal_imag_abs",
            "sum_literal_imag_rms",
        ):
            result[key] = sum(float(payload["result"][key]) for payload in group)
    elif family == "fig2_micromotion":
        if len(group) != 1:
            raise RuntimeError("micromotion must have exactly one work unit")
        result = dict(first["result"])
    result["max_unitary_residual"] = max(
        float(payload["result"]["max_unitary_residual"]) for payload in group
    )
    return {
        "family": family,
        "condition_id": first["unit"]["condition_id"],
        "parameters": parameters,
        "result": result,
    }


def _write_aggregates(
    config: dict[str, Any], conditions: list[dict[str, Any]], data_dir: Path
) -> list[Path]:
    outputs: list[Path] = []
    fig1_rows: list[dict[str, Any]] = []
    level_rows: list[dict[str, Any]] = []
    spectral_rows: list[dict[str, Any]] = []
    motion_row: dict[str, Any] | None = None
    for condition in conditions:
        family = condition["family"]
        parameters = condition["parameters"]
        result = condition["result"]
        count = int(result["count"])
        if family == "fig1":
            fig1_rows.append(
                {
                    **parameters,
                    "samples": count,
                    "r_mean": result["sum_r"] / count,
                    "r_sem": _sem(result["sum_r"], result["sum_r2"], count),
                    "r_nonwrap_mean": result["sum_r_linear"] / count,
                    "chi_mean": result["sum_chi"] / count,
                    "chi_sem": _sem(result["sum_chi"], result["sum_chi2"], count),
                    "max_unitary_residual": result["max_unitary_residual"],
                }
            )
        elif family == "fig2_level":
            level_rows.append(
                {
                    **parameters,
                    "samples": count,
                    "r_mean": result["sum_r"] / count,
                    "r_sem": _sem(result["sum_r"], result["sum_r2"], count),
                    "r_nonwrap_mean": result["sum_r_linear"] / count,
                    "max_unitary_residual": result["max_unitary_residual"],
                }
            )
        elif family == "fig2_spectral":
            spectral_rows.append(
                {
                    **parameters,
                    "samples": count,
                    "omega": result["omega"],
                    "density": (np.asarray(result["sum_density"]) / count).tolist(),
                    "raw_density": (
                        np.asarray(result["sum_raw_density"]) / count
                    ).tolist(),
                    "integrated_weight": result["sum_integrated_weight"] / count,
                    "literal_unsquared_imag_abs": result["sum_literal_imag_abs"]
                    / count,
                    "literal_unsquared_imag_rms": result["sum_literal_imag_rms"]
                    / count,
                    "max_unitary_residual": result["max_unitary_residual"],
                }
            )
        elif family == "fig2_micromotion":
            motion_row = {**parameters, **result}
    for filename, payload in (
        ("fig1_observables.json", {"rows": sorted(fig1_rows, key=_fig1_key)}),
        ("fig2_level_statistics.json", {"rows": sorted(level_rows, key=_level_key)}),
        (
            "fig2_spectral_functions.json",
            {"rows": sorted(spectral_rows, key=_spectral_key)},
        ),
        ("fig2_micromotion.json", motion_row or {}),
    ):
        path = data_dir / filename
        _atomic_json(path, {"schema_version": 1, "paper_id": PAPER_ID, **payload})
        outputs.append(path)
    phase = free_phase_map(int(config["families"]["fig2_phase"]["points"]))
    phase_path = data_dir / "fig2_phase_diagram.npz"
    np.savez_compressed(phase_path, **phase)
    outputs.append(phase_path)
    return outputs


def _science_checks(
    config: dict[str, Any], conditions: list[dict[str, Any]], outputs: list[Path]
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    maximum_residual = max(
        float(condition["result"]["max_unitary_residual"]) for condition in conditions
    )
    _record(
        checks,
        "CHK_UNITARY",
        maximum_residual < 1e-8,
        maximum_residual,
        1e-8,
        "max",
        ["T001", "T004", "T005", "T006"],
    )
    phase = free_phase_map(9)
    labels = set(int(value) for value in np.unique(phase["phase_code"]))
    _record(
        checks,
        "CHK_FOUR_PHASES",
        labels == set(PHASE_TO_CODE.values()),
        len(labels),
        4,
        "equal",
        ["T003", "T007"],
    )
    all_conditions = {condition["family"] for condition in conditions}
    _record(
        checks,
        "CHK_FAMILY_COVERAGE",
        all_conditions == {"fig1", "fig2_level", "fig2_spectral", "fig2_micromotion"},
        len(all_conditions),
        4,
        "equal",
        list(TARGET_IDS),
    )
    fig1 = [condition for condition in conditions if condition["family"] == "fig1"]
    chi_values = [
        condition["result"]["sum_chi"] / condition["result"]["count"]
        for condition in fig1
    ]
    _record(
        checks,
        "CHK_CHI_BOUNDS",
        bool(chi_values) and min(chi_values) >= 0 and max(chi_values) <= 1 + 1e-10,
        max(chi_values),
        1.0,
        "max",
        ["T002"],
    )
    largest_fig1_size = max(
        int(condition["parameters"]["system_size"]) for condition in fig1
    )
    largest_fig1 = [
        condition
        for condition in fig1
        if int(condition["parameters"]["system_size"]) == largest_fig1_size
    ]
    pm_row = min(largest_fig1, key=lambda row: float(row["parameters"]["mean_log_j"]))
    sg_row = max(largest_fig1, key=lambda row: float(row["parameters"]["mean_log_j"]))
    chi_contrast = (
        sg_row["result"]["sum_chi"] / sg_row["result"]["count"]
        - pm_row["result"]["sum_chi"] / pm_row["result"]["count"]
    )
    _record(
        checks,
        "CHK_SG_PM_CONTRAST",
        chi_contrast > 0.2,
        chi_contrast,
        0.2,
        "min",
        ["T002", "T007"],
    )
    levels = [
        condition for condition in conditions if condition["family"] == "fig2_level"
    ]
    largest_level_size = max(
        int(condition["parameters"]["system_size"]) for condition in levels
    )
    largest_levels = [
        condition
        for condition in levels
        if int(condition["parameters"]["system_size"]) == largest_level_size
    ]
    low_level = min(
        largest_levels, key=lambda row: float(row["parameters"]["interaction"])
    )
    transition_level = min(
        largest_levels,
        key=lambda row: abs(float(row["parameters"]["interaction"]) - 0.1),
    )
    level_contrast = (
        transition_level["result"]["sum_r"] / transition_level["result"]["count"]
        - low_level["result"]["sum_r"] / low_level["result"]["count"]
    )
    _record(
        checks,
        "CHK_PI_LEVEL_CROSSOVER",
        level_contrast > 0.02,
        level_contrast,
        0.02,
        "min",
        ["T004", "T007"],
    )
    spectra = [
        condition for condition in conditions if condition["family"] == "fig2_spectral"
    ]
    minimum_density = min(
        float(np.min(condition["result"]["sum_density"])) for condition in spectra
    )
    weight_error = max(
        abs(
            condition["result"]["sum_integrated_weight"] / condition["result"]["count"]
            - 0.5
        )
        for condition in spectra
    )
    _record(
        checks,
        "CHK_SPECTRAL_POSITIVE",
        minimum_density >= -1e-12,
        minimum_density,
        -1e-12,
        "min",
        ["T005"],
    )
    _record(
        checks,
        "CHK_SPECTRAL_SUM_RULE",
        weight_error < 1e-10,
        weight_error,
        1e-10,
        "max",
        ["T005", "T007"],
    )
    spectral_peak_errors: list[float] = []
    spectral_decay_ratios: list[float] = []
    for phase in ("pi", "zero"):
        phase_rows = [row for row in spectra if row["parameters"]["phase"] == phase]
        low = min(phase_rows, key=lambda row: float(row["parameters"]["interaction"]))
        high = max(phase_rows, key=lambda row: float(row["parameters"]["interaction"]))
        omega = np.asarray(low["result"]["omega"], dtype=float)
        density = (
            np.asarray(low["result"]["sum_density"], dtype=float)
            / low["result"]["count"]
        )
        high_density = (
            np.asarray(high["result"]["sum_density"], dtype=float)
            / high["result"]["count"]
        )
        peak = float(omega[int(np.argmax(density))])
        period = float(low["parameters"]["t1"] + low["parameters"]["t2"])
        expected = np.pi / period if phase == "pi" else 0.0
        error = abs(abs(peak) - expected) if phase == "pi" else abs(peak)
        spectral_peak_errors.append(error)
        spectral_decay_ratios.append(float(np.max(density) / np.max(high_density)))
    maximum_peak_error = max(spectral_peak_errors)
    _record(
        checks,
        "CHK_ZERO_PI_PEAKS",
        maximum_peak_error < 0.08,
        maximum_peak_error,
        0.08,
        "max",
        ["T005", "T007"],
    )
    minimum_decay_ratio = min(spectral_decay_ratios)
    _record(
        checks,
        "CHK_SPECTRAL_PEAK_DECAY",
        minimum_decay_ratio > 1.5,
        minimum_decay_ratio,
        1.5,
        "min",
        ["T005", "T007"],
    )
    literal_rms = min(
        condition["result"]["sum_literal_imag_rms"] / condition["result"]["count"]
        for condition in spectra
    )
    _record(
        checks,
        "CHK_PRINTED_SPECTRAL_FORM_COMPLEX",
        literal_rms > 1e-6,
        literal_rms,
        1e-6,
        "min",
        ["T005", "T007"],
    )
    motion = next(
        condition
        for condition in conditions
        if condition["family"] == "fig2_micromotion"
    )
    crossings = int(motion["result"]["crossings"])
    _record(
        checks,
        "CHK_MICROMOTION_CROSSINGS",
        crossings >= 2,
        crossings,
        2,
        "min",
        ["T006", "T007"],
    )
    status = "passed" if all(check["passed"] for check in checks) else "failed"
    return {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "status": status,
        "artifact_stage": config["artifact_stage"],
        "checks": checks,
        "outputs": [path.name for path in outputs],
    }


def _record(
    checks: list[dict[str, Any]],
    check_id: str,
    passed: bool,
    value: Any,
    threshold: Any,
    comparator: str,
    target_ids: list[str],
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "passed": bool(passed),
            "value": value,
            "threshold": threshold,
            "comparator": comparator,
            "target_ids": target_ids,
        }
    )


def _average_distance_operator(
    basis: np.ndarray, system_size: int, axis: str
) -> np.ndarray:
    distance = system_size // 2
    operators = [
        pauli_pair_operator(basis, system_size, site, site + distance, axis)
        for site in range(system_size - distance)
    ]
    return np.mean(operators, axis=0)


def _sample_rng(seed: int, sample_index: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([seed, sample_index]))


def _select_units(
    units: list[WorkUnit], shard_index: int | None, shard_count: int | None
) -> list[WorkUnit]:
    if shard_index is None and shard_count is None:
        return units
    if shard_index is None or shard_count is None:
        raise ValueError("shard_index and shard_count must be provided together")
    if not (0 <= shard_index < shard_count):
        raise ValueError("invalid shard index")
    return [
        unit for index, unit in enumerate(units) if index % shard_count == shard_index
    ]


def _valid_checkpoint(
    path: Path, config_hash: str, implementation_hash: str, unit_hash: str
) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        payload.get("status") == "passed"
        and payload.get("config_sha256") == config_hash
        and payload.get("implementation_sha256") == implementation_hash
        and payload.get("unit_sha256") == unit_hash
    )


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _display_path(path: Path, workspace: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return str(path)


def _sem(total: float, total_square: float, count: int) -> float:
    if count < 2:
        return 0.0
    variance = max(0.0, (total_square - total**2 / count) / (count - 1))
    return float(np.sqrt(variance / count))


def _fig1_key(row: dict[str, Any]) -> tuple[int, float]:
    return int(row["system_size"]), float(row["mean_log_j"])


def _level_key(row: dict[str, Any]) -> tuple[int, float]:
    return int(row["system_size"]), float(row["interaction"])


def _spectral_key(row: dict[str, Any]) -> tuple[str, float]:
    return str(row["phase"]), float(row["interaction"])
