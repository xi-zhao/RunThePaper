# Numerical Methods

## Implemented Observables

- Stroboscopic autocorrelation `R(n)`.
- Fourier spectra of `R(n)`.
- Peak location near half the drive frequency.
- Half-frequency peak magnitude `h`.
- Variance `Var(h)` over disorder samples.
- Floquet quasienergy adjacent-gap ratio `<r>`.
- Endpoint mutual information from Floquet eigenstates.
- GHZ limiting-state check for endpoint mutual information.

## Generated Data

- `outputs/data/fig1_peak_locking.csv`
- `outputs/data/fig1_fourier_spectra.csv`
- `outputs/data/fig2_level_statistics.csv`
- `outputs/data/fig2_variance_h.csv`
- `outputs/data/fig3_mutual_information_small_ed.csv`
- `outputs/data/fig4_long_range_variance_h.csv`
- `outputs/data/iteration2_fig1_peak_locking_L14.csv`
- `outputs/data/iteration2_fig1_fourier_spectra_L14.csv`
- `outputs/data/iteration2_fig1_phase_boundary_proxy.csv`
- `outputs/data/iteration2_fig2_level_statistics_L6_L8_L10.csv`
- `outputs/data/iteration2_fig2_variance_L10.csv`
- `outputs/data/iteration2_fig3_mutual_information_corrected.csv`
- `outputs/data/iteration2_fig4_long_range_variance_L10.csv`

## Generated Figures

- `outputs/figures/fig1_subharmonic_rigidity_reproduction.png`
- `outputs/figures/fig2_level_statistics_variance_reproduction.png`
- `outputs/figures/fig3_mutual_information_proxy_reproduction.png`
- `outputs/figures/fig4_long_range_variance_reproduction.png`
- `outputs/figures/iteration2_fig1_L14_subharmonic_rigidity.png`
- `outputs/figures/iteration2_fig1_phase_boundary_proxy.png`
- `outputs/figures/iteration2_fig2_level_statistics_variance_L10.png`
- `outputs/figures/iteration2_fig3_mutual_information_corrected.png`
- `outputs/figures/iteration2_fig4_long_range_variance_L10.png`

## Checks

- `outputs/checks/source_figure_render_check.json`
- `outputs/checks/formula_verification.json`
- `outputs/checks/dtc_feature_checks.json`
- `outputs/checks/iteration2_dtc_feature_checks.json`
- `outputs/checks/reproduction_scope_check.json`
- `outputs/checks/harness_case_audit.json`

## Limitations

The local case now reproduces the main numerical features, but the original paper's large-scale claims still require larger `L` and much heavier disorder averaging. This case therefore remains a feature-level reproduction with explicit large-scale blockers.

## Complete paper-scale channel

The migration adds `config/paper_scale_all.json`, `src/dtc_paper_scale.py`, and `scripts/run_paper_scale_all.py`. Together they enumerate all 38 numerical items across seven calculation families. Dense Floquet diagonalization is used through L=14; the L=16/18 mutual-information check uses a phase-stratified matrix-free Hermitian-pencil subset across eight quasienergy anchors. Time-evolution targets stream state vectors and persist only scalar summaries.

Every work unit has a deterministic identity and seed. Atomic shard files bind the configuration, implementation, and work-unit hashes; aggregation refuses incomplete or stale inputs. The smoke profile exercises every family but substitutes L=4, one realization, short traces, and two-point grids, so its outputs are implementation evidence only.

The isolated execution contracts add `--skip-render`: they freeze and hash the seven aggregate numerical datasets plus checks without importing Matplotlib. Rendering remains a separate post-freeze action over those generated arrays, preventing font discovery or any other presentation concern from entering the attested numerical process.
