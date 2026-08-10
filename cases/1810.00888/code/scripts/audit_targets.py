#!/usr/bin/env python3
"""Audit all nine paper targets and write machine-readable scientific evidence."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from exact_scars.evidence import (  # noqa: E402
    consecutive_negative_tower,
    fsa_primary_overlaps,
)


def _close(values: list[float], expected: list[float], tolerance: float) -> bool:
    return bool(np.allclose(values, expected, atol=tolerance, rtol=0.0))


def main() -> int:
    manifest = json.loads(
        (WORKSPACE / "outputs/checks/run_manifest.json").read_text(encoding="utf-8")
    )
    profile = json.loads(
        (WORKSPACE / "outputs/checks/profile_formula_crosscheck.json").read_text(
            encoding="utf-8"
        )
    )

    with np.load(
        WORKSPACE / "outputs/data/T003_obc_tower.npz", allow_pickle=False
    ) as data:
        gamma_energies = sorted(float(value) for value in data["gamma"][:, 0])
    with np.load(
        WORKSPACE / "outputs/data/T004_overlaps.npz", allow_pickle=False
    ) as data:
        xi_tower = consecutive_negative_tower(data, prefix="xi", count=13)
    with np.load(WORKSPACE / "outputs/data/T005_fsa.npz", allow_pickle=False) as data:
        fsa_targets = fsa_primary_overlaps(data)

    expected_xi = [
        0.63,
        0.78,
        0.89,
        0.92,
        0.92,
        0.90,
        0.86,
        0.79,
        0.72,
        0.62,
        0.50,
        0.32,
        0.09,
    ]
    computed_xi = [float(item["overlap"]) for item in xi_tower]
    expected_fsa = [
        0.98,
        0.99,
        0.89,
        0.81,
        0.76,
        0.74,
        0.73,
        0.72,
        0.71,
        0.71,
        0.70,
        0.68,
        0.69,
        0.87,
    ]
    computed_fsa = [float(item["overlap"]) for item in fsa_targets[:14]]

    target_results = manifest["targets"]
    t006_values = list(target_results["T006"]["maximum_overlaps"].values())
    t007_values = list(target_results["T007"]["maximum_overlaps"].values())
    t009_values = list(target_results["T009"]["maximum_overlaps"])
    checks = {
        "T001": {
            "paper_length": target_results["T001"]["length"] == 50,
            "zero_total_energy": max(
                abs(value)
                for value in target_results["T001"]["integrated_energies"].values()
            )
            < 1.0e-12,
            "formula_vs_direct_mps": max(
                profile["maximum_formula_vs_mps_error"][name]
                for name in ("gamma_11", "gamma_22")
            )
            < 2.0e-12,
        },
        "T002": {
            "paper_length": target_results["T002"]["length"] == 50,
            "energies_plus_minus_sqrt2": _close(
                sorted(target_results["T002"]["integrated_energies"].values()),
                [-np.sqrt(2.0), np.sqrt(2.0)],
                1.0e-12,
            ),
            "formula_vs_direct_mps": max(
                profile["maximum_formula_vs_mps_error"][name]
                for name in ("gamma_12", "gamma_21")
            )
            < 2.0e-12,
        },
        "T003": {
            "paper_length": target_results["T003"]["length"] == 18,
            "complete_symmetry_sector_dimensions": target_results["T003"][
                "sector_dimensions"
            ]
            == {"even": 3410, "odd": 3355},
            "exact_gamma_energies": _close(
                gamma_energies, [-np.sqrt(2.0), np.sqrt(2.0)], 1.0e-12
            ),
            "eigenstate_residual": max(
                target_results["T003"]["gamma_residuals"].values()
            )
            < 1.0e-12,
        },
        "T004": {
            "paper_length": target_results["T004"]["length"] == 26,
            "all_13_series": len(xi_tower) == 13,
            "consecutive_scar_energies": bool(
                np.all(np.diff([float(item["energy"]) for item in xi_tower]) < 0.0)
            ),
            "printed_overlap_annotations": _close(computed_xi, expected_xi, 0.015),
            "high_particle_split_weight_handled": all(
                float(item["overlap"]) < float(item["global_maximum_overlap"])
                for item in xi_tower[-2:]
            ),
        },
        "T005": {
            "paper_length": target_results["T005"]["length"] == 26,
            "all_27_fsa_states": target_results["T005"]["fsa_states"] == 27,
            "printed_negative_tower_annotations": _close(
                computed_fsa, expected_fsa, 0.015
            ),
            "zero_subspace_basis_invariant": fsa_targets[13]["aggregation"]
            == "zero_energy_subspace_sum",
            "particle_hole_symmetry": _close(
                [float(item["overlap"]) for item in fsa_targets],
                [float(item["overlap"]) for item in reversed(fsa_targets)],
                1.0e-12,
            ),
        },
        "T006": {
            "paper_length": target_results["T006"]["length"] == 26,
            "all_four_sma_families": len(t006_values) == 4,
            "printed_overlap_annotations": _close(
                t006_values, [0.63, 0.66, 0.26, 0.32], 0.015
            ),
        },
        "T007": {
            "paper_length": target_results["T007"]["length"] == 26,
            "all_13_series": len(t007_values) == 13,
            "printed_overlap_annotations": _close(
                t007_values,
                [
                    0.66,
                    0.82,
                    0.93,
                    0.94,
                    0.92,
                    0.90,
                    0.86,
                    0.82,
                    0.79,
                    0.75,
                    0.71,
                    0.66,
                    0.62,
                ],
                0.015,
            ),
        },
        "T008": {
            "all_printed_lengths": target_results["T008"]["lengths"]
            == [16, 18, 20, 22, 24, 26],
            "all_values_finite": target_results["T008"]["all_values_finite"] is True,
        },
        "T009": {
            "paper_length": target_results["T009"]["length"] == 26,
            "full_13_state_variational_space": target_results["T009"][
                "variational_dimension"
            ]
            == 13,
            "printed_overlap_annotations": _close(
                t009_values,
                [
                    0.62,
                    0.81,
                    0.86,
                    0.92,
                    0.93,
                    0.94,
                    0.96,
                    0.96,
                    0.96,
                    0.94,
                    0.90,
                    0.78,
                    0.63,
                ],
                0.015,
            ),
        },
    }
    targets = [
        {
            "target_id": target_id,
            "status": "passed" if all(target_checks.values()) else "failed",
            "checks": target_checks,
        }
        for target_id, target_checks in checks.items()
    ]
    all_passed = all(item["status"] == "passed" for item in targets)
    result = {
        "schema_version": 1,
        "check": "exact_scars_target_acceptance",
        "paper_id": "1810.00888",
        "status": "passed" if all_passed else "failed",
        "summary": {
            "targets_total": 9,
            "targets_passed": sum(item["status"] == "passed" for item in targets),
            "paper_error_candidates": 0,
            "fresh_review_present": False,
        },
        "targets": targets,
        "reproduction_defects": [
            {
                "finding_id": "RD001",
                "status": "fixed",
                "problem": "The initial renderer scored Xi_12 and Xi_13 by their global spectral maxima instead of their corresponding consecutive scar states.",
                "fix": "Use a strictly descending scar-tower selector; frozen numerical arrays were not changed.",
            }
        ],
        "protocol_v2": {
            "finding_id": "REV001",
            "topic": "Main-text edge-energy decay length 2 ln(3)",
            "classification": "inconclusive",
            "paper_error_candidate_emitted": False,
            "gates": {
                "paper_exact_parameters": True,
                "analytic_or_converged_result": True,
                "two_independent_crosschecks": True,
                "source_pinpoint": True,
                "reproduction_defect_excluded": True,
                "compute_ambiguity_excluded": True,
                "fresh_context_review": False,
            },
            "evidence": profile["decay_length_review"],
        },
    }
    output = WORKSPACE / "outputs/checks/target_acceptance.json"
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(output)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
