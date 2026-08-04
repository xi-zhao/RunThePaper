"""Build machine-readable contracts for the idx51 benchmark-gold audit."""

from __future__ import annotations

import json
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def project() -> dict[str, object]:
    formula_ids = ["EQ_SIGN", "EQ_ASYM", "EQ_MOMENT", "EQ_DECOMP", "EQ_ROOT"]
    claims = [
        {
            "claim_id": "CLM_SOURCE",
            "status": "active",
            "statement": "No single PRL source contract is recoverable; the exact lineage is Wang-Teter PRB 45, 13196 (1992).",
            "source_refs": ["code/SOURCE_AUDIT.md", "raw/wang_teter_prb45_13196.pdf"],
            "formula_refs": ["EQ_SIGN", "EQ_ASYM", "EQ_DECOMP"],
            "target_refs": ["T_BENCH_AUDIT"],
            "assumptions": [],
        },
        {
            "claim_id": "CLM_SIGN",
            "status": "active",
            "statement": "Frozen Tasks 1 and 4 have mutually inconsistent response/Hessian signs.",
            "source_refs": ["benchmark:prlb-f37350e-051", "code/GOLD_AUDIT.md"],
            "formula_refs": ["EQ_SIGN"],
            "target_refs": ["T_BENCH_AUDIT"],
            "assumptions": ["The frozen definitions are evaluated without silently repairing -G to G."],
        },
        {
            "claim_id": "CLM_MOMENT",
            "status": "active",
            "statement": "A high-q q^-2 tail alone does not determine the second radial moment.",
            "source_refs": ["benchmark:prlb-f37350e-051", "code/DERIVATION.md"],
            "formula_refs": ["EQ_MOMENT"],
            "target_refs": ["T_BENCH_AUDIT"],
            "assumptions": ["Standard three-dimensional Fourier convention."],
        },
        {
            "claim_id": "CLM_VALID_PARTS",
            "status": "active",
            "statement": "The -3/35 asymptote, conditional contact decomposition, and printed root are independently valid.",
            "source_refs": ["outputs/data/idx51_gold_audit.json"],
            "formula_refs": ["EQ_ASYM", "EQ_DECOMP", "EQ_ROOT"],
            "target_refs": ["T_BENCH_AUDIT"],
            "assumptions": [],
        },
    ]
    return {
        "schema_version": 1,
        "project_id": "prlb-f37350e-051-lindhard-kernel-gold-audit",
        "paper": {
            "paper_id": "prlb-f37350e-051",
            "title": "Unresolved PRL contract; Wang-Teter kernel lineage",
            "authors": ["L.-W. Wang", "M. P. Teter"],
            "publication": "No matching PRL recovered",
            "doi": None,
            "benchmark_record": "prlb-f37350e-051",
            "lineage_doi": "10.1103/PhysRevB.45.13196",
        },
        "paper_map": {
            "figures": [
                {
                    "figure_id": "LINEAGE_FIGURES",
                    "label": "1992 PRB atom and solid figures",
                    "classification": "out_of_scope",
                    "classification_reason": "Lineage source, not a verified PRL contract.",
                },
                {
                    "figure_id": "BENCH_AUDIT",
                    "label": "Response-sign, root, and Fourier-inference diagnostic",
                    "classification": "out_of_scope",
                    "classification_reason": "Benchmark audit artifact rather than a source-paper panel.",
                },
            ],
            "source_refs": ["raw/wang_teter_prb45_13196.pdf", "code/PAPER_MAP.md"],
        },
        "claim_graph": {"claims": claims, "edges": []},
        "formula_traces": [
            {
                "formula_id": formula_id,
                "source_refs": [{"kind": "workspace_card", "value": f"EQUATION_CARDS.json#{formula_id}"}],
                "latex": "See equation card",
                "role": "Independent benchmark-gold audit",
                "numeric_gate": "verified",
                "code_refs": ["code/src/lindhard_kernel.py"],
            }
            for formula_id in formula_ids
        ],
        "method_traces": [
            {
                "method_id": "MTH_AUDIT",
                "source_refs": ["code/METHOD_TRACE.md"],
                "role": "Source diff, exact algebra, counterexample, and arbitrary-precision bisection",
                "method_gate": "verified",
                "code_refs": [
                    "code/src/lindhard_kernel.py",
                    "code/scripts/run_gold_audit.py",
                ],
            }
        ],
        "figure_targets": [
            {
                "target_id": "T_BENCH_AUDIT",
                "figure_id": "BENCH_AUDIT",
                "panel_ids": ["all"],
                "target_kind": "other_numeric",
                "physical_meaning": "Audit all five frozen analytic tasks and their source provenance.",
                "claim_refs": [claim["claim_id"] for claim in claims],
                "formula_refs": formula_ids,
                "method_refs": ["MTH_AUDIT"],
                "formula_gate": "verified",
                "parameter_set": {
                    "paper": {},
                    "generated": {"precision_digits": 180, "root_scan_points": 10000},
                    "parameter_match": "not_applicable",
                    "paper_parameter_source": "Frozen benchmark extension; no matching PRL parameter set exists.",
                },
                "observable": "response sign, asymptotic coefficient, moment logic, contact coefficients, and first root",
                "status": "reproduced",
            }
        ],
        "execution_runs": [
            {
                "run_id": "RUN_AUDIT",
                "target_id": "T_BENCH_AUDIT",
                "runner_kind": "analytic_high_precision_audit",
                "command": "python code/scripts/run_gold_audit.py",
                "inputs": ["benchmark:prlb-f37350e-051", "raw/wang_teter_prb45_13196.pdf"],
                "outputs": ["outputs/data/idx51_gold_audit.json"],
                "status": "passed",
                "generated_data_provenance": "independent_numerics",
            }
        ],
        "generated_datasets": [
            {
                "dataset_id": "DATA_AUDIT",
                "target_id": "T_BENCH_AUDIT",
                "path": "outputs/data/idx51_gold_audit.json",
                "schema": {"keys": ["source_contract", "task_1_and_4_sign_audit", "task_2", "task_3_conditional_algebra", "task_5", "verdict"]},
                "provenance": "independent_numerics",
                "created_by_run": "RUN_AUDIT",
                "status": "available",
            }
        ],
        "rendered_figures": [
            {
                "figure_artifact_id": "ART_AUDIT",
                "target_id": "T_BENCH_AUDIT",
                "path": "outputs/figures/idx51_gold_audit.png",
                "data_refs": ["DATA_AUDIT"],
                "status": "available_benchmark_audit",
                "artifact_stage": "exploratory",
            }
        ],
        "evidence_comparisons": [
            {
                "comparison_id": "CMP_AUDIT",
                "target_id": "T_BENCH_AUDIT",
                "generated_artifact": "ART_AUDIT",
                "reference_comparison": "benchmark_data",
                "generated_data_provenance": "independent_numerics",
                "verdict": "benchmark_gold_invalid",
                "score_cap": 100,
                "evidence": ["code/GOLD_AUDIT.md", "outputs/data/idx51_gold_audit.json"],
            }
        ],
        "failure_verdicts": [
            {
                "failure_id": "FAIL_GOLD",
                "target_id": "T_BENCH_AUDIT",
                "failure_type": "formula_or_method_error",
                "failure_class": "benchmark_gold_invalid",
                "verdict": "benchmark_gold_invalid",
                "physics_diagnosis": "Frozen response sign and positive Hessian are mutually inconsistent; the high-q moment inference is also false.",
                "visual_diagnosis": "Audit diagnostic exposes the sign split and preserves the independently valid root.",
                "provenance_diagnosis": "The closest primary source is a 1992 PRB, not a matching PRL, and uses the opposite G convention.",
                "next_action": "Repair the benchmark source and sign contract before numerical judging.",
                "evidence": ["code/GOLD_AUDIT.md"],
            }
        ],
        "repair_attempts": [],
        "pixel_layout_targets": [],
        "reports": [
            "code/REPRODUCTION_REPORT.md",
            "code/SIMILARITY_SCORECARD.md",
            "code/CONSISTENCY_REPORT.md",
        ],
        "event_log": [],
    }


