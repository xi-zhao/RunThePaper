# Target Ledger

Each numeric figure/table/panel target gets one entry.

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1 | noncritical entropy surface | EQ001--EQ004 | open | physically_consistent | `outputs/data/fig1_ising_surface.csv` | `outputs/figures/main_fig1_reproduction.png` | `outputs/checks/science_checks.json` | Complete scientific surface; rendering is a downstream presentation check. |
| T002 | Main Fig. 2 | critical entropy curves | EQ001--EQ005 | open | partial | `outputs/data/fig2_critical_entropy.csv` | `outputs/figures/main_fig2_reproduction.png` | `outputs/checks/science_checks.json` | All five series generated; XXX printed sign conflicts with the caption. |
| T003 | Eq. (21) | majorization | EQ002, EQ003, EQ006 | open | partial | `outputs/data/majorization_checks.csv` | not applicable | `outputs/checks/science_checks.json` | Finite L=1..16 falsification sweep; no universal proof claimed. |
| T004 | Eqs. (5)--(13) | formula pipeline and Eq. (11) sign audit | EQ002, EQ003, EQ007, EQ011 | open | partial | `outputs/data/formula_pipeline_checks.csv` | not applicable | `outputs/checks/science_checks.json` | Mode-sum and explicit-spectrum entropy paths agree; labelled occupation sign is independently derived and retained for paper review. |
| T005 | Post-Eq. (13) paragraph | polynomial reliability | EQ002, EQ003 | open | physically_consistent | `outputs/data/formula_pipeline_reliability.csv` | not applicable | `outputs/checks/science_checks.json` | Reports matrix dimensions, cubic dense cost scale and quadrature doubling. |
| T006 | Eq. (14) | XX L<=100 scaling | EQ002--EQ004 | open | partial | `outputs/data/critical_scaling_claims.csv` | not applicable | `outputs/checks/science_checks.json` | 1/3 slope passes; printed g0 shortcut conflicts with Eq. (8). |
| T007 | Eq. (15) | critical-Ising L<=100 scaling | EQ002--EQ004 | open | partial | `outputs/data/coefficient_shortcut_audit.csv` | not applicable | `outputs/checks/science_checks.json` | 1/6 slope passes; printed g_l shortcut and k2 are under fresh review. |
| T008 | Eq. (16) | nearcritical half-chain law | EQ004 | open | physically_consistent | `outputs/data/quantitative_claim_checks.json` | not applicable | `outputs/checks/science_checks.json` | Successive slopes approach 1/6; finite points are not treated as the limit. |
| T009 | XXZ method paragraph | N=20 regime distinction | EQ001, EQ005 | open | physically_consistent | `outputs/data/xxz_regime_checks.csv` | not applicable | `outputs/checks/science_checks.json` | Delta=1 and declared Delta=2 runs use collision-proof checkpoints. |
| T010 | Noncritical paragraph/Fig. 1 caption | reviewer-defined scaling proxy | EQ004, EQ008 | open | partial | `outputs/data/noncritical_scaling_collapse.csv` | not applicable | `outputs/checks/science_checks.json` | The frozen grid/tolerance tests internal consistency only; unpublished `f(x)` is not claimed paper-exact. |
| T011 | Eq. (17) | central-charge coefficients | EQ004 | open | physically_consistent | `outputs/data/critical_scaling_claims.csv` | not applicable | `outputs/checks/science_checks.json` | Independent Ising and XX L=20..100 fits. |
| T012 | Eq. (18) | anisotropy offset | EQ004 | open | physically_consistent | `outputs/data/quantitative_claim_checks.json` | not applicable | `outputs/checks/science_checks.json` | Three gamma values and three block lengths. |
| T013 | Fig. 2 caption | XX/Ising increment ratio | EQ004 | open | physically_consistent | `outputs/data/quantitative_claim_checks.json` | not applicable | `outputs/checks/science_checks.json` | Independent tail finite differences. |
| T014 | Eq. (3)/Fig. 2 caption | XXX sign audit | EQ001, EQ005 | open | partial | `outputs/data/fig2_critical_entropy.csv` | not applicable | `outputs/checks/science_checks.json` | Literal ground manifold and caption-implied curve computed separately. |
| T015 | c-theorem discussion | RG monotonicity | EQ009 | source_only | partial | `outputs/data/rg_flow_proxy.csv` | not applicable | `outputs/checks/science_checks.json` | Proxy runs, but the paper omits an executable RG map; target stays inconclusive. |
| T016 | Eq. (20) | complete reduced spectrum | EQ007 | open | physically_consistent | `outputs/data/product_spectrum_checks.csv` | not applicable | `outputs/checks/science_checks.json` | Complete spectra through L=16, normalization and entropy identity. |
| T017 | DMRG discussion | epsilon-effective rank proxy | EQ007, EQ010 | open | partial | `outputs/data/effective_rank_checks.csv` | not applicable | `outputs/checks/science_checks.json` | Algebraic, resolved, and retained-weight ranks are separate; the finite proxy does not prove the undefined universal claim. |

## Status Values

- `not_started`
- `spec_ready`
- `running`
- `reproduced`
- `physically_consistent`
- `algorithmically_consistent`
- `partial`
- `blocked`
- `planned_large_scale`
- `failed`

For `blocked` or `planned_large_scale` targets, add a plan document and config
path in the `Notes` column, for example:

```text
PLANNED_LARGE_SCALE_RUNS.md
config/<target>_recommended.yaml
```
