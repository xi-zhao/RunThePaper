# Consistency Report

## Paper-level result

| Measure | Result | Meaning |
| --- | ---: | --- |
| inventory completeness | 121/121 classified | 117 display items + 4 claims; unknown remainder false |
| eligible-item coverage | 55/60 = **91.67%** | five eligible items have no accepted evidence |
| covered-item fidelity | **69.30/100** | mean only over covered items |
| reproduction degree | **63.52/100** | uncovered items contribute zero |
| evidence grade | **E1** | current execution/science authority is not fully closed |
| lifecycle | `partial` | critical gate and fresh review fail |

The figure-coverage validator's `numeric_coverage_ratio=1.0` means every eligible
item has a target decision. It does **not** mean every item has been successfully
reproduced. Scientific coverage is the separate 55/60 measure above.

## Covered-item consistency

| Target | Covered items | Evidence summary | Fidelity |
| --- | ---: | --- | ---: |
| T002 | 9 | S2/S3 analytic/direct error `1.67e-16` | 62.19 |
| T004 | 10 | trace/positivity and Bell-fidelity checks pass | 75.64 |
| T006 | 12 | S8(d-f) 100-sample robustness ordering passes | 75.87 |
| T007 | 5 | trace and corner symmetry pass; parameters reconstructed | 52.12 |
| T008 | 12 | S7(d-f) 50-sample robustness ordering passes | 75.42 |
| T009 | 4 | S9 anchors agree within `0.0021` | 63.52 |
| T010 | 3 | S10(b-d) large-`m` population suppression passes | 55.00 capped |

T001, T003 and T005 remain useful auxiliary calculations, but their source
panels are schematic or experimental and therefore they do not count in the
eligible-item numerator or denominator.

## Uncovered-item consistency

| ID | Direct observation | Root attribution | Code fault | Status |
| --- | --- | --- | --- | --- |
| D001 | S10(a) crossover is `m=10`, paper says `m=6` | unresolved | not excluded | scientific mismatch open |
| C001 | no literal Eq. (1) Hermiticity test | scope-definition gap | not excluded | evidence incomplete |
| C002 | no universal all-`m` PST property test | scope-definition gap | not excluded | evidence incomplete |
| C003 | no independent Schur/index test | scope-definition gap | not excluded | evidence incomplete |
| C004 | no phase-aware Bell-gauge test | scope-definition gap | not excluded | evidence incomplete |

None is a confirmed paper error. Source pixels enter only after frozen numerical
data are produced, and no pixel score can convert an uncovered or scientifically
failed item into covered evidence.
