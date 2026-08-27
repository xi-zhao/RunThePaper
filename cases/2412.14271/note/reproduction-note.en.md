# Dissipative Phase Transition in the Two-Photon Dicke Model: scientific reproduction note

## Result

Atomic numerical coverage is 29/31 (93.55%); the old 7/8 figure described implementation groups, not paper items.

The public status is **Partial scientific reproduction**. The package preserves the current evidence boundary and never presents partial, review-pending, or paper-assessment-pending work as complete.

## What is reproduced

The case starts from a full-paper reading and equation-level derivation, then performs independent numerical work. Paper pixels, author numerical arrays, and author source code are not scientific inputs to the numerical runner. Source figures are used only after generated data are frozen, for layout and declared scientific-region comparison. The public package contains derivations, independent code, generated data and figures, machine-readable checks, and limited comparison boards.

Current authoritative dimensions: `artifact_integrity=artifact_valid, numerical_scope=incomplete, parameters=mixed, parameter_provenance=passed, causal_resolution=repair_required, science=pending, execution=attested, pixel=missing, independent_review=passed, review_scope=complete, paper_assessment=inconclusive`.

## Run

From `code`, run `python scripts/run_reproduction.py` with the arguments shown in the main README. Compute-heavy paper-scale runners and configurations remain available under `code/scripts` and `code/config`; code readiness is not reported as an executed production run.

## Paper-review boundary

Stable conflicts among equations, captions, conclusions, and independent numerics are recorded. They become paper-error candidates only after the falsification and independent-review requirements are met. Current limitation: Main quantum figures are feature-level because trajectory counts are reduced. Formal Supplement Fig. S3 is an explicit uncovered item because its panel inventory, observable, and parameters are unavailable. Formal Supplement Fig. S4 is an explicit uncovered item because its panel inventory, observable, and parameters are unavailable. Fig. 3(g)/Fig. S2 has a confirmed branch-to-spectrum evidence discrepancy: the plotted lower branch is nonlinearly unstable but has no positive Bogoliubov eigenvalue.
