"""Low-cost clean-room attestation for every Anderson-paper target.

The full paper-scale eigensystem campaign remains declared in
``paper_scale.json``.  This module executes the same scientific primitives on
one tiny lattice, exercises every target projection, and records that this is
implementation evidence rather than paper-scale scientific acceptance.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np

try:
    from .paper_scale_campaign import (
        ANDERSON_TARGET_IDS,
        anderson_hamiltonian_sparse,
        build_work_units,
        describe_campaign,
        run_unit_numerics,
        work_unit_seed,
    )
except ImportError:
    from paper_scale_campaign import (  # type: ignore[no-redef]
        ANDERSON_TARGET_IDS,
        anderson_hamiltonian_sparse,
        build_work_units,
        describe_campaign,
        run_unit_numerics,
        work_unit_seed,
    )


TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 25))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _smoke_config(paper_config: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    config = copy.deepcopy(paper_config)
    config["largest_L"] = int(params["L"])
    config["selected_state_block_size"] = int(params["selected_state_block_size"])
    config["families"] = [
        {
            "family_id": "implementation_validation",
            "target_ids": list(ANDERSON_TARGET_IDS),
            "sizes": [int(params["L"])],
            "w_values": [float(params["W"])],
            "sample_count": 1,
            "operators": ["T_s", "T", "n"],
            "full_spectrum_spacing": True,
            "collect_spectral": True,
            "collect_distribution": True,
            "collect_perturbation": True,
        }
    ]
    return config


def _tiny_payload(
    paper_config: dict[str, Any], params: dict[str, Any]
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    config = _smoke_config(paper_config, params)
    unit = build_work_units(config)[0]
    rng = np.random.default_rng(work_unit_seed(int(config["seed_base"]), unit))
    hamiltonian = anderson_hamiltonian_sparse(
        unit.L,
        unit.W,
        rng,
        boundary_disorder=False,
        boundary_disorder_halfwidth=float(config["boundary_disorder_halfwidth"]),
    )
    eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian.toarray())
    return run_unit_numerics(unit, config, eigenvalues, eigenvectors), eigenvalues, eigenvectors


def _phenomenology_check(params: dict[str, Any]) -> dict[str, Any]:
    gamma = float(params["gamma"])
    omega = np.asarray(params["omega"], dtype=float)
    spectral = gamma / (omega**2 + gamma**2)
    tail_exponent = float(
        -np.polyfit(np.log(omega[-3:]), np.log(spectral[-3:]), 1)[0]
    )
    return {
        "mode": "analytic_validation",
        "positive": bool(np.all(spectral > 0)),
        "even_identity_error": float(
            np.max(np.abs(spectral - gamma / ((-omega) ** 2 + gamma**2)))
        ),
        "tail_exponent": tail_exponent,
        "passed": bool(
            np.all(spectral > 0)
            and abs(tail_exponent - 2.0) <= float(params["tail_tolerance"])
        ),
    }


def _boundary_invariance(
    paper_config: dict[str, Any], params: dict[str, Any]
) -> dict[str, Any]:
    size = int(params["L"])
    seed = int(params["seed"])
    halfwidth = float(paper_config["boundary_disorder_halfwidth"])
    plain = anderson_hamiltonian_sparse(
        size,
        float(params["W"]),
        np.random.default_rng(seed),
        boundary_disorder=False,
        boundary_disorder_halfwidth=halfwidth,
    )
    edged = anderson_hamiltonian_sparse(
        size,
        float(params["W"]),
        np.random.default_rng(seed),
        boundary_disorder=True,
        boundary_disorder_halfwidth=halfwidth,
    )
    delta = edged.diagonal() - plain.diagonal()
    expected_boundary_sites = size**3 - max(size - 2, 0) ** 3
    changed = int(np.count_nonzero(np.abs(delta) > 0))
    config = _smoke_config(paper_config, params)
    unit = build_work_units(config)[0]
    plain_values, plain_vectors = np.linalg.eigh(plain.toarray())
    edged_values, edged_vectors = np.linalg.eigh(edged.toarray())
    plain_numerics = run_unit_numerics(
        unit, config, plain_values, plain_vectors
    )
    edged_numerics = run_unit_numerics(
        unit, config, edged_values, edged_vectors
    )
    mu_key = f"{float(params['mu']):.16g}"
    plain_chi = float(
        plain_numerics["operators"]["T_s"]["susceptibility"]["regularized"][
            mu_key
        ]["tilde_chi_typ_r"]
    )
    edged_chi = float(
        edged_numerics["operators"]["T_s"]["susceptibility"]["regularized"][
            mu_key
        ]["tilde_chi_typ_r"]
    )
    relative_change = abs(edged_chi - plain_chi) / max(abs(plain_chi), 1e-300)
    claim_supported = relative_change <= float(params["relative_tolerance"])
    return {
        "mode": "reduced_validation",
        "changed_diagonal_sites": changed,
        "expected_boundary_sites": expected_boundary_sites,
        "max_boundary_shift": float(np.max(np.abs(delta))),
        "halfwidth": halfwidth,
        "mu": float(params["mu"]),
        "plain_tilde_chi_typ_r": plain_chi,
        "boundary_tilde_chi_typ_r": edged_chi,
        "relative_change": relative_change,
        "relative_tolerance": float(params["relative_tolerance"]),
        "scientific_invariance_supported_at_canary_scale": claim_supported,
        "passed": bool(
            changed == expected_boundary_sites
            and np.max(np.abs(delta)) <= halfwidth
            and np.isfinite(relative_change)
        ),
    }


def _multi_operator_susceptibility(
    target_params: dict[str, Any], tiny: dict[str, Any]
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for operator in target_params["operators"]:
        susceptibility = tiny["operators"][operator]["susceptibility"]
        regularized = susceptibility["regularized"]
        results[operator] = {
            "unregularized_tilde_chi_typ": susceptibility["unregularized"][
                "tilde_chi_typ"
            ],
            "regularized_points": len(regularized),
        }
    return {
        "mode": "reduced_validation",
        "operators": results,
        "passed": bool(
            set(results) == set(target_params["operators"])
            and all(
                np.isfinite(row["unregularized_tilde_chi_typ"])
                and row["regularized_points"] > 0
                for row in results.values()
            )
        ),
    }


def _multi_operator_spectral(
    target_params: dict[str, Any], tiny: dict[str, Any]
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for operator in target_params["operators"]:
        spectral = tiny["operators"][operator].get("spectral", {})
        counts = spectral.get("counts", [])
        results[operator] = {
            "bin_count": len(counts),
            "occupied_bins": int(sum(value > 0 for value in counts)),
        }
    return {
        "mode": "reduced_validation",
        "operators": results,
        "passed": bool(
            set(results) == set(target_params["operators"])
            and all(row["occupied_bins"] > 0 for row in results.values())
        ),
    }


def _ipr_crossover(
    paper_config: dict[str, Any], shared: dict[str, Any], target: dict[str, Any]
) -> dict[str, Any]:
    rows = []
    for disorder in target["W_values"]:
        params = dict(shared)
        params["W"] = float(disorder)
        config = _smoke_config(paper_config, params)
        unit = build_work_units(config)[0]
        hamiltonian = anderson_hamiltonian_sparse(
            unit.L,
            unit.W,
            np.random.default_rng(int(shared["seed"])),
            boundary_disorder=False,
            boundary_disorder_halfwidth=float(
                config["boundary_disorder_halfwidth"]
            ),
        )
        values, vectors = np.linalg.eigh(hamiltonian.toarray())
        numerics = run_unit_numerics(unit, config, values, vectors)
        rows.append(
            {"W": float(disorder), "central_ipr": float(numerics["central_ipr"])}
        )
    ipr_values = np.asarray([row["central_ipr"] for row in rows])
    return {
        "mode": "reduced_validation",
        "rows": rows,
        "paper_claim_W4_approx": 40.0,
        "paper_value_accepted_at_canary_scale": False,
        "passed": bool(
            np.all(np.isfinite(ipr_values)) and ipr_values[-1] > ipr_values[0]
        ),
    }


def _target_payload(
    target_id: str,
    *,
    target_params: dict[str, Any],
    shared: dict[str, Any],
    tiny: dict[str, Any],
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
    paper_config: dict[str, Any],
) -> dict[str, Any]:
    mode = target_params["mode"]
    operators = tiny["operators"]
    if mode == "eigensystem_projection":
        operator = target_params.get("operator")
        if operator is not None and operator not in operators:
            raise ValueError(f"{target_id}: missing operator {operator}")
        payload: dict[str, Any] = {
            "mode": "reduced_validation",
            "operator": operator,
            "eigenvalue_count": int(len(eigenvalues)),
            "central_ipr": float(tiny["central_ipr"]),
            "passed": bool(
                np.all(np.diff(eigenvalues) >= -1e-12)
                and 0.0 < tiny["central_ipr"] <= 1.0
            ),
        }
        if operator:
            record = operators[operator]
            payload["selected_state_count"] = int(record["selected_state_count"])
            payload["regularized_points"] = len(record["susceptibility"]["regularized"])
            payload["has_spectral"] = "spectral" in record
            payload["has_distribution"] = "chi_distribution" in record
            payload["has_perturbation"] = "localized_perturbation" in record
        return payload
    if mode == "phenomenology":
        return _phenomenology_check(target_params)
    if mode == "multi_operator_susceptibility":
        return _multi_operator_susceptibility(target_params, tiny)
    if mode == "multi_operator_spectral":
        return _multi_operator_spectral(target_params, tiny)
    if mode == "ratio_curve":
        values = [
            row["average_over_typical"]
            for row in operators["T_s"]["susceptibility"]["regularized"].values()
        ]
        return {
            "mode": "reduced_validation",
            "point_count": len(values),
            "minimum_ratio": float(min(values)),
            "passed": bool(values and all(np.isfinite(values)) and min(values) >= 1.0),
        }
    if mode == "spectral_collapse":
        spectral = operators["T_s"].get("spectral", {})
        counts = spectral.get("counts", [])
        return {
            "mode": "reduced_validation",
            "bin_count": len(counts),
            "occupied_bins": int(sum(value > 0 for value in counts)),
            "passed": bool(counts and sum(value > 0 for value in counts) > 0),
        }
    if mode == "localized_mu_curve":
        perturbation = operators["T_s"].get("localized_perturbation", {})
        return {
            "mode": "reduced_validation",
            "mu_point_count": len(perturbation),
            "passed": bool(
                perturbation
                and all(
                    np.isfinite(row["chi_typ_r"]) and row["chi_typ_r"] >= 0
                    for row in perturbation.values()
                )
            ),
        }
    if mode == "ipr_crossover":
        return _ipr_crossover(paper_config, shared, target_params)
    if mode == "boundary_invariance":
        return _boundary_invariance(
            paper_config, {**shared, **target_params}
        )
    raise ValueError(f"{target_id}: unsupported mode {mode!r}")


def run_campaign(
    config_path: Path, paper_config_path: Path, output_root: Path
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paper_config = json.loads(paper_config_path.read_text(encoding="utf-8"))
    targets = config.get("targets")
    if not isinstance(targets, dict) or tuple(sorted(targets)) != TARGET_IDS:
        raise ValueError("implementation config must declare exactly T001-T024")

    paper_description = describe_campaign(paper_config)
    if paper_description["target_ids"] != list(ANDERSON_TARGET_IDS):
        raise ValueError("paper-scale campaign target contract drifted")
    tiny, eigenvalues, eigenvectors = _tiny_payload(
        paper_config, config["shared_validation"]
    )

    results: dict[str, dict[str, Any]] = {}
    for target_id in TARGET_IDS:
        payload = _target_payload(
            target_id,
            target_params=targets[target_id],
            shared=config["shared_validation"],
            tiny=tiny,
            eigenvalues=eigenvalues,
            eigenvectors=eigenvectors,
            paper_config=paper_config,
        )
        payload.update(
            {
                "schema_version": 1,
                "paper_id": config["paper_id"],
                "target_id": target_id,
                "campaign_scale": config["campaign_scale"],
                "scientific_coverage_promoted": False,
            }
        )
        passed = bool(payload.get("passed"))
        check = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "status": "passed" if passed else "failed",
            "implementation_attestation_only": True,
            "scientific_coverage_promoted": False,
            "mode": payload["mode"],
        }
        _write_json(
            output_root / "data" / "implementation_closure" / f"{target_id}.json",
            payload,
        )
        _write_json(
            output_root / "checks" / "implementation_closure" / f"{target_id}.json",
            check,
        )
        if not passed:
            raise RuntimeError(f"{target_id}: implementation validation failed")
        results[target_id] = payload

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "campaign_scale": config["campaign_scale"],
        "target_ids": list(TARGET_IDS),
        "targets_attested": len(results),
        "paper_scale_work_units_declared": paper_description["work_unit_count"],
        "scientific_coverage_promoted": False,
        "clean_room_boundary": config["clean_room_boundary"],
    }
    _write_json(
        output_root / "checks" / "implementation_closure" / "manifest.json",
        manifest,
    )
    return manifest
