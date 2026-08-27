# Target Ledger

| Target | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Fig. 1b-d: subharmonic rigidity | feature_match | `outputs/figures/iteration2_fig1_L14_subharmonic_rigidity.png`, `outputs/data/iteration2_fig1_peak_locking_L14.csv`, `outputs/data/iteration2_fig1_fourier_spectra_L14.csv` | Reproduces the main contrast at `L=14`: free-spin peak drifts, interacting peak locks at `1/2`. |
| Fig. 1a: phase diagram | partial_proxy | `outputs/figures/iteration2_fig1_phase_boundary_proxy.png`, `outputs/data/iteration2_fig1_phase_boundary_proxy.csv` | Local `Var(h)` peak proxy generated. Full phase boundary requires combining all original diagnostics. |
| Fig. 2a: level statistics | partial_feature_match | `outputs/figures/iteration2_fig2_level_statistics_variance_L10.png`, `outputs/data/iteration2_fig2_level_statistics_L6_L8_L10.csv` | Same observable generated through `L=10`, but original crossing needs far more disorder samples. |
| Fig. 2b: variance of half-frequency peak | feature_match | `outputs/figures/iteration2_fig2_level_statistics_variance_L10.png`, `outputs/data/iteration2_fig2_variance_L10.csv` | Variance peak appears and shifts with interaction strength. |
| Fig. 3a: mutual information finite-size flow | feature_match | `outputs/figures/iteration2_fig3_mutual_information_corrected.png`, `outputs/data/iteration2_fig3_mutual_information_corrected.csv` | Corrected observable now shows `log 2` at `epsilon=0` and collapse toward zero at large detuning. |
| Fig. 3b-d: scaling collapse | planned_large_scale | `FIG3_LARGE_ED_PLAN.md`, `PLANNED_LARGE_SCALE_RUNS.md`, `config/fig3_large_ed_recommended.yaml`, `outputs/checks/iteration2_dtc_feature_checks.json` | Critical exponent collapse is not claimed locally; concrete recommended large-ED parameters are now recorded. |
| Fig. 4: long-range trapped-ion variance | feature_match | `outputs/figures/iteration2_fig4_long_range_variance_L10.png`, `outputs/data/iteration2_fig4_long_range_variance_L10.csv` | Reproduces a variance peak in the long-range `alpha=1.5` model. Schematic inset is not reproduced. |

## Case Status

`feature_reproduced_large_scale_blocked`

The main numerical features are reproduced locally. Full phase boundaries, scaling collapse, and critical exponents remain large-scale targets.

## Full-scope implementation state

| Scope | Code state | Execution state | Scientific claim |
| --- | --- | --- | --- |
| Main Figs. 1–4, all numerical panels/insets | ready | all-family smoke only | legacy feature evidence; not paper-exact |
| Supplement Fig. S1, all three panels | ready | all-family smoke only | protocol interpretation disclosed; not paper-exact |
| Supplement Fig. S2, all nine panels | ready | all-family smoke only | full production and scaling validation pending |
| Supplement Fig. S3, all ten panels | ready | all-family smoke only | full 1000-period production pending |

The authoritative item inventory is `figure_coverage.json`. The shared implementation contract maps every one of the 38 numerical items to T001–T004. Code readiness closes the prior silent-skip gap; it does not promote any target to complete.

All four target families are covered by the attested `1608.02589-all-family-smoke-v2` isolated run. That evidence is execution-only: it binds the implementation and configuration, but the smoke selector deliberately replaces paper-scale sizes, grids, trace lengths, and disorder counts.
