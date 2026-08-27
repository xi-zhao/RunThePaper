# Target Ledger

| Target ID | Plain-language meaning | Paper item | Formula gate | Status | Main evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `T001` | Numerical Wigner fields behind the theorem overview | Main Fig. 1 | reconstructed/open | `physically_consistent` | `outputs/figures/overview_numeric_surfaces.png`; `outputs/checks/t001_paper_target_run.json` | exact fields; reconstructed 3D rendering; source threshold inconsistency |
| `T002` | W-state Wigner and characteristic panels | Main Fig. 2(a,b) | verified/open | `reproduced` | `outputs/figures/w_state_wigner_characteristic.png`; `outputs/checks/t002_paper_target_run.json` | paper-exact final reproduction |
| `V001` | Independent disk-integral and radius check | Fig. 2(a) validation | verified/open | `reproduced` | `outputs/checks/v001_paper_target_run.json` | analytic formula agrees with quadrature to \(1.1\times10^{-16}\) |
| `V002` | Independent 7-by-7 characteristic-matrix check | Fig. 2(b) validation | verified/open | `reproduced` | `outputs/checks/v002_paper_target_run.json` | 19 differences and witness \(0.0175804\) |
| `V003` | State norm, slice integrals, both thresholds, and smoothing check | Fig. 1 validation | reconstructed/open | `physically_consistent` | `outputs/checks/v003_paper_target_run.json` | confirms numerator 52 from the state and records printed 56 separately |

The identifiers above are only stable machine keys. Their meanings are always
shown beside them so a reader does not need to memorize abbreviations.
