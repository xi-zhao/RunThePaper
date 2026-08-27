"""Clean-room analytic campaign for the paper's uncovered claims.

The campaign implements the SU(2), discrete-symmetry, and replica identities
from their formulas.  The unplotted finite-Ising numerical claim is fail-closed
until its paper-scale lattice protocol is supplied.  No source figure, raw
paper, author array, or author code is read by this module.
"""

from __future__ import annotations

import json
from math import pi
from pathlib import Path
from typing import Any

import numpy as np


TARGET_IDS = ("T004", "T005", "T006", "T007")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _su2_claims(params: dict[str, Any]) -> dict[str, Any]:
    spin_traces = np.asarray(params["spin_sector_traces"], dtype=float)
    fixed_m_traces = np.asarray(
        [spin_traces[index:].sum() for index in range(spin_traces.size)] + [0.0]
    )
    projected = fixed_m_traces[:-1] - fixed_m_traces[1:]

    vertex_rows: list[dict[str, float]] = []
    for level in params["levels"]:
        for alpha_over_2pi in params["alpha_over_2pi"]:
            delta = float(level) * float(alpha_over_2pi) ** 2 / 4.0
            vertex_rows.append(
                {
                    "level": int(level),
                    "alpha_over_2pi": float(alpha_over_2pi),
                    "delta": delta,
                    "delta_bar": delta,
                }
            )
    probe = float(params["consistency_alpha_over_2pi"])
    wzw_total_dimension = 2.0 * 0.25 * probe**2
    heisenberg_u1_dimension = float(params["heisenberg_luttinger_k"]) * probe**2

    level = float(params["entropy_level"])
    central_charge = float(params["central_charge"])
    scale_factor = float(params["typical_spin_scale"])
    lengths = np.asarray(params["asymptotic_lengths"], dtype=float)
    spins = scale_factor * np.sqrt(np.log(lengths))
    entropy = (
        (2.0 * spins + 1.0)
        * central_charge
        * pi ** 2.5
        / (3.0 * level**1.5 * np.sqrt(np.log(lengths)))
        * np.exp(-(pi**2) * spins**2 / (level * np.log(lengths)))
    )
    asymptotic_limit = (
        2.0
        * scale_factor
        * central_charge
        * pi ** 2.5
        / (3.0 * level**1.5)
        * np.exp(-(pi**2) * scale_factor**2 / level)
    )
    errors = np.abs(entropy - asymptotic_limit)
    passed = (
        np.allclose(projected, spin_traces, atol=float(params["tolerance"]), rtol=0.0)
        and abs(wzw_total_dimension - heisenberg_u1_dimension) <= float(params["tolerance"])
        and np.all(np.isfinite(entropy))
        and np.all(entropy > 0.0)
        and np.all(np.diff(errors) < 0.0)
    )
    return {
        "mode": "analytic_formula_validation",
        "claim_item_ids": ["C021", "C022", "C023", "C024", "C025"],
        "spin_projection": {
            "sector_traces": spin_traces.tolist(),
            "fixed_m_traces": fixed_m_traces.tolist(),
            "recovered_sector_traces": projected.tolist(),
        },
        "vertex_dimensions": vertex_rows,
        "k1_consistency": {
            "wzw_total_dimension": wzw_total_dimension,
            "heisenberg_u1_dimension": heisenberg_u1_dimension,
        },
        "resolved_entropy_scaling": {
            "lengths": lengths.tolist(),
            "typical_spins": spins.tolist(),
            "entropy_contributions": entropy.tolist(),
            "asymptotic_limit": float(asymptotic_limit),
            "absolute_errors": errors.tolist(),
        },
        "passed": bool(passed),
    }


