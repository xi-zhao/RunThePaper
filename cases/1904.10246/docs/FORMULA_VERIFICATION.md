# Formula Verification

Numerical execution was opened only after the machine-readable formula gate
passed. The authoritative result is
`outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Numerical use |
| --- | --- | --- | --- |
| `EQ001` | Amplified Bernoulli probability | verified | Figure 2 and Figure A sampling |
| `EQ002` | Joint likelihood and global MLE | verified | Figure 2 and Figure A estimates |
| `EQ003` | Fisher information and Cramér–Rao error | verified | Figure 2 bounds and Table 1 |
| `EQ004` | Total oracle-query count | verified | Figure 2, Figure A, and Table 1 |
| `EQ005` | Exact LIS/EIS schedule sums | verified | Figure 2 and Table 1 |
| `EQ006` | Table 1 complexity exponents | verified | Table 1 exact comparison |
| `EQ007` | Conventional-AE error envelope | verified | Appendix Figure A |
| `EQ008` | Circuit-resource formulas | verified | Table 2 |

## Independent Checks

- Direct LIS and EIS schedule sums equal their closed forms for all tested
  indices.
- The `m=0` likelihood estimator equals the analytic binomial estimator.
- Table 1 exponents are derived from query and Fisher-information growth.
- Table 2 primitive block sums equal the independent closed forms.

There are no closed or quarantined formulas used by executable targets.
`DERIVATION.md` is generated from `EQUATION_CARDS.json`; implementation
bindings are recorded in `DERIVATION_TRACE.md`.
