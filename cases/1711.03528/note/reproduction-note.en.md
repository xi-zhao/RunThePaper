# Quantum many-body scars: scientific reproduction note

## Result

量子多体 scar 的核心数值特征和 L=28 同一对称 sector 已复现；L=32 与 bond-400 MPS 路径已有代码，但尚未执行论文尺度收敛网格。

The public status is **Partial scientific reproduction**. The package preserves the current evidence boundary and never presents partial, review-pending, or paper-assessment-pending work as complete.

## What is reproduced

The case starts from a full-paper reading and equation-level derivation, then performs independent numerical work. Paper pixels, author numerical arrays, and author source code are not scientific inputs to the numerical runner. Source figures are used only after generated data are frozen, for layout and declared scientific-region comparison. The public package contains derivations, independent code, generated data and figures, machine-readable checks, and limited comparison boards.

Current authoritative dimensions: `artifact_integrity=artifact_valid_with_warnings, numerical_scope=complete, parameters=mixed, parameter_provenance=passed, causal_resolution=repair_required, science=passed, execution=attested, pixel=missing, independent_review=missing, review_scope=missing, paper_assessment=missing`.

## Run

From `code`, run `python scripts/run_reproduction.py` with the arguments shown in the main README. Compute-heavy paper-scale runners and configurations remain available under `code/scripts` and `code/config`; code readiness is not reported as an executed production run.

## Paper-review boundary

Stable conflicts among equations, captions, conclusions, and independent numerics are recorded. They become paper-error candidates only after the falsification and independent-review requirements are met. Current limitation: The paper-scale L=32 symmetry-resolved exact diagonalization and thermodynamic-limit iTEBD are not rerun locally.
