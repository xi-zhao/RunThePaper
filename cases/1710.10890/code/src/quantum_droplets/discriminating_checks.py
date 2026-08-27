"""Code-fault discrimination for the pending GPE and calibration targets.

All numerical inputs are frozen assumptions used only to exercise the declared
solver path.  The missing paper atom numbers and calibration field remain an
explicit input boundary, so successful checks do not alter scientific coverage.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .coupled_gpe import run_split_step_scenario
from .implementation_closure import calibration_input_contract
from .model import ScatteringModel
from .paper_scale import build_tasks, make_smoke_config, validate_config


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _interactions(scenario: dict[str, Any], theory: dict[str, Any]) -> dict[str, float]:
    interaction = scenario["interaction"]
    if interaction["mode"] == "scattering_model":
        values = ScatteringModel.from_config(theory).evaluate(
            float(interaction["magnetic_field_gauss"])
        )
        return {
            "a11_bohr": float(values["a11_bohr"]),
            "a22_bohr": float(values["a22_bohr"]),
            "a12_bohr": float(values["a12_bohr"]),
        }
    if interaction["mode"] == "explicit":
        return {
            "a11_bohr": float(interaction["a11_bohr"]),
            "a22_bohr": float(interaction["a22_bohr"]),
            "a12_bohr": float(interaction["a12_bohr"]),
        }
    raise ValueError(f"unsupported interaction mode {interaction['mode']!r}")


def _run_scenario(
    *,
    scenario: dict[str, Any],
    profile: dict[str, Any],
    theory: dict[str, Any],
    checkpoint: Path,
) -> dict[str, Any]:
    payload = {"scenario": scenario, "profile": profile}
    result = run_split_step_scenario(
        scenario,
        profile,
        _interactions(scenario, theory),
        checkpoint,
        resume=False,
        task_hash=_canonical_hash(payload),
    )
    diagnostics = dict(result["diagnostics"])
    return {
        "diagnostics": diagnostics,
        "final_sigma_micrometre": float(result["sigma_micrometre"][-1]),
        "maximum_boundary_mass_fraction": float(
            np.max(result["boundary_mass_fraction"])
        ),
        "all_values_finite": bool(
            all(
                np.all(np.isfinite(value))
                for key, value in result.items()
                if key != "diagnostics"
            )
        ),
    }


def _refined_smoke_config(config: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    refined = copy.deepcopy(config)
    for profile in refined["parameters"]["profiles"].values():
        profile["grid"] = {
            "shape": [int(parameters["grid_points"])] * 3,
            "lengths_micrometre": [float(parameters["box_length_micrometre"])] * 3,
        }
    return validate_config(refined)


def _t008_check(
    paper_scale: dict[str, Any],
    theory: dict[str, Any],
    parameters: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    coarse = make_smoke_config(paper_scale)
    refined = _refined_smoke_config(
        make_smoke_config(paper_scale), parameters["refined_smoke"]
    )
    runs: dict[str, dict[str, Any]] = {}
    for profile_name, campaign in (("coarse", coarse), ("refined", refined)):
        selected = [
            task
            for task in build_tasks(campaign)
            if task.campaign_id == "production"
            and task.payload["scenario"]["target_id"] == "T008"
        ]
        if len(selected) != 2:
            raise RuntimeError("T008 smoke must contain exactly two field scenarios")
        for task in selected:
            runs[f"{profile_name}:{task.scenario_id}"] = _run_scenario(
                scenario=task.payload["scenario"],
                profile=task.payload["profile"],
                theory=theory,
                checkpoint=output_root / f"{profile_name}-{task.scenario_id}.npz",
            )
    maximum_norm_drift = max(
        float(row["diagnostics"]["norm_relative_drift"]) for row in runs.values()
    )
    maximum_boundary = max(
        float(row["maximum_boundary_mass_fraction"]) for row in runs.values()
    )
    convergence = []
    for scenario_id in ("fig4_B56p45", "fig4_B56p64"):
        first = runs[f"coarse:{scenario_id}"]["final_sigma_micrometre"]
        second = runs[f"refined:{scenario_id}"]["final_sigma_micrometre"]
        convergence.append(abs(first - second) / max(abs(second), 1e-15))
    maximum_width_gap = max(convergence)
    invariant_passed = bool(
        all(row["all_values_finite"] for row in runs.values())
        and all(float(row["final_sigma_micrometre"]) > 0.0 for row in runs.values())
        and maximum_norm_drift <= float(parameters["norm_drift_maximum"])
        and 0.0 <= maximum_boundary <= 1.0
    )
    return {
        "target_id": "T008",
        "checks": {
            "two_field_solver_invariants": {
                "kind": "invariant",
                "maximum_norm_drift": maximum_norm_drift,
                "maximum_boundary_mass_fraction": maximum_boundary,
                "passed": invariant_passed,
            },
            "grid_refinement_width": {
                "kind": "convergence",
                "value": maximum_width_gap,
                "tolerance": float(parameters["width_relative_gap_maximum"]),
                "passed": maximum_width_gap
                <= float(parameters["width_relative_gap_maximum"]),
            },
        },
        "runs": runs,
        "scientific_boundary": "exact atom numbers for both Main Fig. 4 curves are unpublished",
    }


def _t012_check(
    paper_scale: dict[str, Any],
    theory: dict[str, Any],
    parameters: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    required = list(parameters["required_paper_inputs"])
    blocked = calibration_input_contract(
        {"required_paper_inputs": required, "paper_inputs": None}
    )
    complete_inputs = dict(parameters["sensitivity_input"])
    ready = calibration_input_contract(
        {"required_paper_inputs": required, "paper_inputs": complete_inputs}
    )
    schema_passed = bool(
        blocked["status"] == "input_blocked"
        and blocked["missing_paper_inputs"] == required
        and ready["status"] == "ready"
        and not ready["missing_paper_inputs"]
    )

    smoke = make_smoke_config(paper_scale)
    template = next(
        task
        for task in build_tasks(smoke)
        if task.campaign_id == "production"
        and task.payload["scenario"]["target_id"] == "T008"
    )
    scenario = copy.deepcopy(template.payload["scenario"])
    scenario["initial_total_atom_number"] = float(complete_inputs["total_atom_number"])
    scenario["initial_trap_hz"] = list(complete_inputs["initial_trap_frequencies_hz"])
    scenario["post_transfer_fraction_1"] = float(
        complete_inputs["component_populations"][0]
    ) / float(sum(complete_inputs["component_populations"]))
    scenario["interaction"]["magnetic_field_gauss"] = float(
        complete_inputs["magnetic_field_gauss"]
    )
    run = _run_scenario(
        scenario=scenario,
        profile=template.payload["profile"],
        theory=theory,
        checkpoint=output_root / "T012-sensitivity.npz",
    )
    solver_passed = bool(
        run["all_values_finite"]
        and run["final_sigma_micrometre"] > 0.0
        and float(run["diagnostics"]["norm_relative_drift"])
        <= float(parameters["norm_drift_maximum"])
        and 0.0 <= run["maximum_boundary_mass_fraction"] <= 1.0
    )
    return {
        "target_id": "T012",
        "checks": {
            "strict_missing_input_schema": {
                "kind": "parameter_audit",
                "required_paper_inputs": required,
                "passed": schema_passed,
            },
            "parameterized_solver_invariants": {
                "kind": "invariant",
                "passed": solver_passed,
                "norm_relative_drift": run["diagnostics"]["norm_relative_drift"],
                "maximum_boundary_mass_fraction": run["maximum_boundary_mass_fraction"],
                "final_sigma_micrometre": run["final_sigma_micrometre"],
            },
        },
        "sensitivity_input": complete_inputs,
        "scientific_boundary": "sensitivity inputs are declared assumptions; the paper-exact calibration field and atom number are unpublished",
    }


def run_campaign(
    config: dict[str, Any], *, workspace: Path, output_root: Path
) -> dict[str, Any]:
    if config.get("paper_id") != "1710.10890":
        raise ValueError("paper_id must be 1710.10890")
    policy = config["source_policy"]
    if any(bool(policy.get(key, True)) for key in policy):
        raise ValueError("all forbidden input flags must be false")
    paper_scale = json.loads(
        (workspace / config["paper_scale_config"]).read_text(encoding="utf-8")
    )
    validate_config(paper_scale)
    theory = json.loads(
        (workspace / config["paper_theory_config"]).read_text(encoding="utf-8")
    )
    checkpoint_root = output_root / "checks" / "discriminating_checkpoints"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    results = {
        "T008": _t008_check(
            paper_scale,
            theory,
            config["parameters"]["T008"],
            checkpoint_root,
        ),
        "T012": _t012_check(
            paper_scale,
            theory,
            config["parameters"]["T012"],
            checkpoint_root,
        ),
    }
    for result in results.values():
        result["passed"] = bool(
            len({check["kind"] for check in result["checks"].values()}) >= 2
            and all(bool(check["passed"]) for check in result["checks"].values())
        )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "purpose": "code_fault_discrimination_only",
        "target_results": results,
        "status": "passed" if all(row["passed"] for row in results.values()) else "failed",
        "scientific_coverage_changed": False,
        "source_pixels_used": False,
        "author_arrays_used": False,
        "author_code_used": False,
    }