def scorecard() -> dict[str, object]:
    return {
        "schema_version": 3,
        "status": "failed",
        "score_model": "rra_similarity_v3_figure_evaluation",
        "paper_id": "prlb-f37350e-051",
        "summary": "Benchmark gold invalidated; no matching PRL or source-paper panel reproduced.",
        "targets": [
            {
                "target_id": "T_BENCH_AUDIT",
                "label": "Five-task Lindhard-kernel benchmark audit",
                "figure_refs": ["BENCH_AUDIT"],
                "weight": 1.0,
                "components": {
                    "feature_match": {"score": 20.0, "max_score": 50.0, "reason": "The analytic objects are audited, but the source/sign contract fails."},
                    "numeric_closeness": {"score": 14.0, "max_score": 35.0, "reason": "The asymptote, conditional coefficients, and root match; three requested claims are invalid."},
                    "paper_scope_coverage": {"score": 0.0, "max_score": 15.0, "reason": "No matching PRL or source-paper panel is reproduced."},
                },
                "panel_coverage": {"panels": [{"panel_id": "all", "status": "not_reproduced"}]},
                "evaluation": {
                    "critical": True,
                    "paper_level_role": "method_validation",
                    "artifact_pass": True,
                    "data_backed": True,
                    "manual_interventions": 0,
                    "failure_type": "formula_or_method_error",
                    "parameter_match": "not_applicable",
                    "artifact_stage": "exploratory",
                    "reference_comparison": "benchmark_data",
                    "generated_data_provenance": "independent_numerics",
                    "formula_dependencies": ["EQ_SIGN", "EQ_ASYM", "EQ_MOMENT", "EQ_DECOMP", "EQ_ROOT"],
                    "formula_gate": "verified",
                },
                "evidence": ["outputs/data/idx51_gold_audit.json", "outputs/figures/idx51_gold_audit.png"],
                "remaining_gap": "A valid PRL source contract and internally consistent frozen response convention do not exist.",
            }
        ],
    }


def main() -> None:
    write_json(WORKSPACE / "physics_reproduction_project.json", project())
    write_json(WORKSPACE / "outputs" / "checks" / "similarity_scorecard.json", scorecard())


if __name__ == "__main__":
    main()
