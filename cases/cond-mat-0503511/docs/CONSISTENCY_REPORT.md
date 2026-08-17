# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | The paper publishes curves rather than reusable numeric arrays. |
| feature_match | 5 | Every target passes its scientific feature checks. |
| partial_match | 0 | No scientific target is only partially matched. |
| input_match_only | 0 | Inputs match, outputs still differ. |
| blocked | 0 | Missing information prevents exact validation. |
| not_in_scope | 0 | Schematic, experimental, or external context. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 1 + inset | feature_match | `science_checks.json`, `fig1_kink_density.csv` | Prefactor 0.17889 versus paper fit near 0.16; exponent 0.58069 versus 0.58. | Finite-size/grid and printed-fit precision. |
| T002 | Fig. 2(a) | feature_match | `science_checks.json`, `fig2a_spectrum.csv` | Physics checks pass; render score 78.76. V4's unintended three-particle branches were removed. | The internal defect is fixed; exact pixel attribution is capped because “lowest excitations” does not specify the plotted level subset or cutoff. |
| T003 | Fig. 2(b) | feature_match | `science_checks.json`, `fig2b_fidelity_scaling.csv` | Fitted exponent 1.83876 versus paper's finite-size fit near 1.93. | Fit-window and finite-size sensitivity; axis-unit defect in an earlier run was fixed. |
| T004 | Fig. 2(c) | feature_match | `science_checks.json`, `fig2c_fidelity_bounds.csv` | No bound violation observed. | No unresolved scientific mismatch. |
| T005 | Fig. 3 + inset | feature_match | `science_checks.json`, `fig3_kink_count.csv` | Render score 86.59, below high-fidelity band. | Presentation/registration difference, not identified physics error. |

No paper error is claimed. A fresh-context reviewer still has to try to falsify
the formulas, parameter map, and generated observables.
