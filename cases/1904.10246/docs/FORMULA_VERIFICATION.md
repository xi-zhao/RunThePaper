# Formula Verification

This document explains which formulas are allowed to feed numerical reproduction.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python private validation harness/scripts/check_formula_gate.py case/<paper-id> --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| `EQ_PROB` | amplified Bernoulli probability | verified | \(m=0\) limit and normalization pass |
| `EQ_LOGLIK` | joint binomial likelihood | verified | \(m=0\) analytic MLE and code trace pass |
| `EQ_FISHER` | schedule Fisher information | verified | symbolic derivative and numerical check pass |
| `EQ_QUERY` | oracle-query accounting | verified | finite schedule sums pass |
| `EQ_CRB` | Cramér–Rao error | verified | classical limiting case passes |
| `EQ_LIS` | linear schedule | verified | exact \(N_{\rm shot}(M+1)^2\) sum passes |
| `EQ_EIS` | exponential schedule | verified | schedule and asymptotic scaling pass |
| `EQ_QAE` | conventional-QAE comparator | verified | four-nearest-grid construction passes |
| `EQ_RESOURCES` | CNOT/qubit resource rows | verified | all 37 Table 2 numeric cells pass |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| None | All nine executable formulas are verified. | No target is quarantined or blocked by a formula gate. |

The detailed source-to-code derivations live in `DERIVATION_TRACE.md`, the rendered equations in `DERIVATION.md`, and the machine result in `outputs/checks/formula_verification.json`.
