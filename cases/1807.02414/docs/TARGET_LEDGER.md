# Target Ledger

| Target | Eligible items | Reproduced | External blocker | Final disposition | Evidence |
| --- | ---: | ---: | ---: | --- | --- |
| T001 — Main Fig. 1 Euler curves | 3 | 3 | 0 | `reproduced` | independent TBA data and scientific invariants |
| T001-DIFFUSIVE — full Eq. (13) curves | 3 | 0 | 3 | `externally_blocked` | clean isolated smoke plus measured CuPy/A100 capacity mismatch |
| T002 — printed spin Onsager values | 1 | 1 | 0 | `reproduced` | paper-parameter independent integral evaluation |
| T003 — Main Fig. 1 tDMRG markers | 3 | 0 | 3 | `externally_blocked` | clean isolated purification-TEBD smoke plus measured CuPy/A100 capacity mismatch |
| T004 — hard-rod diffusion limit | 1 | 1 | 0 | `reproduced` | independently coded operator identity and conservation check |
| T005 — free-model zero diffusion | 1 | 1 | 0 | `reproduced` | exact zero-scattering limit |
| T006 — entropy-production positivity | 1 | 1 | 0 | `reproduced` | weighted pairwise-square identity, Laplacian invariant, spectrum, and random forms |

## Fixed denominator

- eligible items: 13
- `reproduced`: 7
- `externally_blocked`: 6
- `attempted_not_reproduced`: 0
- `pending`: 0
- eligible targets: 7; 5 reproduced and 2 externally blocked

There is no pending set. The six external items are exactly the three full
diffusive curves and three tDMRG marker series. Their direct cause is that the
paper-scale runs were not executable on this host; their root cause is a
machine-verified compute-capacity shortfall, not missing code. Both code paths
pass isolated smoke contracts with empty forbidden-access logs.

## Artifact pointers

- T001/T002 data: `outputs/data/T001_fig1_domain_wall.npz` and
  `outputs/data/T002_diffusion_constants.json`
- analytic checks: `outputs/checks/implementation_closure/campaign_summary.json`
- resource proof: `outputs/checks/final_resolution/resource_benchmark.json`
- full-GHD smoke: `outputs/checks/T001_full_ghd_smoke_checks.json`
- tDMRG smoke: `outputs/checks/T003_tdmrg_smoke_checks.json`
- authoritative state: `outputs/checks/authoritative_reproduction_state.json`

The ledger records author-side final disposition only; it does not represent a
fresh independent-review verdict.
