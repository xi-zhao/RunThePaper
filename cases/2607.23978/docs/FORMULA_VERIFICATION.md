# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| QS001 | State and encoding | open | Density normalization and phase rotation checked. |
| QS002 | Observables and variance | open with explicit inconsistency | Both literal and paper-intended symbolic identities are verified. |
| QS003 | Polar fringe readout | open | Polar identity and probability bounds checked. |
| QS004 | Amplitude damping | open | CPTP identity and endpoint limits checked. |
| QS005 | Numerical derivatives | open for variance; POVM not targeted | Central differences are defined; missing POVM elements remain outside executable targets. |

## Blocked inputs

| Missing item | Consequence |
| --- | --- |
| Non-optimal `A1`, `A2` matrices | Fig. 2(a,b) and non-optimal series of (e,f) cannot be scientifically regenerated. |
| Explicit complete-POVM elements | The paper's concluding CFI statement cannot be independently replotted. |
| Reported `Delta gamma` | Exact finite-difference sampling of Fig. 3(c) cannot be source-identical; the smooth derivative remains reproducible. |
