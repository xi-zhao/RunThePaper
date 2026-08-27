# Target Ledger

All 23 reproducible theory-numerical panels are covered by ten target bundles.
Schematics and non-numerical context are excluded. Every generated result comes
from equations or independently implemented numerical methods.

| Target | Paper panels | Core object | Verdict | Acceptance evidence |
| --- | --- | --- | --- | --- |
| T001 | Fig. 1(c) | EQ001 | reproduced (analytic) | four identities, residual <= `1.34e-15` |
| T002A | Fig. 2(a-b) | EQ005/MTH002 | reproduced | Gaussian dynamics, steady limit, author trajectories |
| T002C | Fig. 2(c) | EQ002 | reproduced | 3 x 1000 author values, max error `2.85e-13` |
| T002D | Fig. 2(d) | EQ002/EQ006 | reproduced | ergotropy arrays and Gaussian-invariant checks |
| T003 | Fig. 3(a-d) | EQ002/EQ003 | reproduced | invariant `5.33e-15`; author cuts `1.78e-15` |
| T004 | Fig. 4(a-b) | EQ004 | partially reproduced | final formula residual `7.11e-15`; released data are stale |
| TS01 | Fig. S1(a-d) | EQ005/MTH002 | partially reproduced; paper claim rejected | exact Gaussian surface plus cutoff-10 convergence diagnosis |
| TS02 | Fig. S2(a-c) | EQ003 | reproduced | derivative identities, signs, and zero contours |
| TS03 | Fig. S3(a-c) | EQ002 | reproduced with source-axis correction | nine normalized curves, absolute audit arrays, identities, unit intercepts, and endpoint checks |
| TS04 | Fig. S4(a-b) | EQ006 | reproduced | passive-energy positivity and ergotropy margin |

## Scope Accounting

- Numerical panels selected: 23.
- Numerical panels executed: 23.
- Unselected reproducible numerical panels: 0.
- Fully reproduced target bundles: 8.
- Partially adjudicated target bundles: 2.
- Pending target bundles: 0.
- Formula numericalization violations: 0.

T004 is limited by version-mismatched released data. TS01 is limited by the
paper's undisclosed finite-Hilbert cutoff, not by missing local computation.
TS03 is scientifically complete but capped below exact-array credit because
the source label is internally inconsistent and no underlying array is public.
