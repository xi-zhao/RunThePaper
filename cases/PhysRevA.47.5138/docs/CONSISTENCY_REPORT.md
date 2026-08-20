# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_or_formula_match | 5 | T001-T004 and T007 pass their formula, parameter and scientific checks. |
| partial_match | 0 | No target has a partial scientific result. |
| unresolved_mismatch | 2 | T005 and T006 retain caption-value discrepancies beyond printed rounding intervals. |
| not_in_scope | 2 | Figures 1 and 5 are schematics. |

## Per-Target Consistency

| Target | Paper item | Evidence | Difference | Interpretation |
| --- | --- | --- | --- | --- |
| T001 | Fig. 2(a) | Qmax=1; normalized CSS | none above tolerance | exact initial state |
| T002 | Fig. 2(b) | Qmax=0.446284 vs 0.445 | +0.001284 | rounding/grid agreement |
| T003 | Fig. 2(c) | Qmax=0.240581 vs 0.241 | -0.000419 | rounding/grid agreement |
| T004 | Fig. 3(a) | Qmax=1; normalized CSS | none above tolerance | exact initial state |
| T005 | Fig. 3(b) | Qmax=0.254471 vs 0.252 | +0.002471 | stable caption discrepancy after spectral, dense-expm and DOP853 checks |
| T006 | Fig. 3(c) | Qmax=0.185589 vs 0.187 | -0.001411 | stable caption discrepancy after a full printed-mu rounding sweep |
| T007 | Fig. 4 | OAT/TACT minima and asymptotes pass | finite-S distance only | scientific scaling reproduced |

The maximum direct OAT formula-versus-state covariance difference is
4.89e-14. Doubling the TACT search grid changes the S=20 minimum by zero at
stored precision. Independent `scipy.linalg.expm` evolution agrees with the
spectral implementation in the tests.

## Paper Review

The prior fresh-context protocol-v2 review supported T001-T004 and T007, and
identified T005 and T006 as `paper_error_candidate`. This is limited to the two
Figure 3 caption values; it does not invalidate the spin-squeezing theory. Its
scope finding triggered the present repair: all ten missing quantitative claims
now have canonical coverage and executable evidence. Because that repair changes
the review bundle, the historical verdict cannot be copied forward; a new
fresh-context review must adjudicate the v3 evidence.
