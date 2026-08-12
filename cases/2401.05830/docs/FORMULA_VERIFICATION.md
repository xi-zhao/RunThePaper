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
| EQ001 | figure-consistent GKSL physical model | verified | Supplemental component/matrix forms uniquely imply doubled collapse rates; trace and limiting cases pass. |
| EQ002 | Bloch numerical dynamics | verified | Independently expanded from EQ001 and prepared for 4x4 Liouvillian parity. |
| EQ003 | steady state/locus | verified | Closed solution, affine residual, limits, and ellipse identity agree. |
| EQ004 | rates/modes | verified | Characteristic polynomial and direct eigensolver agree. |
| EQ005 | slow amplitude/strong root | verified | Printed normalized formula and normalization-independent slow-mode zero agree. |
| EQ006 | distance/crossing metrics | verified | Exact affine solution and independent density-matrix propagation agree by construction; runtime tolerances are machine checked. |
| EQ007 | state-preparation mapping | verified | Follows directly from Bloch radius/angle and produces valid probabilities. |
| EQ008 | literal main-text rate comparator | source-only/open | Main Eqs. (1)-(2) are unambiguous but conflict by a factor two with the Supplemental dynamics; implemented only to quantify the discrepancy. |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| Main-text prose `H=Omega sigma_x` | It conflicts with Main Eq. (1), the entire Supplemental derivation, and the Rabi convention, all of which use `H=Omega sigma_x/2`. | The runner follows the mutually consistent equations. The isolated prose statement is retained as an inconclusive likely typographical discrepancy for fresh review, not silently repaired or declared a paper error. |
| Main Eqs. (1)-(2) dissipative rates | With the explicitly printed standard `D[A]`, the main rates give half the damping in Supplement Eqs. (1)-(4). | Theory figures use the Supplemental equations. A literal-main comparator quantifies the factor-two temperature-axis shift; classification remains inconclusive pending fresh review. |
