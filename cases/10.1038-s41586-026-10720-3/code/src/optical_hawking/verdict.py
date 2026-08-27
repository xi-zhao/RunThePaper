"""Fail-closed scientific verdict for the optical-Hawking reproduction.

Historical versions let a PDF-derived dispersion, source-marker fit, and
pixel SSIM satisfy the paper-level gate.  Those are useful comparison
diagnostics but cannot establish scientific reproduction.  This adapter now
accepts only the formula/coverage contracts and the isolated formula-only
campaign; missing source parameters and review remain visible blockers.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def evaluate_reproduction_evidence(
    evidence: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Return the case-local verdict without allowing comparison leakage."""

    formula = evidence["formula_verification"]
    project = evidence["physics_project"]
    ledger = evidence["claim_target_ledger"]
    coverage = evidence["figure_coverage"]
    campaign = evidence["paper_scale_acceptance"]
    similarity = evidence["similarity_scorecard"]
    review = evidence.get("independent_review", {})

    project_counts = _mapping(_mapping(project.get("summary")).get("finding_counts"))
    ledger_summary = _mapping(ledger.get("summary"))
    coverage_summary = _mapping(coverage.get("summary"))
    similarity_summary = _mapping(similarity.get("evaluation_summary"))

    missing_inputs = list(campaign.get("blocking_missing_inputs") or [])
    gates = {
        "formula_gate": formula.get("status") == "passed",
        "project_schema_gate": (
            project.get("status") in {"passed", "passed_with_warnings"}
            and int(project_counts.get("error", 1)) == 0
        ),
        "claim_coverage_gate": (
            ledger.get("status") == "passed"
            and int(ledger_summary.get("numeric_claims_without_targets", 1)) == 0
            and int(ledger_summary.get("targets_without_claim_refs", 1)) == 0
        ),
        "complete_numeric_inventory_gate": (
            coverage.get("status") == "passed"
            and int(coverage_summary.get("paper_scale_code_missing_total", 1)) == 0
            and int(coverage_summary.get("compute_deferred_code_missing", 1)) == 0
        ),
        "clean_scientific_input_gate": (
            bool(campaign.get("static_clean_input_boundary_passed"))
            and not list(campaign.get("forbidden_scientific_inputs") or [])
        ),
        "isolated_execution_gate": bool(campaign.get("runtime_file_access_attested")),
        "paper_scale_execution_gate": (
            bool(campaign.get("complete"))
            and bool(campaign.get("paper_parameters_executed"))
        ),
        "paper_parameter_gate": bool(campaign.get("paper_exact")) and not missing_inputs,
        "physics_assertion_gate": (
            similarity.get("status") == "passed"
            and not list(similarity_summary.get("essential_physics_failures") or [])
        ),
        "independent_review_gate": review.get("status") == "passed",
    }
    failed_gates = [name for name, passed in gates.items() if not passed]
    complete = not failed_gates
    return {
        "schema_version": 2,
        "status": "passed" if complete else "in_progress",
        "decision": {
            "status": (
                "scientific_reproduction_complete"
                if complete
                else "scientific_reproduction_incomplete"
            ),
            "next_action": (
                "publication_ready"
                if complete
                else "run_full_campaign_or_resolve_missing_inputs_then_fresh_review"
            ),
            "exact_reproduction": complete,
            "reason": (
                "All scientific, execution, provenance, and review gates passed."
                if complete
                else f"Open gates: {', '.join(failed_gates)}"
            ),
        },
        "summary": {
            "gates_passed": len(gates) - len(failed_gates),
            "gates_total": len(gates),
            "failed_gates": failed_gates,
            "similarity_score": float(similarity.get("overall_score", 0.0)),
            "similarity_level": str(similarity.get("similarity_level") or ""),
            "missing_indispensable_inputs": missing_inputs,
            "paper_scale_completed_units": int(campaign.get("completed_units", 0)),
            "paper_scale_expected_units": int(campaign.get("expected_units", 0)),
        },
        "gates": gates,
        "evidence_boundary": {
            "scientific_inputs": "paper equations, published scalar parameters, and explicit reconstructed assumptions only",
            "comparison_only": [
                "Fig. 2 vector dispersion trace",
                "Fig. 3/4/5 vector markers and curves",
                "pixel and SSIM diagnostics",
            ],
            "forbidden_for_scientific_generation": [
                "author code",
                "author numerical arrays",
                "digitized source curves",
                "source pixels",
            ],
            "unavailable_inputs": missing_inputs,
            "paper_error_candidates": 0,
        },
    }
