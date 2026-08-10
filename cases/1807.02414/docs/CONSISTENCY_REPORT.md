# Consistency Report

| Target | Level | Evidence | Remaining difference |
| --- | --- | --- | --- |
| T001 Euler curves | `exact_match` | odd profiles, charged speed 0.43388365, post-freeze curve-pixel F1 93.49/100 | finite rapidity-grid staircase at line thickness scale |
| T001 solid curves | `feature_match` | independent `(D C)/chi` broadening reproduces the six-curve geometry | scalar collective-spin projection, not full non-diagonal spectral operator |
| T002 ell=3 | `exact_match` | 0.136197 vs 0.137, 0.59% | printed rounding/convention residual |
| T002 ell=4 | `exact_match` | 0.280863 vs 0.281, 0.05% | printed rounding |
| T002 ell=7 | `partial_match` | 0.730768 vs 0.744, 1.78% | unresolved convention/numerical discrepancy, no fit applied |
| T003 tDMRG | `blocked` | planned large-scale specification | external many-body simulation not run |

All physics invariants and the isolated provenance gate pass. The case remains
scientifically partial because T001 uses a reduced diffusion operator and T003
is deferred.
