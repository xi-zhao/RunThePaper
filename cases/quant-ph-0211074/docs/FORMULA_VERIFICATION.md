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
| EQ007 | complete reduced spectrum | open | every factor source-traced; normalization and independent entropy identity checked |
| EQ008 | noncritical scaling proxy | open with attribution cap | the reconstructed fixed-coordinate proxy is defined and gated, but is not the unpublished paper function `f(x)` |
| EQ009 | RG monotonicity | source-only | the paper claim is traced, but no executable RG map or matching convention is published |
| EQ010 | epsilon-effective rank proxy | open with attribution cap | exact, resolved, and retained-weight rank semantics are separated; the paper does not define “relevant” |
| EQ011 | Eq. (11) occupation sign | open with source discrepancy | Pauli/Fock algebra gives `(1-nu)/2`; pair exchange leaves entropy and the unordered spectrum unchanged |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| EQ009 | no lattice RG transformation, scale matching, or post-RG observable | only the declared proxy may run; the paper claim stays inconclusive |

An open formula gate does not resolve a publication discrepancy. It means the
scientific object is sufficiently specified to calculate and compare without
borrowing the author's curve. EQ008 and EQ010 open only their explicitly named
proxies; they do not make an unpublished scaling function or relevance
threshold paper-exact. EQ011 opens the entropy calculation while retaining the
printed occupation-sign conflict for fresh-context review.
