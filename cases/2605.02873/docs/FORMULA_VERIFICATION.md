# Formula Verification

Machine-readable gate: `outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Independent reason |
| --- | --- | --- | --- |
| EQ001 | Finite-width field | verified | Dimensionless phase and quadrature convergence |
| EQ002 | Field derivatives | verified | Differentiation under a bounded finite integral and central-difference check |
| EQ003 | Exact local scores | verified | Product rule, \(\operatorname{Re}(iz)=-\operatorname{Im}z\), and point-slit limit |
| EQ004 | Full Fisher matrix | verified | Positive-semidefinite Gram representation |
| EQ005 | Optimized codes | verified | Cauchy--Schwarz optimum and Gram--Schmidt orthogonality |
| EQ006 | Coded Fisher/retention | verified | Projection theorem and basis invariance |
| EQ007 | Toy-code baseline | verified | Same nuisance metric and normalization as optimized codes |
| EQ008 | Width scan | verified | Slit-local expansion and vanishing narrow-slit limit |

## Numerical Consequences

- All five targets use verified formulas and may run at
  `final_reproduction`.
- A target fails scientifically if the finite-difference score check,
  quadrature convergence, Fisher positivity, code orthogonality, retention
  bounds, or width-scan trend fails.
- The paper's printed Fisher matrices, retention eigenvalues, and width-scan
  values are analytic references used only in checks; they do not feed the
  generated arrays.

## Closed Or Unclear Formulas

None in the frozen scope.
