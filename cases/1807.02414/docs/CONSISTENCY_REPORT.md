# Consistency Report

| Target | Final disposition | Evidence consistency | Remaining boundary |
| --- | --- | --- | --- |
| T001 Euler curves | `reproduced` | odd profiles, charged speed 0.43388365, frozen-curve pixel F1 93.49/100 | raster-only source and finite rapidity-grid staircase |
| T001-DIFFUSIVE | `externally_blocked` | full non-diagonal operator passes isolated smoke invariants | immutable four-variant CuPy/A100 campaign not executable locally |
| T002 ell=3 | `reproduced` | 0.136197 vs 0.137, 0.59% | printed rounding/convention residual |
| T002 ell=4 | `reproduced` | 0.280863 vs 0.281, 0.05% | printed rounding |
| T002 ell=7 | `reproduced` | 0.730768 vs 0.744, 1.78% | residual preserved; no new discrepancy adjudication |
| T003 tDMRG | `externally_blocked` | purification, conservation, and checkpoint/resume pass isolated smoke | immutable four-variant CuPy/A100 campaign not executable locally |
| T004 hard-rod limit | `reproduced` | direct reduction agrees to `5.55e-17` and conserves the weighted mode sum | no display/pixel comparison applies |
| T005 free-model limit | `reproduced` | zero scattering produces an exactly zero operator | no display/pixel comparison applies |
| T006 entropy production | `reproduced` | non-negative pairwise-square identity, graph-Laplacian structure, spectrum, and 64 random forms agree | no display/pixel comparison applies |

Formula gates are open for all 12 equation cards. The fixed-denominator item
ledger and seven-target ledger have zero pending entries. Case-level science
and lifecycle status may remain incomplete because independent review is a
separate requirement; no fresh-review result is inferred from author-side
implementation evidence.
