# Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain: scientific reproduction note

## Result

The two Main Fig. 5 panels and two central periodic analytic families are independently covered, while a full-paper audit exposes five supplemental claim families without accepted implementations. The legacy two-panel similarity score remains 95; whole-paper coverage and reproduction degree are derived separately.

The public status is **Partial scientific reproduction**. The package preserves the current evidence boundary and never presents partial, review-pending, or paper-assessment-pending work as complete.

## What is reproduced

The case starts from a full-paper reading and equation-level derivation, then performs independent numerical work. Paper pixels, author numerical arrays, and author source code are not scientific inputs to the numerical runner. Source figures are used only after generated data are frozen, for layout and declared scientific-region comparison. The public package contains derivations, independent code, generated data and figures, machine-readable checks, and limited comparison boards.

Current authoritative dimensions: `artifact_integrity=artifact_valid_with_warnings, numerical_scope=complete, parameters=mixed, parameter_provenance=passed, causal_resolution=repair_required, science=failed, execution=attested, pixel=missing, independent_review=passed, review_scope=complete, paper_assessment=inconclusive`.

## Run

From `code`, run `python scripts/run_reproduction.py` with the arguments shown in the main README. Compute-heavy paper-scale runners and configurations remain available under `code/scripts` and `code/config`; code readiness is not reported as an executed production run.

## Paper-review boundary

Stable conflicts among equations, captions, conclusions, and independent numerics are recorded. They become paper-error candidates only after the falsification and independent-review requirements are met. Current limitation: All 25 first-excited values agree with the digitized source within 0.0015. The ground-state panel has one retained 0.00364 discrepancy at theta=10 degrees, N=12; the remaining 24 values agree within 0.0015. The paper omits eigensolver and tolerance details, so the two rendered overlap artifacts remain exploratory despite their strong numerical agreement. The full-paper item audit finds 9 eligible scientific items: 4 covered and 5 uncovered, for 44.44% coverage and reproduction degree 40.90. V003-V007 expose three open-chain results, one parity-selection rule, and one perturbative-sector claim that still lack independent implementations.
