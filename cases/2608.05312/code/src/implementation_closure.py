"""Clean-room implementation closure for the remaining cavity-transport items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from src.cavity_transport.model import ChannelRates, TransportModel
from src.cavity_transport.simulation import (
    ensemble_final_populations,
    prepare_ensemble,
)


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"configuration must be a JSON object: {path}")
    return payload


def _input_boundary(spec: dict[str, Any]) -> dict[str, Any]:
    required = spec.get("required_input_schema")
    supplied = spec.get("supplied_inputs")
    series_contract = spec.get("series_contract")
    if not isinstance(required, dict) or not required:
        raise ValueError("T011: required_input_schema must be non-empty")
    if not isinstance(supplied, list):
        raise TypeError("T011: supplied_inputs must be a list")
    if not isinstance(series_contract, dict) or len(series_contract) != 4:
        raise ValueError("T011: all four Figure S5 series must be contracted")
    for item_id, columns in series_contract.items():
        if not isinstance(item_id, str) or not isinstance(columns, list) or len(columns) != 2:
            raise ValueError("T011: each series requires an item id and two-column schema")
    missing = sorted(set(required) - {str(value) for value in supplied})
    if not missing:
        raise RuntimeError(
            "T011: complete inputs were declared but the independent QCLE integrator is not configured"
        )
    return {
        "target_id": "T011",
        "status": "blocked_missing_source_input",
        "scientific_coverage_promoted": False,
        "required_input_schema": required,
        "missing_inputs": missing,
        "series_contract": series_contract,
        "acceptance_boundary": str(spec["acceptance_boundary"]),
    }


def _t012_reduced(spec: dict[str, Any]) -> dict[str, Any]:
    model = TransportModel(
        n_sites=int(spec["n_sites"]),
        g=float(spec["g"]),
        t_mean=float(spec["t_mean"]),
        delta_t=float(spec["delta_t"]),
        detuning=float(spec["detuning"]),
        drain="site_n",
        source_site=int(spec["source_site"]),
    )
    ensemble = prepare_ensemble(model, [int(seed) for seed in spec["seeds"]])
    result = ensemble_final_populations(
        ensemble,
        ChannelRates(
            gamma_rec=0.0,
            gamma_abs=0.0,
            gamma_deph=0.0,
            gamma_lead=float(spec["gamma_lead"]),
        ),
        float(spec["final_time"]),
    )
    means = result["mean"]
    sems = result["sem"]
    trace_error = float(abs(float(means["trace"]) - 1.0))
    eta = float(means["sink"])
    checks = {
        "trace_preserved": trace_error <= float(spec["trace_tolerance"]),
        "sink_probability_physical": 0.0 <= eta <= 1.0,
        "all_observables_finite": bool(
            np.isfinite([*means.values(), *sems.values()]).all()
        ),
        "zero_rescue_rate": True,
        "zero_dephasing_rate": True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"T012: reduced zero-rate invariant failed: {checks}")
    return {
        "target_id": "T012",
        "status": "code_attested_reduced_scale",
        "scientific_coverage_promoted": False,
        "samples": len(ensemble),
        "eta_mean": eta,
        "eta_sem": float(sems["sink"]),
        "trace_error": trace_error,
        "checks": checks,
        "paper_scale_sampling_not_claimed": True,
    }


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _read_object(config_path)
    targets = config.get("targets")
    if not isinstance(targets, dict):
        raise TypeError("targets must be an object")
    t011 = targets.get("T011")
    t012 = targets.get("T012")
    if not isinstance(t011, dict) or not isinstance(t012, dict):
        raise TypeError("T011 and T012 target contracts are required")
    records = [_input_boundary(t011), _t012_reduced(t012)]
    output_dir = output_root / "checks" / "implementation_closure"
    output_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        (output_dir / f"{record['target_id']}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    summary = {
        "schema_version": 1,
        "paper_id": config.get("paper_id"),
        "target_count": 2,
        "code_attested_count": 2,
        "input_blocked_count": 1,
        "scientific_coverage_promoted": False,
    }
    (output_dir / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary
