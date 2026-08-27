"""Clean-room scientific generation for the EV20 Rydberg-qudit targets.

This module has one deliberately narrow responsibility: turn paper-derived
configuration into numerical arrays and freeze those arrays.  It never opens
the author dataset, source figures, paper PDF, or legacy numerical outputs.
Reference comparison is a separate phase in ``reproduce_qudit_annealing.py``.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from src.rydberg_qudit import (
    atom_coordinate_rows,
    compile_paper_program,
    hardware_control_rows,
    simulate_program,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"configuration must be a JSON object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write an empty dataset: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _workspace_path(output_root: Path, declared: str) -> Path:
    relative = Path(declared)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe output path: {declared}")
    parts = relative.parts[1:] if relative.parts and relative.parts[0] == "outputs" else relative.parts
    return output_root / Path(*parts)


def _as_float_array(value: object) -> np.ndarray:
    return np.asarray(value, dtype=float)


def _assert_program_contract(program: object, profiles: dict[str, Any]) -> None:
    profile = program.profile
    try:
        expected = profiles[profile.profile_id]
    except KeyError as exc:
        raise ValueError(f"profile absent from frozen configuration: {profile.profile_id}") from exc
    checks = {
        "principal_quantum_numbers": np.array_equal(
            np.asarray(profile.principal_quantum_numbers),
            np.asarray(expected["principal_quantum_numbers"]),
        ),
        "c6_intra_2pi_ghz_um6": np.allclose(
            _as_float_array(profile.c6_intra_2pi_ghz_um6),
            _as_float_array(expected["c6_intra_2pi_ghz_um6"]),
            atol=0.0,
            rtol=0.0,
        ),
        "c6_inter_2pi_ghz_um6": np.allclose(
            _as_float_array(profile.c6_inter_2pi_ghz_um6),
            _as_float_array(expected["c6_inter_2pi_ghz_um6"]),
            atol=0.0,
            rtol=0.0,
        ),
        "omega_max_over_2pi_mhz": np.allclose(
            _as_float_array(profile.omega_max_over_2pi_mhz),
            _as_float_array(expected["omega_max_over_2pi_mhz"]),
            atol=0.0,
            rtol=0.0,
        ),
        "detuning_max_over_2pi_mhz": np.allclose(
            _as_float_array(profile.detuning_max_over_2pi_mhz),
            _as_float_array(expected["detuning_max_over_2pi_mhz"]),
            atol=0.0,
            rtol=0.0,
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"compiled profile differs from frozen contract: {checks}")


def _program_result_record(result: object, *, trotter_intervals: int) -> dict[str, Any]:
    probability_sum = float(result.final_probabilities.sum())
    target_mass = float(result.final_probabilities[result.target_indices].sum())
    proper_mass = float(
        result.final_probabilities[result.proper_coloring_indices].sum()
    )
    checks = {
        "finite_probabilities": bool(np.isfinite(result.final_probabilities).all()),
        "normalization": bool(abs(probability_sum - 1.0) <= 1e-10),
        "target_indices_nonempty": bool(len(result.target_indices) > 0),
        "proper_coloring_indices_nonempty": bool(
            len(result.proper_coloring_indices) > 0
        ),
        "target_probability_bounded": bool(
            np.all(
                (result.target_probability >= -1e-12)
                & (result.target_probability <= 1.0 + 1e-12)
            )
        ),
        "time_grid_independently_constructed": bool(
            len(result.times_us) == trotter_intervals + 1
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"{result.graph_id}: clean-room invariant failed: {checks}"
        )
    return {
        "graph_id": result.graph_id,
        "profile_id": result.profile_id,
        "basis_state_count": int(len(result.basis)),
        "time_point_count": int(len(result.times_us)),
        "trotter_intervals": trotter_intervals,
        "propagation_scheme": result.propagation_scheme,
        "final_probability_sum": probability_sum,
        "final_target_probability": target_mass,
        "final_proper_coloring_probability": proper_mass,
        "final_norm_error": float(result.final_norm_error),
        "target_indices_zero_based": [int(value) for value in result.target_indices],
        "proper_coloring_indices_zero_based": [
            int(value) for value in result.proper_coloring_indices
        ],
        "checks": checks,
    }


def _curve_rows(results: dict[str, object], graph_ids: list[str]) -> list[dict[str, object]]:
    first = results[graph_ids[0]]
    rows: list[dict[str, object]] = []
    for index, time_us in enumerate(first.times_us):
        row: dict[str, object] = {"time_us": float(time_us)}
        for graph_id in graph_ids:
            result = results[graph_id]
            if not np.array_equal(result.times_us, first.times_us):
                raise RuntimeError("clean-room curve grids differ within one target")
            row[f"graph_{graph_id}_target_probability"] = float(
                result.target_probability[index]
            )
        rows.append(row)
    return rows


def _distribution_rows(
    results: dict[str, object], graph_ids: list[str]
) -> list[dict[str, object]]:
    maximum = max(len(results[graph_id].final_probabilities) for graph_id in graph_ids)
    rows: list[dict[str, object]] = []
    for state_index in range(maximum):
        row: dict[str, object] = {"state_index_1_based": state_index + 1}
        for graph_id in graph_ids:
            values = results[graph_id].final_probabilities
            row[f"graph_{graph_id}_probability"] = (
                float(values[state_index]) if state_index < len(values) else ""
            )
        rows.append(row)
    return rows


def _write_hardware_handoff(output_root: Path) -> list[Path]:
    program_keys = [
        *((graph_id, 2) for graph_id in "ABCDEF"),
        *((graph_id, 3) for graph_id in "ABCDEFGHIJ"),
        *((graph_id, 4) for graph_id in "GHI"),
    ]
    coordinate_rows: list[dict[str, object]] = []
    for graph_id, count in program_keys:
        try:
            program = compile_paper_program(graph_id, count)
        except ValueError:
            continue
        coordinate_rows.extend(
            {"rydberg_level_count": count, **row}
            for row in atom_coordinate_rows(program)
        )
    coordinate_path = output_root / "data" / "paper_atom_coordinates.csv"
    _write_csv(coordinate_path, coordinate_rows)

    control_rows: list[dict[str, object]] = []
    for graph_id, count in (("A", 2), ("A", 3), ("G", 4), ("J", 3)):
        program = compile_paper_program(graph_id, count)
        control_rows.extend(
            {"rydberg_level_count": count, **row}
            for row in hardware_control_rows(program)
        )
    control_path = output_root / "data" / "paper_hardware_controls.csv"
    _write_csv(control_path, control_rows)
    return [coordinate_path, control_path]


def _run_convergence_checks(
    config: dict[str, Any],
    cached: dict[tuple[str, int], object],
) -> dict[str, Any]:
    schedule = config["schedule"]
    base_intervals = int(schedule["trotter_intervals"])
    rows: list[dict[str, Any]] = []
    for spec in config.get("convergence_checks", []):
        graph_id = str(spec["graph_id"])
        level_count = int(spec["rydberg_level_count"])
        refined_intervals = int(spec["refined_trotter_intervals"])
        base = cached[(graph_id, level_count)]
        program = compile_paper_program(graph_id, level_count)
        refined = simulate_program(
            program,
            times_us=program.schedule.times(refined_intervals + 1),
        )
        distribution_tvd = float(
            0.5 * np.sum(np.abs(base.final_probabilities - refined.final_probabilities))
        )
        proper_delta = float(
            abs(
                base.final_probabilities[base.proper_coloring_indices].sum()
                - refined.final_probabilities[refined.proper_coloring_indices].sum()
            )
        )
        rows.append(
            {
                "target_id": spec["target_id"],
                "graph_id": graph_id,
                "rydberg_level_count": level_count,
                "base_trotter_intervals": base_intervals,
                "refined_trotter_intervals": refined_intervals,
                "final_distribution_total_variation": distribution_tvd,
                "proper_coloring_mass_absolute_delta": proper_delta,
                "base_norm_error": float(base.final_norm_error),
                "refined_norm_error": float(refined.final_norm_error),
                "status": "passed" if proper_delta <= 0.01 else "failed",
            }
        )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if all(row["status"] == "passed" for row in rows) else "failed",
        "checks": rows,
    }


def run_generation(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _read_object(config_path)
    if config.get("paper_id") != "2504.08598":
        raise ValueError("clean-room configuration paper_id mismatch")
    boundary = config.get("clean_room_boundary")
    if not isinstance(boundary, dict) or any(
        boundary.get(field) is not False
        for field in (
            "paper_pdf_read_by_runner",
            "source_pixels_used",
            "author_numeric_arrays_used",
            "author_code_used",
        )
    ):
        raise ValueError("clean-room boundary must explicitly prohibit source inputs")

    schedule = config["schedule"]
    intervals = int(schedule["trotter_intervals"])
    times = np.linspace(
        0.0,
        float(schedule["duration_us"]),
        intervals + 1,
        dtype=float,
    )
    profiles = config["profiles"]
    targets = config["targets"]
    cached: dict[tuple[str, int], object] = {}
    generated_paths: list[Path] = []
    target_paths: list[Path] = []
    target_records: dict[str, dict[str, Any]] = {}

    for target_id, spec in targets.items():
        if spec.get("mode") == "input_boundary":
            record = {
                "target_id": target_id,
                "figure_id": spec["figure_id"],
                "status": "blocked_missing_source_input",
                "scientific_coverage_promoted": False,
                "required_input": spec["required_input"],
                "conflicting_public_values": spec["conflicting_public_values"],
                "acceptance_boundary": spec["acceptance_boundary"],
                "author_dataset_accessed": False,
            }
        else:
            results: dict[str, object] = {}
            graph_records: dict[str, Any] = {}
            for program_spec in spec["programs"]:
                graph_id = str(program_spec["graph_id"])
                level_count = int(program_spec["rydberg_level_count"])
                program = compile_paper_program(graph_id, level_count)
                _assert_program_contract(program, profiles)
                if not np.isclose(program.schedule.ramp_on_end_us, schedule["ramp_on_end_us"]):
                    raise RuntimeError("compiled ramp-on time differs from frozen config")
                if not np.isclose(program.schedule.detuning_sweep_end_us, schedule["detuning_sweep_end_us"]):
                    raise RuntimeError("compiled detuning sweep differs from frozen config")
                if not np.isclose(program.schedule.duration_us, schedule["duration_us"]):
                    raise RuntimeError("compiled duration differs from frozen config")
                result = simulate_program(program, times_us=times)
                cached[(graph_id, level_count)] = result
                results[graph_id] = result
                graph_records[graph_id] = _program_result_record(
                    result, trotter_intervals=intervals
                )

            if spec.get("curve_graph_ids"):
                curve_path = _workspace_path(output_root, str(spec["curve_output"]))
                _write_csv(curve_path, _curve_rows(results, list(spec["curve_graph_ids"])))
                generated_paths.append(curve_path)
            if spec.get("distribution_graph_ids"):
                graph_ids = list(spec["distribution_graph_ids"])
                if "distribution_output" in spec:
                    distribution_path = _workspace_path(
                        output_root, str(spec["distribution_output"])
                    )
                    _write_csv(
                        distribution_path,
                        _distribution_rows(results, graph_ids),
                    )
                    generated_paths.append(distribution_path)
                else:
                    for key, declared_path in spec["distribution_outputs"].items():
                        selected = key.split(",")
                        distribution_path = _workspace_path(
                            output_root, str(declared_path)
                        )
                        _write_csv(
                            distribution_path,
                            _distribution_rows(results, selected),
                        )
                        generated_paths.append(distribution_path)
            record = {
                "target_id": target_id,
                "figure_id": spec["figure_id"],
                "status": "generated_clean_room",
                "scientific_coverage_promoted": False,
                "author_dataset_accessed": False,
                "time_grid_source": "paper schedule and printed p=300 only",
                "graphs": graph_records,
            }

        target_path = output_root / "data" / "clean_room_reproduction" / f"{target_id}.json"
        _write_json(target_path, record)
        target_paths.append(target_path)
        target_records[target_id] = record

    generated_paths.extend(_write_hardware_handoff(output_root))
    convergence = _run_convergence_checks(config, cached)
    convergence_path = output_root / "checks" / "qudit_convergence_audit.json"
    _write_json(convergence_path, convergence)
    generated_paths.append(convergence_path)
    if convergence["status"] != "passed":
        raise RuntimeError("clean-room convergence checks failed")

    frozen_files = [*generated_paths, *target_paths]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "phase": "scientific_generation_frozen",
        "author_dataset_accessed": False,
        "author_numeric_arrays_used_for_scientific_inputs": False,
        "source_pixels_used_for_scientific_inputs": False,
        "scientific_configuration_frozen_before_reference_comparison": True,
        "trotter_intervals": intervals,
        "time_point_count": intervals + 1,
        "generated_files": [
            {
                "path": path.relative_to(output_root.parent).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(frozen_files)
        ],
    }
    manifest_path = output_root / "checks" / "generated_data_manifest.json"
    _write_json(manifest_path, manifest)
    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "generated_and_frozen",
        "target_count": len(target_records),
        "generated_target_count": sum(
            row["status"] == "generated_clean_room"
            for row in target_records.values()
        ),
        "input_blocked_target_count": sum(
            row["status"] == "blocked_missing_source_input"
            for row in target_records.values()
        ),
        "generated_files_count": len(frozen_files),
        "generation_manifest": manifest_path.relative_to(output_root.parent).as_posix(),
        "author_dataset_accessed": False,
    }
    summary_path = output_root / "data" / "clean_room_reproduction" / "campaign_summary.json"
    _write_json(summary_path, summary)
    return summary
