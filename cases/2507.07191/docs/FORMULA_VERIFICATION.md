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
| EQ001 | stable-rank superposition inequality | open / verified | Proposition 1 source trace and triangle-inequality proof pass. |
| EQ002 | feasibility | open / verified | Exact Cauchy-Schwarz and rational checks pass. |
| EQ003 | scalar dual root | open / verified | Proposition 2 source trace and derivative check pass. |
| EQ004 | inverse-square distribution | open / verified | Source KKT form and normalization pass. |
| EQ005 | uniqueness | open / verified | Appendix strict-concavity proof applies to the ordered nondegenerate energies. |
| EQ006 | energy and residuals | open / verified | Primal-dual equality and both active constraints pass numerically. |
| EQ007 | support and tail | open / verified | Positive KKT weights, top-five obstruction and unequal slopes pass. |
| EQ008 | two-level extension | open / verified | Appendix formula and exact rational aggregates pass. |
| EQ009 | 4x4 periodic AFHM Hamiltonian | open / verified | Author TeX convention and complete 65,536-state sector decomposition pass. |
| EQ010 | ground-state overlap bound | open / verified | All three `Λ(D)` values match the printed table precision. |
| EQ011 | Gaussian-broadened `Predict+` | open / verified | Width-0.1 source trace and three vector-curve comparisons pass. |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| None | All eleven numeric gates are open. | T001-T004 are allowed to run. |
