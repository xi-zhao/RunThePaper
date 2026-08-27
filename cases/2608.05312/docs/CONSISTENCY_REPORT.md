# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | No target can be called paper-exact because author seeds/grids and one Hamiltonian parameter are unpublished. |
| feature_match | 10 | Scientific feature and declared numerical tolerances pass. |
| partial_match | 1 | T010 passes its feature contract on a reduced sample/grid. |
| input_match_only | 0 | No executed target stops at input matching. |
| uncovered | 1 target / 4 items | T011 has four source-blocked items. |
| not_in_scope | 1 | Fig. 1(a,b) is schematic. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 1(c) | feature_match | `size_scaling.csv`, `scaling_fits.json` | large-N error `<0.002` | exact optimizer grid/seeds absent |
| T002 | Fig. 2(a,b) | feature_match | `fig2_dynamics.csv` | no author curve data for pointwise error | raster-only reference |
| T003 | Fig. 2(c,d) | feature_match | `fig2_dynamics.csv` | endpoints match printed claims | raster-only peak shape |
| T004 | Fig. 3 | feature_match | `temperature_lines.csv`, `temperature_map_n6.csv` | boundary errors `0.0045/0.0029` | exact grid/seeds absent |
| T005 | Fig. S1 | feature_match | `site_n_sweep.csv` | gap `-0.080` vs `-0.044` | site-N optimum is seed/grid sensitive |
| T006 | Table S1 | feature_match | `table_s1_regimes.csv` | MAE `0.00615`, max `0.04138` | unpublished seeds/grid |
| T007 | Table S2 | feature_match | `table_s2_detuning.csv` | MAE `0.00182` | reconstructed shared inputs |
| T008 | Fig. S2 | feature_match | `scaling_fits.json` | alpha `0.799` vs `0.77` | optimizer/grid reconstruction |
| T009 | Fig. S3 | feature_match | `site_n_dynamics.csv` | no pointwise author data | author seed absent |
| T010 | Fig. S4 | partial_match | `temperature_map_n64.csv` | 5 realizations, `9x9` map | local compute choice |
| T011 | Fig. S5 | uncovered | `figure_coverage.json` | 0/4 series have independent output | publication omits indispensable benchmark inputs; code judgment not applicable yet |
| T012 | Fig. S1(b) baseline | feature_match | `implementation_probe/site_n_no_dissipation_baseline.csv`, `site_n_baseline_check.json` | `0.5536 +/- 0.0548` vs paper `0.65` | author disorder seeds are unpublished; absolute error `0.0964` passes the declared `0.12` tolerance |

The authoritative machine checks are `outputs/checks/numerical_feature_checks.json`,
`outputs/checks/similarity_scorecard.json`, and
`outputs/checks/figure_coverage_check.json`. The authoritative item list is
`figure_coverage.json`.
