# Simulating the Sycamore quantum supremacy circuits: scientific reproduction note

## Result

All 17 targets have a v6 clean-room author baseline from exact public circuit definitions, analytic rederivations, and a resource-guarded isolated run. T005/T009 now have complete publication-input audits, and T012/T013 have executable formula checks. No independent-review verdict is authored.

The public status is **Scientific reproduction — paper-error candidates identified**. The package preserves the current evidence boundary and never presents partial, review-pending, or paper-assessment-pending work as complete.

## What is reproduced

The case starts from a full-paper reading and equation-level derivation, then performs independent numerical work. Paper pixels, author numerical arrays, and author source code are not scientific inputs to the numerical runner. Source figures are used only after generated data are frozen, for layout and declared scientific-region comparison. The public package contains derivations, independent code, generated data and figures, machine-readable checks, and limited comparison boards.

Current authoritative dimensions: `artifact_integrity=artifact_valid_with_warnings, numerical_scope=complete, parameters=mixed, parameter_provenance=passed, causal_resolution=repair_required, science=pending, execution=attested, pixel=missing, independent_review=passed, review_scope=complete, paper_assessment=mixed`.

## Run

From `code`, run `python scripts/run_reproduction.py` with the arguments shown in the main README. Compute-heavy paper-scale runners and configurations remain available under `code/scripts` and `code/config`; code readiness is not reported as an executed production run.

## Paper-review boundary

Stable conflicts among equations, captions, conclusions, and independent numerics are recorded. They become paper-error candidates only after the falsification and independent-review requirements are met. Current limitation: Canonical source switched to arXiv because it includes TeX source and original figure assets. Local reproduction validates formulas and numerical features, not the full 53-qubit GPU-scale contraction.
