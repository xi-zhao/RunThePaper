# Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices: scientific reproduction note

## Result

SABRE 的核心算法机制已经复现，小例子可以精确对齐；但 Table II 是论文里最重要的数值表，目前只达到部分一致。

The public status is **Partial scientific reproduction**. The package preserves the current evidence boundary and never presents partial, review-pending, or paper-assessment-pending work as complete.

## What is reproduced

The case starts from a full-paper reading and equation-level derivation, then performs independent numerical work. Paper pixels, author numerical arrays, and author source code are not scientific inputs to the numerical runner. Source figures are used only after generated data are frozen, for layout and declared scientific-region comparison. The public package contains derivations, independent code, generated data and figures, machine-readable checks, and limited comparison boards.

Current authoritative dimensions: `artifact_integrity=artifact_valid, numerical_scope=complete, parameters=mixed, parameter_provenance=failed, causal_resolution=terminal_blocker, science=passed, execution=missing, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing`.

## Run

From `code`, run `python scripts/run_reproduction.py` with the arguments shown in the main README. Compute-heavy paper-scale runners and configurations remain available under `code/scripts` and `code/config`; code readiness is not reported as an executed production run.

## Paper-review boundary

Stable conflicts among equations, captions, conclusions, and independent numerics are recorded. They become paper-error candidates only after the falsification and independent-review requirements are met. Current limitation: Remaining lifecycle boundaries: parameters=mixed, parameter_provenance=failed, causal_resolution=terminal_blocker, execution=missing, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing.
