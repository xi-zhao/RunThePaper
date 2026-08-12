# Formula Verification

This document explains which formulas are allowed to feed numerical reproduction.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/<paper-id> --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQ001 | pure-state QFIM | open: verified | covariance form follows independently from pure-state SLD and direct finite differences |
| EQ002 | optimal-generator theorem | open: verified | Rayleigh-Ritz maximum of a real symmetric QFIM |
| EQ003 | symmetric SU(n) basis | open: verified | bilinear commutators and trace Gram matrix will be tested explicitly |
| EQ004 | OAT state evolution | open: verified | diagonal Jz-squared propagator and norm conservation |
| EQ005 | analytic OAT optimum | open: verified | compared pointwise to QFIM diagonalization away from branch changes |
| EQ006 | SU(4) Hamiltonian | open: verified | direct bilinear construction and Hermiticity/norm checks |
| EQ007 | commuting-generator anchors | open: source-only | used as an independent numeric anchor, not as generator input |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| none | all formulas feeding the six targets have an open gate | implementation may proceed |
