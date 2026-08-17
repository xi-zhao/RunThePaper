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
| EQ001 | XY/XXZ models | open | source-traced; limiting signs checked explicitly |
| EQ002 | Majorana covariance | open | source-traced; antisymmetry and normalization derived |
| EQ003 | entropy observable | open | source-traced; binary-mode normalization checked |
| EQ004 | scaling references | open | source-traced; CFT coefficients derived |
| EQ005 | finite XXX entropy | open | source-traced; Schmidt identity checked; convention discrepancy retained |
| EQ006 | majorization | open | source-traced; padding and normalization derived |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| none | all formula dependencies are open | numerical implementation may proceed |

An open formula gate does not resolve the XXX Hamiltonian/caption discrepancy.
It means both conventions are sufficiently specified to calculate and compare
without borrowing the author's curve.
