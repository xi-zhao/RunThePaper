#!/usr/bin/env python3
"""Run fast, independent scientific checks for all four reproduction targets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from pxp_scars import (  # noqa: E402
    build_basis,
    build_hamiltonian,
    build_symmetric_hamiltonian,
    build_symmetric_sector,
    fibonacci,
    fsa_basis_and_matrix,
    make_dynamics_data,
    pattern_state,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def safe_ref(value: str, root: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != (root,):
        raise ValueError(f"path must stay under {root}/: {value}")
    return path


def main() -> int:
    args = parse_args()
    config_ref = safe_ref(args.config, "config")
    output_ref = safe_ref(args.output, "outputs")
    config = json.loads((WORKSPACE / config_ref).read_text(encoding="utf-8"))

    graph_l = int(config["graph_system_size"])
    smoke_l = int(config["smoke_system_size"])
    graph_basis = build_basis(graph_l, periodic=True)
    graph_h = build_hamiltonian(graph_basis)
    expected_graph_dim = fibonacci(graph_l - 1) + fibonacci(graph_l + 1)

    dynamics = make_dynamics_data(WORKSPACE, L=smoke_l)
    z2 = dynamics["summary"]["z2"]
    vacuum = dynamics["summary"]["vacuum"]
    period = float(z2["correlation_period_mean"])

    basis = build_basis(smoke_l, periodic=True)
    hamiltonian = build_hamiltonian(basis)
    fsa = fsa_basis_and_matrix(basis, hamiltonian, pattern_state(smoke_l, "z2"))
    fsa_error = float(np.linalg.norm(fsa["projected_matrix"] - fsa["matrix"]))

    sector_checks = []
    for size in config["sector_validation_sizes"]:
        size = int(size)
        sector = build_symmetric_sector(size)
        sector_h = build_symmetric_hamiltonian(sector).toarray()
        full = np.linalg.eigvalsh(build_hamiltonian(build_basis(size)).toarray())
        sector_values = np.linalg.eigvalsh(sector_h)
        max_subset_error = max(float(np.min(np.abs(full - value))) for value in sector_values)
        sector_checks.append(
            {
                "L": size,
                "dimension": len(sector["representatives"]),
                "symmetry_error": float(np.max(np.abs(sector_h - sector_h.T))),
                "spectrum_subset_error": max_subset_error,
            }
        )

    gate_flags = {
        "T001_graph_dimension_and_hermiticity": len(graph_basis.states) == expected_graph_dim
        and (graph_h - graph_h.T).nnz == 0,
        "T002_z2_slow_growth_and_revival": float(z2["entropy_slope_early_time"])
        < float(vacuum["entropy_slope_early_time"])
        and float(z2["max_return_after_t1"]) > float(vacuum["max_return_after_t1"])
        and abs(period - float(config["paper_revival_period"]))
        <= float(config["revival_period_tolerance"]),
        "T003_fsa_chain_closes": int(fsa["matrix"].shape[0]) == smoke_l + 1 and fsa_error < 1e-10,
        "T004_sector_construction_exact": all(
            row["symmetry_error"] < 1e-12 and row["spectrum_subset_error"] < 1e-9
            for row in sector_checks
        ),
    }
    payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "target_ids": config["target_ids"],
        "status": "passed" if all(gate_flags.values()) else "failed",
        "resolved_parameters": config,
        "observables": {
            "graph_dimension": len(graph_basis.states),
            "graph_edges": int(graph_h.nnz // 2),
            "z2_entropy_slope": z2["entropy_slope_early_time"],
            "vacuum_entropy_slope": vacuum["entropy_slope_early_time"],
            "z2_revival_period": period,
            "z2_max_return": z2["max_return_after_t1"],
            "vacuum_max_return": vacuum["max_return_after_t1"],
            "fsa_dimension": int(fsa["matrix"].shape[0]),
            "fsa_projected_error": fsa_error,
            "sector_checks": sector_checks,
        },
        "gate_flags": gate_flags,
        "boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "scale": "independent_reduced_scale_validation"
        }
    }
    output = WORKSPACE / output_ref
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
