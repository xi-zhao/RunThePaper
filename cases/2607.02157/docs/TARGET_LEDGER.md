# Target Ledger

Each numeric figure/table/panel target gets one entry.

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2 (a1-c2 + insets), 18 atomic series | capacity/thermodynamics scan | EQC001-EQC010, EQC013, EQC014 | verified | reproduced | outputs/data/fig2_*_paper_exact.csv + outputs/data/nmse_*_paper_exact.csv | outputs/figures/fig2_*.png | outputs/checks/fig2_*.json | W1 scope 18/18. Historical target score 80; stronger run/physics/review evidence remains open. |
| T002 | Fig. S1 (a,b,c), 7 atomic series/families | spectral analytics | EQC002, EQC012, EQC013 | verified | reproduced | outputs/data/figS1_*.csv | outputs/figures/figS1_*.png | outputs/checks/figS1_*.json | W1 scope 7/7. Panel b uses 400 rather than 10000 disorder realizations; this limits fidelity, not coverage. Historical target score 80. |
| T003 | Fig. S2 (a1-c2), 18 atomic series | multi-step capacity scan | EQC001-EQC004, EQC013, EQC014 | verified | reproduced | outputs/data/fig2_*_paper_exact.csv + outputs/data/nmse_*_paper_exact.csv | outputs/figures/figS2_*.png | outputs/checks/figS2_*.json | W1 scope 18/18. The full-Pauli versus reduced-readout wording conflict requires a provenance/hash audit before evidence promotion. Historical normalized fidelity 77.65. |

## Paper-Parameter Cards

### T001 (Fig. 2)

- Original paper parameters: L=6; beta=1; gamma0=0.1; dt=1; lambda=0.05;
  H1=sum sigma^z; MG drive (beta_MG=0.2, gamma_MG=0.1, tau_MG=18, sample
  interval 3, rescaled to [-1,1]); binning B=50; N_wash=500; N_eval=2000;
  5000 sequences; disordered TFIM (h=1, J_ij ~ U[-J/2,J/2]) averaged over 100
  realizations x 5000 sequences per J in [1e-1, 1e2] (log grid); cluster model
  (J_zz=0.1, J_zxz=(1-J_zz)alpha, h_x=(1-J_zz)(1-alpha)) for alpha in [0,1];
  NMSE with N_train=2000, N_test=2000, eta=1e-5, 500 sequences, full Pauli basis.
- Generated-run parameters (A100 paper-exact campaign): identical physics
  constants; cluster 5000 sequences x 21 alpha points; TFIM 100 realizations
  x 5000 sequences x 25 J points; NMSE both rows on the full 4^6-1 Pauli
  readout. Supersedes the first local reduced pass.
- Parameter match level: `paper_exact`.
- Artifact stage: `production`.

### T002 (Fig. S1)

- Original paper parameters: same MG/model constants; a: 5000 sequences of
  5000 steps for G(omega) and averaged Fourier spectrum; b: 10000 disorder
  realizations of the L=6 TFIM spectrum per J, normalized by spectral width;
  c: single cluster-model spectrum vs alpha.
- Generated-run parameters: a/c paper-exact (deterministic); b at 400 disorder
  realizations (only affects one supplementary spectral panel's smoothness).
- Parameter match level: `paper_exact` (a/c); b's reduced realization count
  affects panel smoothness only, not features.
- Artifact stage: `production`.

### T003 (Fig. S2)

- Original paper parameters: identical to Fig. 2 protocol; tau in {0,1,2};
  h in {1,2,3}; NMSE with the Fig. 2 readout protocol.
- Generated-run parameters: same paper-exact ensembles as T001; full-Pauli NMSE.
- Parameter match level: `paper_exact`.
- Artifact stage: `production`.

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
