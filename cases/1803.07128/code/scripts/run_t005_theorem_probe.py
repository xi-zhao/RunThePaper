#!/usr/bin/env python3
"""Falsification-oriented probe for Appendices B-D of arXiv:1803.07128."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qml_feature_space.separability import (  # noqa: E402
    all_binary_affine_interpolation,
    analytic_multimode_gram,
    multimode_fock_states,
    numerical_rank,
    realify,
    strict_affine_separation_feasible,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    return parser.parse_args()


def check(name: str, passed: bool, evidence: dict[str, object]) -> dict[str, object]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text())
    parameters = config["parameters"]
    tolerances = config["tolerances"]
    c = float(parameters["squeezing_c"])
    rank_tolerance = float(tolerances["rank_relative"])
    single_phases = np.asarray(parameters["single_mode_phases"], dtype=float)[:, None]
    multimode_phases = np.asarray(parameters["multimode_phases"], dtype=float)

    single_rows = []
    for cutoff in parameters["single_mode_cutoffs"]:
        states = multimode_fock_states(single_phases, c, int(cutoff))
        singular_values = np.linalg.svd(states, compute_uv=False)
        single_rows.append(
            {
                "even_terms": int(cutoff),
                "rank": numerical_rank(states, rank_tolerance),
                "expected_vandermonde_rank": min(len(single_phases), int(cutoff)),
                "minimum_singular_value": float(singular_values[-1]),
            }
        )

    analytic_gram = analytic_multimode_gram(multimode_phases, c)
    analytic_eigenvalues = np.linalg.eigvalsh(analytic_gram)
    multimode_rows = []
    for cutoff in parameters["multimode_cutoffs"]:
        states = multimode_fock_states(multimode_phases, c, int(cutoff))
        explicit_gram = states.conj() @ states.T
        singular_values = np.linalg.svd(states, compute_uv=False)
        multimode_rows.append(
            {
                "even_terms_per_mode": int(cutoff),
                "complex_rank": numerical_rank(states, rank_tolerance),
                "realified_rank": numerical_rank(realify(states), rank_tolerance),
                "minimum_singular_value": float(singular_values[-1]),
                "analytic_gram_max_absolute_error": float(
                    np.max(np.abs(explicit_gram - analytic_gram))
                ),
            }
        )

    label_states = multimode_fock_states(
        multimode_phases,
        c,
        int(parameters["label_test_cutoff"]),
        normalize=True,
    )
    label_result = all_binary_affine_interpolation(realify(label_states))

    periodic_phase = float(parameters["periodic_phase"])
    periodic_states = multimode_fock_states(
        np.asarray([[periodic_phase], [periodic_phase + 2.0 * np.pi]]),
        c,
        40,
        normalize=True,
    )
    periodic_result = {
        "raw_inputs": [periodic_phase, periodic_phase + 2.0 * np.pi],
        "state_distance": float(np.linalg.norm(periodic_states[0] - periodic_states[1])),
        "state_rank": numerical_rank(periodic_states, rank_tolerance),
        "interpretation": "Raw real inputs differing by 2*pi encode the same physical phase and state.",
    }

    affine_points = np.asarray(parameters["affine_counterexample_points"], dtype=float)
    affine_labels = np.asarray(parameters["affine_counterexample_labels"], dtype=float)
    affine_design = np.column_stack((affine_points, np.ones(len(affine_points))))
    affine_result = {
        "points": affine_points.tolist(),
        "labels": affine_labels.tolist(),
        "rank_of_first_M_minus_1_vectors": numerical_rank(
            affine_points[:-1], rank_tolerance
        ),
        "affine_design_rank": numerical_rank(affine_design, rank_tolerance),
        "augmented_with_labels_rank": numerical_rank(
            np.column_stack((affine_design, affine_labels)), rank_tolerance
        ),
        "strict_affine_separator_exists": strict_affine_separation_feasible(
            affine_points, affine_labels
        ),
        "interpretation": "This falsifies Proposition 1 as written: M-1 linearly independent vectors do not guarantee shattering of all M points.",
    }

    checks = [
        check(
            "single-mode ranks follow the Vandermonde prediction",
            all(row["rank"] == row["expected_vandermonde_rank"] for row in single_rows),
            {"rows": single_rows},
        ),
        check(
            "distinct multimode phase vectors have full feature rank",
            all(
                row["complex_rank"] == len(multimode_phases)
                and row["realified_rank"] == len(multimode_phases)
                for row in multimode_rows
            ),
            {"rows": multimode_rows},
        ),
        check(
            "explicit Fock Gram converges to the independent analytic overlap",
            multimode_rows[-1]["analytic_gram_max_absolute_error"]
            <= float(tolerances["gram_convergence_absolute"]),
            {
                "final_error": multimode_rows[-1]["analytic_gram_max_absolute_error"],
                "threshold": tolerances["gram_convergence_absolute"],
            },
        ),
        check(
            "analytic multimode Gram is strictly positive on the test set",
            float(analytic_eigenvalues[0])
            >= float(tolerances["analytic_gram_minimum_eigenvalue"]),
            {"minimum_eigenvalue": float(analytic_eigenvalues[0])},
        ),
        check(
            "every binary labelling is affinely interpolated for full-rank mapped states",
            label_result["worst_absolute_residual"]
            <= float(tolerances["label_interpolation_absolute"]),
            label_result,
        ),
        check(
            "periodic raw-input counterexample is reproduced",
            periodic_result["state_distance"]
            <= float(tolerances["periodic_state_distance_absolute"])
            and periodic_result["state_rank"] == 1,
            periodic_result,
        ),
        check(
            "Proposition 1 affine counterexample is reproduced",
            affine_result["rank_of_first_M_minus_1_vectors"] == 2
            and affine_result["augmented_with_labels_rank"]
            > affine_result["affine_design_rank"]
            and not affine_result["strict_affine_separator_exists"],
            affine_result,
        ),
    ]

    property_payload = {
        "schema_version": 1,
        "target_id": "T005",
        "claim_verdict": "qualified_pass_with_proof_defect_candidates",
        "scientific_conclusion": "The finite-set separability conclusion survives when encoded physical phase vectors are distinct modulo 2*pi: the mapped states are full rank and all tested binary labelings interpolate. Proposition 1 is false as written, the raw-input claim needs a periodic-domain qualification, and the paper's nonzero-overlap argument is not a proof of multimode independence.",
        "checks": checks,
        "passed": all(item["passed"] for item in checks),
        "fresh_review_required": True,
    }
    crosscheck_payload = {
        "schema_version": 1,
        "target_id": "T005",
        "method_a": "explicit tensor-product Fock expansion",
        "method_b": "closed-form complex overlap Gram matrix",
        "single_mode_rows": single_rows,
        "multimode_rows": multimode_rows,
        "analytic_gram_eigenvalues": analytic_eigenvalues.tolist(),
        "binary_label_test": label_result,
    }
    counterexample_payload = {
        "schema_version": 1,
        "target_id": "T005",
        "status": "paper_claim_discrepancy_candidates_not_yet_independently_reviewed",
        "periodic_input_counterexample": periodic_result,
        "proposition_one_counterexample": affine_result,
        "multimode_proof_gap": {
            "paper_step": "nonzero pairwise overlap is asserted to imply linear independence",
            "assessment": "invalid implication",
            "independent_resolution": "explicit tensor-product rank and analytic Gram positivity support the corrected finite-set conclusion",
        },
        "author_code_or_arrays_used": False,
    }

    outputs = {
        args.output_root / "checks" / "T005_separability_property_tests.json": property_payload,
        args.output_root / "checks" / "T005_independent_rank_crosscheck.json": crosscheck_payload,
        args.output_root / "data" / "T005_counterexample_search.json": counterexample_payload,
    }
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"passed": property_payload["passed"], "checks": len(checks)}))
    return 0 if property_payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
