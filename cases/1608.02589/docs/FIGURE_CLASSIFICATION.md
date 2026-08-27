# Figure Classification

## Main Text Figures

| Figure | Type | Action |
| --- | --- | --- |
| Fig. 1 | Numerical + phase-diagram summary | Peak locking and Fourier spectra reproduced at feature level; local phase proxy generated. |
| Fig. 2 | Numerical | Level-statistics observable and variance peak reproduced at feature level. |
| Fig. 3 | Numerical scaling | Mutual-information finite-size flow reproduced at feature level; scaling collapse not fully rerun. |
| Fig. 4 | Numerical + schematic inset | Long-range variance peak reproduced at feature level. Trapped-ion schematic is not reproduced. |

## Supplementary Figures

| Figure | Type | Action |
| --- | --- | --- |
| Fig. S1 | Numerical time traces and Fourier response | Covered by the same local autocorrelation/Fourier implementation used for Fig. 1. |
| Fig. S2 | Numerical mutual-information scaling | Partially covered by corrected Fig. 3 mutual-information flow; full collapse remains large-scale. |
| Fig. S3 | Numerical Fourier response for clean vs disordered cases | All ten numerical panels are now mapped to T001/T004 and implemented by the paper-scale runner. |

## Generated Targets

| Target | Original reference | Generated result | Status |
| --- | --- | --- | --- |
| Fig. 1 peak locking and Fourier spectra | `internal-paper-reference/Fig1_prl_revision_v1.png` | `outputs/figures/iteration2_fig1_L14_subharmonic_rigidity.png` | feature_match |
| Fig. 1 phase proxy | `internal-paper-reference/Fig1_prl_revision_v1.png` | `outputs/figures/iteration2_fig1_phase_boundary_proxy.png` | partial_proxy |
| Fig. 2 level statistics / variance | `internal-paper-reference/Fig2_v91.png` | `outputs/figures/iteration2_fig2_level_statistics_variance_L10.png` | partial_feature_match |
| Fig. 3 mutual information | `internal-paper-reference/Fig3_v63.png` | `outputs/figures/iteration2_fig3_mutual_information_corrected.png` | feature_match_for_flow |
| Fig. 4 long-range variance | `internal-paper-reference/Fig4_v49.png` | `outputs/figures/iteration2_fig4_long_range_variance_L10.png` | feature_match |

## Complete inventory and code-readiness update

The full paper and supplement contain `38` numerical items: `16` main-text items and `22` supplementary items, plus one non-numerical trapped-ion schematic. `figure_coverage.json` freezes each item separately. All 38 numerical items point to the executable `paper_scale_all_numeric` contract; none is silently skipped or covered by copied pixels.

`config/paper_scale_all.json`, `src/dtc_paper_scale.py`, and `scripts/run_paper_scale_all.py` implement the complete campaign with deterministic work units, atomic checkpoint/resume, fail-closed aggregation, invariant checks, and seven composite numerical renderings. The full production campaign has not run.

## Scope Note

The legacy generated figures demonstrate core observables only. The new full-scope code proves implementation readiness, not paper-exact numerical completion. Neither artifact may be used to claim that the complete PRL numerical campaign has already run.
