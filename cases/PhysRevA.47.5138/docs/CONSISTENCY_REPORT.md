# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_or_formula_match | 7 | Formula, paper parameters, target features and scientific checks pass. |
| partial_match | 0 | No target has a partial scientific result. |
| unresolved_mismatch | 0 | No stable paper-versus-reproduction discrepancy remains. |
| not_in_scope | 2 | Figures 1 and 5 are schematics. |

## Per-Target Consistency

| Target | Paper item | Evidence | Difference | Interpretation |
| --- | --- | --- | --- | --- |
| T001 | Fig. 2(a) | Qmax=1; normalized CSS | none above tolerance | exact initial state |
| T002 | Fig. 2(b) | Qmax=0.446284 vs 0.445 | +0.001284 | rounding/grid agreement |
| T003 | Fig. 2(c) | Qmax=0.240581 vs 0.241 | -0.000419 | rounding/grid agreement |
| T004 | Fig. 3(a) | Qmax=1; normalized CSS | none above tolerance | exact initial state |
| T005 | Fig. 3(b) | Qmax=0.254471 vs 0.252 | +0.002471 | rounding/grid agreement |
| T006 | Fig. 3(c) | Qmax=0.185589 vs 0.187 | -0.001411 | rounding/grid agreement |
| T007 | Fig. 4 | OAT/TACT minima and asymptotes pass | finite-S distance only | scientific scaling reproduced |

The maximum direct OAT formula-versus-state covariance difference is
4.89e-14. Doubling the TACT search grid changes the S=20 minimum by zero at
stored precision. Independent `scipy.linalg.expm` evolution agrees with the
spectral implementation in the tests.

## Paper Review

The printed Qmax values, one-axis optimum and both asymptotic claims are
numerically supported. No paper-error candidate is emitted. A new reviewer must
still attempt to falsify this conclusion from the frozen review bundles.