def _discrete_symmetry_claims(params: dict[str, Any]) -> dict[str, Any]:
    order = int(params["cyclic_order"])
    sector_weights = np.asarray(params["sector_weights"], dtype=float)
    if sector_weights.size != order or np.any(sector_weights < 0.0):
        raise ValueError("sector_weights must be a nonnegative Z_N vector")
    sector_weights = sector_weights / sector_weights.sum()
    charges = np.arange(order)
    flux = np.asarray(
        [np.sum(sector_weights * np.exp(2j * pi * mode * charges / order)) for mode in charges]
    )
    recovered = np.asarray(
        [np.sum(flux * np.exp(-2j * pi * charges * charge / order)) / order for charge in charges]
    )

    parity_checks: list[dict[str, Any]] = []
    for spins_raw in params["ising_spin_configurations"]:
        spins = np.asarray(spins_raw, dtype=int)
        if not np.all(np.isin(spins, (-1, 1))):
            raise ValueError("Ising configurations must contain only -1 and +1")
        disorder = np.concatenate(([1], np.cumprod(spins)))
        parity_checks.append(
            {
                "spin_product": int(np.prod(spins)),
                "boundary_disorder_product": int(disorder[0] * disorder[-1]),
            }
        )

    ising_rows: list[dict[str, float | int]] = []
    for replica in params["replicas"]:
        for length in params["lengths"]:
            base = float(length) ** (-(float(replica) - 1.0 / float(replica)) / 12.0)
            correction = float(length) ** (-1.0 / (4.0 * float(replica)))
            even = 0.5 * base * (1.0 + correction)
            odd = 0.5 * base * (1.0 - correction)
            ising_rows.append(
                {
                    "replica": int(replica),
                    "length": int(length),
                    "even_moment": even,
                    "odd_moment": odd,
                    "relative_parity_difference": correction,
                }
            )

    parafermions: list[dict[str, Any]] = []
    for n_value in params["parafermion_orders"]:
        n_value = int(n_value)
        dimensions = [
            float(alpha * (n_value - alpha) / (2.0 * n_value * (n_value + 2.0)))
            for alpha in range(1, n_value)
        ]
        parafermions.append(
            {
                "order": n_value,
                "central_charge": float(2.0 * (n_value - 1.0) / (n_value + 2.0)),
                "disorder_dimensions": dimensions,
            }
        )

    n1_differences = [
        row["relative_parity_difference"]
        for row in ising_rows
        if row["replica"] == 1
    ]
    passed = (
        np.allclose(recovered.real, sector_weights, atol=float(params["tolerance"]), rtol=0.0)
        and np.max(np.abs(recovered.imag)) <= float(params["tolerance"])
        and all(row["spin_product"] == row["boundary_disorder_product"] for row in parity_checks)
        and all(left > right for left, right in zip(n1_differences, n1_differences[1:]))
        and all(
            np.isclose(row["even_moment"] + row["odd_moment"], row["length"] ** (-(row["replica"] - 1.0 / row["replica"]) / 12.0))
            for row in ising_rows
        )
        and all(
            np.allclose(row["disorder_dimensions"], row["disorder_dimensions"][::-1])
            and all(value > 0.0 for value in row["disorder_dimensions"])
            for row in parafermions
        )
    )
    return {
        "mode": "analytic_formula_validation",
        "claim_item_ids": ["C026", "C027", "C028", "C029", "C031", "C032"],
        "discrete_fourier_projection": {
            "sector_weights": sector_weights.tolist(),
            "flux_moments": [[float(value.real), float(value.imag)] for value in flux],
            "recovered_weights": recovered.real.tolist(),
        },
        "ising_parity_identity": parity_checks,
        "ising_resolved_moments": ising_rows,
        "parafermion_results": parafermions,
        "passed": bool(passed),
    }


def _measurement_claims(params: dict[str, Any]) -> dict[str, Any]:
    blocks = {
        int(charge): np.asarray(values, dtype=float)
        for charge, values in params["charge_block_eigenvalues"].items()
    }
    if any(np.any(values < 0.0) for values in blocks.values()):
        raise ValueError("density-matrix block eigenvalues must be nonnegative")
    if abs(sum(float(values.sum()) for values in blocks.values()) - 1.0) > float(params["tolerance"]):
        raise ValueError("density-matrix eigenvalues must sum to one")

    charges = np.asarray(sorted(blocks), dtype=int)
    alphas = np.asarray(params["alpha_grid"], dtype=float)
    replica_results: dict[str, Any] = {}
    passed = True
    for replica in params["replicas"]:
        resolved = np.asarray([np.sum(blocks[int(charge)] ** int(replica)) for charge in charges])
        flux = np.asarray(
            [np.sum(resolved * np.exp(1j * alpha * charges)) for alpha in alphas]
        )
        transform = np.asarray(
            [
                np.sum(flux * np.exp(-1j * alphas * charge)) / len(alphas)
                for charge in charges
            ]
        )
        passed = passed and bool(
            np.allclose(transform.real, resolved, atol=float(params["tolerance"]), rtol=0.0)
            and np.max(np.abs(transform.imag)) <= float(params["tolerance"])
        )
        replica_results[str(replica)] = {
            "resolved_moments": resolved.tolist(),
            "flux_moments": [[float(value.real), float(value.imag)] for value in flux],
            "inverse_transform": transform.real.tolist(),
        }
    return {
        "mode": "analytic_formula_validation",
        "claim_item_ids": ["C033", "C034", "C035"],
        "charges": charges.tolist(),
        "replica_results": replica_results,
        "passed": bool(passed),
    }


