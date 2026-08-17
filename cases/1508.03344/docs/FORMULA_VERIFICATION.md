# Formula Verification

Seven formula cards gate every numerical target. All are independently traced
from the manuscript and verified; no author code, author numerical array,
digitized curve or source pixel feeds the numerical generator.

| Formula | Role | Gate | Independent check |
| --- | --- | --- | --- |
| EQ001 | Floquet eigensystem | verified | generated operators are unitary to `3.781e-12` |
| EQ002 | log-normal Fig. 1 drive | verified | printed duration and disorder identities are unit tested |
| EQ003 | circular adjacent-gap ratio | verified | circular ordering and crossover checks pass |
| EQ004 | SG susceptibility/correlation | verified | bounds, contrast and crossing checks pass |
| EQ005 | positive Lehmann spectrum | verified with disclosed interpretation | positivity and half-sum rule pass; literal printed form is complex |
| EQ006 | two-stage pi drive | verified with disclosed duration branch | products `hT1` and `JT2` are preserved |
| EQ007 | free-drive phase boundaries | verified | all four sectors occur on the exact paper domain |

The machine-readable gate is `outputs/checks/formula_verification.json`.
Uncertainty in EQ005/EQ006 limits paper-exact attribution; it does not permit
pixel-derived physics or silent parameter fitting.
