# Target Ledger

Each numeric figure/table/panel target gets one entry.

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | Fig. 2 (both panels) | numeric_reproduction | single_mode_partition_z_R, thermal_occupation_n_beta | verified | reproduced | `outputs/data/fig2_left_degeneracies.csv`, `outputs/data/fig2_right_occupation.csv` | `outputs/figures/fig2_reproduction.png` | `outputs/checks/fig2.json` | Paper-exact params Ex.2 m=2, Ex.3 m=2, Ex.4 m=3 |
| T2 | 1D solvable spin model (Eq. Hamil1Dspin) | numeric_reproduction (validation) | solvable_1d_spin_model_free_paraparticles | verified | physically_consistent | (spectra in check) | — | `outputs/checks/ed_validation.json` | ED confirms emergent free paraparticles & z_R=1+m x |

## Paper-parameter cards

### T1 — Fig. 2 exclusion statistics + free-particle thermodynamics

- Original paper parameters (from the **published figure legend**):
  species = {fermion (m=1), boson (m=1), Ex.2 (m=2), Ex.3 (m=2), Ex.4 (m=3)};
  left panel: level degeneracies `d_n` for `n=0..4`;
  right panel: `<n>_beta` over `beta*eps in [-4, 4]`.
- Generated-run parameters: identical — `species_table(m3=2, m4=3)`, `beta*eps`
  on `linspace(-4, 4, 401)`, `n_max=4`.
- Parameter match: **paper_exact**.
- Reason for mismatch: none. (The `m=5` in the prose is a text/figure
  inconsistency; the figure is the reproduced artifact.)
- Reference comparison: `analytic_reference` — the paper's Fig. 2 curves and our
  curves are the *same* closed-form functions (`d_n` = coeffs of `z_R`,
  `<n>=x z'/z`); the comparison is analytic-to-analytic and matches exactly.
- Generated-data provenance: `analytic_reference` (closed-form, no digitization).
- Artifact stage: `final_reproduction`.

### T2 — 1D solvable spin-model ED (validation of the physics)

- Original paper parameters: Ex.3 R-matrix, Hamiltonian Eq. Hamil1Dspin, open BC.
  The paper gives no figure-level `N`; chain length is illustrative.
- Generated-run parameters: `N in {4,5}` with `m=2`, `N=4` with `m=3`, random
  `J_i in [0.5,1.5]` (open BC `J_N=0`), `mu_i in [-1,1]`, seeds fixed.
- Parameter match: **paper_exact** (model/statistics exact; `N` not claim-relevant).
- Reference comparison: `analytic_reference` — ED spectrum vs the free-paraparticle
  analytic prediction `sum_{k in S} eps_k`, multiplicity `m^{|S|}`.
- Generated-data provenance: `independent_numerics` (brute-force ED).
- Artifact stage: `final_reproduction` (exact reproduction of the solvable model).

## Status Values

`not_started`, `spec_ready`, `running`, `reproduced`, `physically_consistent`,
`algorithmically_consistent`, `partial`, `blocked`, `planned_large_scale`, `failed`.
