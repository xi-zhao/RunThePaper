# Unidirectional Dark-to-Bright Rescue in Cavity-Coupled Quantum Transport: scientific reproduction note

## Result

Eleven independent numerical targets reproduce the paper's central features; only the four T011 QCLE benchmark series remain uncovered because indispensable operating parameters are not published.

The public status is **Partial scientific reproduction**. The package preserves the current evidence boundary and never presents partial, review-pending, or paper-assessment-pending work as complete.

## What is reproduced

The case starts from a full-paper reading and equation-level derivation, then performs independent numerical work. Paper pixels, author numerical arrays, and author source code are not scientific inputs to the numerical runner. Source figures are used only after generated data are frozen, for layout and declared scientific-region comparison. The public package contains derivations, independent code, generated data and figures, machine-readable checks, and limited comparison boards.

Current authoritative dimensions: `artifact_integrity=artifact_valid, numerical_scope=incomplete, parameters=mixed, parameter_provenance=passed, causal_resolution=repair_required, science=pending, execution=attested, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing`.

## Run

From `code`, run `python scripts/run_reproduction.py` with the arguments shown in the main README. Compute-heavy paper-scale runners and configurations remain available under `code/scripts` and `code/config`; code readiness is not reported as an executed production run.

## Paper-review boundary

Stable conflicts among equations, captions, conclusions, and independent numerics are recorded. They become paper-error candidates only after the falsification and independent-review requirements are met. Current limitation: Mean hopping t=1 meV and source state |1> are reconstructed from cross-figure constraints and validated numerically. Exact author random seeds and optimization grids are unavailable, so generated artifacts are exploratory paper-subset evidence. Ten scored numerical targets pass with an overall similarity score of 83.4; the QCLE benchmark remains blocked by missing source inputs.
