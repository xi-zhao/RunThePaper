# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 2 | Printed analytic/parity invariants match. |
| feature_match | 3 | Main numerical structure matches at reduced trajectory scale. |
| partial_match | 2 | Method/count differences materially limit closeness. |
| blocked | 1 | Formal supplementary input is unavailable. |
| not_in_scope | 1 | Fig. 1 is schematic only. |

## Per-target consistency

| Target | Level | Evidence | Main difference |
| --- | --- | --- | --- |
| T001 | partial_match | lambda_c=0.509901951 exactly; cutoff mean range 18.26 and nonzero tails | finite-time QT replaces steady-state ED |
| T002 | feature_match | normalized means track the upper cumulant branch; tails <2.1e-9 | only 6-16 trajectories |
| T003 | feature_match | six Wigner fields, integral error <7.1e-4, four lobes visible | Z4 residual remains 0.13-0.62 |
| T004 | exact_match | all post-threshold superradiant points have positive real modes | presentation differs |
| T005 | partial_match | fixed-point residual <=6.1e-14; physical-real Jacobian and cubic zero-mode audit | stable source branch-to-spectrum/Bogoliubov-evidence discrepancy pending fresh review; see `PAPER_DISCREPANCY.md` |
| T006 | blocked | coverage record | formal supplement inaccessible |
| T007 | feature_match | same trend from cumulative trajectory subsets | 4 vs final count, not 500 vs 3000 |
| T008 | exact_match | two zero modes; parity leakage exactly 0 | trajectory count is reduced, invariants exact |

The case must remain lifecycle `partial`: a high white-background pixel score,
successful process exit, or valid artifact cannot override a blocked target,
reduced sampling, independently unreviewed scientific discrepancy, or missing
independent review.