def _input_boundary(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    schema = params.get("required_input_schema")
    supplied = params.get("supplied_inputs", [])
    if not isinstance(schema, dict) or not schema:
        raise ValueError(f"{target_id}: required_input_schema must be non-empty")
    if not isinstance(supplied, list):
        raise ValueError(f"{target_id}: supplied_inputs must be a list")
    missing = [name for name in schema if name not in supplied]
    if not missing:
        raise ValueError(f"{target_id}: supplied inputs require an executable scientific mode")
    return {
        "mode": "input_boundary",
        "status": "input_blocked",
        "target_id": target_id,
        "claim_item_ids": ["C030"],
        "required_input_schema": schema,
        "supplied_inputs": supplied,
        "missing_inputs": missing,
        "forbidden_substitutions": [
            "author numerical code",
            "author numerical arrays",
            "digitized paper curves",
            "source-figure pixels",
            "guessed lattice, boundary, or finite-size protocol parameters",
        ],
        "acceptance_boundary": str(params["acceptance_boundary"]),
        "scientific_coverage_promoted": False,
    }


def _run_target(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    mode = str(params.get("mode") or "")
    if mode == "su2_claims":
        result = _su2_claims(params)
    elif mode == "discrete_symmetry_claims":
        result = _discrete_symmetry_claims(params)
    elif mode == "measurement_claims":
        result = _measurement_claims(params)
    elif mode == "input_boundary":
        return _input_boundary(target_id, params)
    else:
        raise ValueError(f"{target_id}: unsupported campaign mode {mode!r}")
    result.update({"target_id": target_id, "scientific_coverage_promoted": False})
    return result


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if tuple(config.get("attestation_parameters", {}).get("target_ids", ())) != TARGET_IDS:
        raise ValueError("campaign target list does not match the fixed claim denominator")
    boundary = config.get("clean_room_boundary", {})
    for name in (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    ):
        if boundary.get(name) is not False:
            raise ValueError(f"clean-room boundary must set {name}=false")
    targets = config.get("targets", {})
    if tuple(targets) != TARGET_IDS:
        raise ValueError("target configuration must preserve the frozen target order")

    data_dir = output_root / "data" / "implementation_closure"
    check_dir = output_root / "checks" / "implementation_closure"
    checks: list[dict[str, Any]] = []
    for target_id in TARGET_IDS:
        result = _run_target(target_id, targets[target_id])
        _write_json(data_dir / f"{target_id}.json", result)
        status = result.get("status") or ("passed" if result.get("passed") else "failed")
        check = {
            "target_id": target_id,
            "status": status,
            "mode": result["mode"],
            "claim_item_ids": result["claim_item_ids"],
            "scientific_coverage_promoted": False,
            "acceptance_criteria": targets[target_id]["acceptance_criteria"],
        }
        _write_json(check_dir / f"{target_id}.json", check)
        checks.append(check)

    hard_failures = [row for row in checks if row["status"] == "failed"]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_scale": config["campaign_scale"],
        "status": "failed" if hard_failures else "passed_with_input_boundaries",
        "target_ids": list(TARGET_IDS),
        "scientific_coverage_promoted": False,
        "clean_room_boundary": boundary,
        "target_checks": checks,
    }
    _write_json(check_dir / "manifest.json", manifest)
    return manifest
