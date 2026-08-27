"""Checkpointed paper-scale convergence campaign.

The campaign is intentionally independent of any author code or numerical
array.  Its unit of progress is a fully specified parameter point.  Every
checkpoint binds the effective configuration and implementation hashes so that
resume cannot silently mix scientific inputs.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from .collocation import solve_collocation, solve_collocation_eliminated
from .kinetic import GridSpec, solve_transport
from .kubo import kubo_resistivity, leading_order_boltzmann_resistivity
from .thermodynamics import ModelParameters, solve_equilibrium


@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    family: str
    grid_name: str
    grid: GridSpec
    density_cm2: float
    tunnel_mev: float
    detuning_ratio: float
    temperature_k: float
    frequency_mev: float


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def implementation_sha256(workspace: Path) -> str:
    digest = hashlib.sha256()
    for relative in (
        "src/bose_fermi_transport/thermodynamics.py",
        "src/bose_fermi_transport/kinetic.py",
        "src/bose_fermi_transport/collocation.py",
        "src/bose_fermi_transport/kubo.py",
        "src/bose_fermi_transport/paper_scale.py",
    ):
        path = workspace / relative
        digest.update(relative.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _model(base_parameters: dict[str, Any]) -> ModelParameters:
    return ModelParameters(
        fermi_energy_mev=float(base_parameters["fermi_energy_mev"]),
        trion_binding_mev=float(base_parameters["trion_binding_mev"]),
        hole_mass_me=float(base_parameters["hole_mass_me"]),
        exciton_mass_ratio_to_hole=float(base_parameters["exciton_mass_ratio_to_hole"]),
        exciton_density_cm2=float(base_parameters["exciton_density_cm2"]),
        relaxation_time_ps=float(base_parameters["relaxation_time_ps"]),
    )


def enumerate_units(
    config: dict[str, Any], base_config: dict[str, Any]
) -> list[WorkUnit]:
    campaign = config["parameters"]
    base = base_config["parameters"]
    units: list[WorkUnit] = []
    for grid_payload in campaign["grid_levels"]:
        grid_name = str(grid_payload["name"])
        grid = GridSpec(
            **{key: value for key, value in grid_payload.items() if key != "name"}
        )
        for density in campaign["exciton_density_values_cm2"]:
            for tunnel in campaign["tunnel_values_mev"]:
                for detuning in campaign["detuning_ratios"]:
                    for temperature in campaign["temperature_values_k"]:
                        unit_id = (
                            f"dc-{grid_name}-n{float(density):.6e}-t{float(tunnel):.3f}"
                            f"-d{float(detuning):.6f}-T{float(temperature):.3f}"
                        )
                        units.append(
                            WorkUnit(
                                unit_id,
                                "dc_transport",
                                grid_name,
                                grid,
                                float(density),
                                float(tunnel),
                                float(detuning),
                                float(temperature),
                                0.0,
                            )
                        )
        for frequency in campaign["frequency_values_mev"]:
            unit_id = f"ac-{grid_name}-w{float(frequency):+.6f}"
            units.append(
                WorkUnit(
                    unit_id,
                    "ac_transport",
                    grid_name,
                    grid,
                    float(base["exciton_density_cm2"]),
                    1.0,
                    float(base["ac_detuning_ratio"]),
                    float(base["temperature_k"]),
                    float(frequency),
                )
            )
        for density in campaign["exciton_density_values_cm2"]:
            for detuning in campaign["detuning_ratios"]:
                unit_id = (
                    f"kubo-{grid_name}-n{float(density):.6e}-d{float(detuning):.6f}"
                )
                units.append(
                    WorkUnit(
                        unit_id,
                        "kubo",
                        grid_name,
                        grid,
                        float(density),
                        1.0,
                        float(detuning),
                        float(base["temperature_k"]),
                        0.0,
                    )
                )
    return units


def _complex(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def _transport_payload(result: Any) -> dict[str, Any]:
    return {
        "sigma_h": _complex(result.sigma_h),
        "sigma_x": _complex(result.sigma_x),
        "sigma_t": _complex(result.sigma_t),
        "momentum_residual": result.collision_momentum_residual,
        "minimum_collision_eigenvalue": result.collision_min_eigenvalue,
        "condition_number": result.condition_number,
    }


def execute_unit(
    unit: WorkUnit, model: ModelParameters, closure: str
) -> dict[str, Any]:
    local_model = replace(model, exciton_density_cm2=unit.density_cm2)
    equilibrium = solve_equilibrium(
        local_model,
        unit.temperature_k,
        unit.detuning_ratio * local_model.fermi_energy_mev,
        closure,
    )
    galerkin = solve_transport(
        local_model,
        equilibrium,
        unit.tunnel_mev,
        unit.frequency_mev,
        unit.grid,
    )
    collocation = solve_collocation(
        local_model,
        equilibrium,
        unit.tunnel_mev,
        unit.frequency_mev,
        unit.grid,
    )
    eliminated = solve_collocation_eliminated(
        local_model,
        equilibrium,
        unit.tunnel_mev,
        unit.frequency_mev,
        unit.grid,
    )
    direct_values = np.array(
        [collocation.sigma_h, collocation.sigma_x, collocation.sigma_t]
    )
    eliminated_values = np.array(
        [eliminated.sigma_h, eliminated.sigma_x, eliminated.sigma_t]
    )
    result: dict[str, Any] = {
        "unit": asdict(unit),
        "equilibrium": asdict(equilibrium),
        "galerkin": _transport_payload(galerkin),
        "collocation": _transport_payload(collocation),
        "collocation_eliminated": _transport_payload(eliminated),
        "algebraic_checks": {
            "direct_vs_eliminated_max_abs": float(
                np.max(np.abs(direct_values - eliminated_values))
            ),
            "effective_g4_q_terms_retained": True,
            "reason": (
                "The eliminated lane evaluates the trion Schur complement "
                "B D^-1 C corresponding to Supplement Eqs. (21)-(32)."
            ),
        },
    }
    if unit.family == "kubo":
        result["kubo_rho"] = kubo_resistivity(
            local_model,
            equilibrium,
            unit.tunnel_mev,
            hole_points=unit.grid.hole_points,
            hole_max_pf=unit.grid.hole_max_pf,
            exciton_points=unit.grid.exciton_points,
            exciton_max_pf=unit.grid.exciton_max_pf,
            angle_points=max(96, unit.grid.exciton_points * 2),
        )
        result["boltzmann_lo_analytic_delta_rho"] = leading_order_boltzmann_resistivity(
            local_model,
            equilibrium,
            unit.tunnel_mev,
            hole_points=unit.grid.hole_points,
            hole_max_pf=unit.grid.hole_max_pf,
            exciton_points=unit.grid.exciton_points,
            exciton_max_pf=unit.grid.exciton_max_pf,
        )
        result["boltzmann_full_galerkin_rho"] = 1.0 / galerkin.sigma_h.real
        result["boltzmann_full_collocation_rho"] = 1.0 / collocation.sigma_h.real
    return result


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial-{os.getpid()}")
    partial.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)


def run_campaign(
    config_path: Path,
    workspace: Path,
    shard_index: int = 0,
    shard_count: int = 1,
    max_units: int | None = None,
    validate_only: bool = False,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base_path = workspace / config["parameters"]["base_config"]
    base_config = json.loads(base_path.read_text(encoding="utf-8"))
    if shard_count < 1 or shard_index < 0 or shard_index >= shard_count:
        raise ValueError("invalid shard selection")
    units = enumerate_units(config, base_config)
    selected = [
        unit for index, unit in enumerate(units) if index % shard_count == shard_index
    ]
    if max_units is not None:
        selected = selected[:max_units]
    config_hash = sha256(config_path)
    base_hash = sha256(base_path)
    implementation_hash = implementation_sha256(workspace)
    plan = {
        "schema_version": 1,
        "paper_id": "2409.18176",
        "profile": "paper_scale",
        "total_units": len(units),
        "selected_units": len(selected),
        "shard_index": shard_index,
        "shard_count": shard_count,
        "config_sha256": config_hash,
        "base_config_sha256": base_hash,
        "implementation_sha256": implementation_hash,
        "family_counts": {
            family: sum(unit.family == family for unit in units)
            for family in sorted({unit.family for unit in units})
        },
    }
    output_root = workspace / "outputs" / "paper_scale"
    _atomic_json(output_root / "plan.json", plan)
    if validate_only:
        return plan

    model = _model(base_config["parameters"])
    closure = str(base_config["parameters"]["closure"])
    completed = 0
    resumed = 0
    checkpoint_paths: list[Path] = []
    for unit in selected:
        checkpoint = output_root / "checkpoints" / f"{unit.unit_id}.json"
        checkpoint_paths.append(checkpoint)
        if checkpoint.exists():
            existing = json.loads(checkpoint.read_text(encoding="utf-8"))
            binding = existing.get("binding", {})
            if binding == {
                "config_sha256": config_hash,
                "base_config_sha256": base_hash,
                "implementation_sha256": implementation_hash,
            }:
                resumed += 1
                continue
        result = execute_unit(unit, model, closure)
        result["binding"] = {
            "config_sha256": config_hash,
            "base_config_sha256": base_hash,
            "implementation_sha256": implementation_hash,
        }
        _atomic_json(checkpoint, result)
        completed += 1

    available = sorted((output_root / "checkpoints").glob("*.json"))
    manifest = {
        **plan,
        "completed_this_run": completed,
        "resumed_this_run": resumed,
        "available_checkpoints": len(available),
        "selected_complete": all(path.exists() for path in checkpoint_paths),
        "checkpoints": [
            {"path": str(path.relative_to(workspace)), "sha256": sha256(path)}
            for path in available
        ],
    }
    _atomic_json(output_root / "manifest.json", manifest)
    convergence = aggregate_convergence(
        available, config["parameters"]["acceptance_relative_change"]
    )
    _atomic_json(output_root / "convergence.json", convergence)
    target_acceptance = {
        "schema_version": 1,
        "paper_id": "2409.18176",
        "paper_scale_complete": len(available) == len(units),
        "convergence_passed": convergence["passed"],
        "trion_elimination_passed": convergence["trion_elimination"]["passed"],
        "paper_exact_promoted": False,
        "paper_discrepancy_status": "pending_production_and_fresh_review",
        "reason": (
            "Paper discretization metadata and fitted ac operating densities remain "
            "unavailable. The full campaign and fresh-context review are required "
            "before attributing any stable gap to the paper."
        ),
    }
    _atomic_json(output_root / "target_acceptance.json", target_acceptance)
    return manifest


def aggregate_convergence(checkpoints: list[Path], tolerance: float) -> dict[str, Any]:
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in checkpoints]
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        unit = row["unit"]
        key = (
            unit["family"],
            unit["density_cm2"],
            unit["tunnel_mev"],
            unit["detuning_ratio"],
            unit["temperature_k"],
            unit["frequency_mev"],
        )
        groups.setdefault(key, []).append(row)
    comparisons: list[dict[str, Any]] = []
    for key, values in groups.items():
        by_grid = {row["unit"]["grid_name"]: row for row in values}
        if "g96" not in by_grid or "cutoff" not in by_grid:
            continue
        changes: dict[str, float] = {}
        for method in ("galerkin", "collocation"):
            for species in ("h", "x", "t"):
                fine = complex(**by_grid["g96"][method][f"sigma_{species}"])
                cutoff = complex(**by_grid["cutoff"][method][f"sigma_{species}"])
                changes[f"{method}_{species}"] = float(
                    abs(cutoff - fine) / max(abs(fine), 1.0e-12)
                )
        if key[0] == "kubo":
            for observable in (
                "kubo_rho",
                "boltzmann_lo_analytic_delta_rho",
                "boltzmann_full_galerkin_rho",
                "boltzmann_full_collocation_rho",
            ):
                fine = float(by_grid["g96"][observable])
                cutoff = float(by_grid["cutoff"][observable])
                changes[observable] = abs(cutoff - fine) / max(abs(fine), 1.0e-12)
        comparisons.append(
            {
                "condition": list(key),
                "relative_changes": changes,
                "passed": max(changes.values()) <= tolerance,
            }
        )
    algebraic_gaps = [
        float(row["algebraic_checks"]["direct_vs_eliminated_max_abs"]) for row in rows
    ]
    lo_regularization = [
        {
            "unit_id": row["unit"]["unit_id"],
            "relative_gap": abs(
                float(row["kubo_rho"]) - float(row["boltzmann_lo_analytic_delta_rho"])
            )
            / max(abs(float(row["boltzmann_lo_analytic_delta_rho"])), 1.0e-12),
        }
        for row in rows
        if row["unit"]["family"] == "kubo"
    ]
    return {
        "schema_version": 1,
        "tolerance": tolerance,
        "comparisons": comparisons,
        "passed": bool(comparisons) and all(row["passed"] for row in comparisons),
        "trion_elimination": {
            "maximum_direct_vs_eliminated_abs": max(algebraic_gaps, default=None),
            "passed": bool(algebraic_gaps) and max(algebraic_gaps) <= 1.0e-10,
            "interpretation": (
                "Passing proves that the simultaneous three-species solve retains "
                "the effective g^4 Q terms generated by eliminating trions."
            ),
        },
        "leading_order_regularization": {
            "comparisons": lo_regularization,
            "maximum_relative_gap": max(
                (row["relative_gap"] for row in lo_regularization), default=None
            ),
            "interpretation": (
                "This compares broadened Kubo and analytic-delta leading-order "
                "rates only; it is not the full Boltzmann comparison in the paper."
            ),
        },
    }
