# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | Numeric values match reference data or paper values. |
| feature_match | 2 | Fig. 1 and Eq. (21) pass all scientific checks. |
| partial_match | 1 | Fig. 2 numerics pass, but its XXX source convention is internally inconsistent. |
| input_match_only | 0 | Inputs match, outputs still differ. |
| blocked | 0 | Missing information prevents exact validation. |
| not_in_scope | 0 | Schematic, experimental, or external context. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1 | feature_match | `fig1_ising_surface.csv`, `science_checks.json` | No reusable author array exists; critical slope is 0.1666817 and render score is 85.16. | Independent formula implementation plus reconstructed plotting grid. |
| T002 | Main Fig. 2 | partial_match | `fig2_critical_entropy.csv`, `test_model.py`, `science_checks.json` | The printed-sign XXX ground manifold admits entropies 0 and 2.24476, while the caption-implied antiferromagnetic calculation gives 1.95332 at half chain. | Probable sign inconsistency between Eq. (3) and the caption; fresh review pending. |
| T003 | Eq. (21) | feature_match | `majorization_checks.csv` | Minimum partial-sum margin is -1.11e-15, within numerical tolerance. | No unresolved scientific mismatch. |

The discrepancy is not attributed to insufficient compute. It survives an
independent full-space Hamiltonian, a fixed-sector sparse implementation,
Lanczos tolerance tightening and analytic ferromagnetic-state checks. No paper
error is declared before fresh review.
