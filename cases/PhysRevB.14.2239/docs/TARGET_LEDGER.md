# Target Ledger

| Target | Paper item | Scientific object | Equations | Parameter status | Data output | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 1 | All rational-flux bands for q<50 | EQ001–EQ004 | paper exact | `fig1_spectrum.npz` | q bands, symmetries, [-4,4], trace edges |
| T002 | Fig. 2 | Pure-case skeleton through N=37 | EQ001–EQ005 | paper exact | `fig2_skeleton.npz` | all printed pure families and central bands |
| T003 | Fig. 3 | L2 rectangularization | EQ001–EQ005 | exact map, reconstructed sampling | `fig3_l2_rectangularized.npz` | local coordinate in [0,1], resolved internal bands |
| T004 | Fig. 4 | C2 rectangularization | EQ001–EQ005 | exact map, reconstructed sampling | `fig4_c2_rectangularized.npz` | local coordinate in [0,1], resolved internal bands |
| T005 | Fig. 5 | delta-alpha=0.01 smeared quadrant | EQ001–EQ004, EQ006 | exact field window, reconstructed raster/cutoff | `fig5_blurred_quadrant.npz` | energy bound and finite smeared-band count |
| T006 | Fig. 6, three independently counted series | Three reordered top-edge eigenfunctions | EQ001, EQ007 | paper exact | `fig6_wavefunctions.json` | printed eigenvalues, residual, normalization, order |
| T007 | Supporting checks | Cross-figure assertions already carried by T001-T006 | EQ001–EQ007 | mixed by constituent check | `science_checks.json` | all 11 checks pass; excluded from item denominator |
| T008 | Section VI Cantor-spectrum theorem | Irrational spectrum is uncountable, measure zero, and Cantor-homeomorphic | EQ005 | not applicable | — | uncovered; independent proof/check missing |
| T009 | Section VII continuity theorem family | Set-valued continuity and rational/irrational spectral-measure behavior | EQ005–EQ006 | not applicable | — | uncovered; independent convergence artifact missing |

## Item-level Coverage

- Eligible items: **10** — five whole figures, three Fig. 6 series, and two
  central text-only theorem families.
- Covered: **8**; uncovered: **2**; coverage: **80.00%**.
- Covered-item fidelity: **89.62/100**.
- Reproduction degree: **71.70/100**, with T008 and T009 each contributing zero.

## Explicit Uncovered Items

| Item | Direct cause | Code responsibility | Required closing evidence |
| --- | --- | --- | --- |
| T008 / Section VI Cantor-spectrum theorem | No independent theorem-specific proof/check artifact. | `not_excluded`: existing code tests finite rational spectra, not the irrational-limit topology. | `outputs/checks/T008_cantor_spectrum.json` from an independent nested-cell/rational-approximant test. |
| T009 / Section VII continuity theorem family | No independent set-valued and measure-continuity artifact. | `not_excluded`: no claim-specific convergence oracle exists. | `outputs/checks/T009_spectrum_continuity.json` separating set convergence from measure convergence. |

The final lifecycle status is derived by Harness and cannot be inferred from
this ledger alone. Existing display arrays, scores, and run attestations were
not changed by this inventory migration.
