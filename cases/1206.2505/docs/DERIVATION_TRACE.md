# Derivation Trace

| Card | Source | Numerical role | Code | Status |
| --- | --- | --- | --- | --- |
| EQ001 | main text, boundary partition function | Loschmidt rate definition | `loschmidt_rate` | verified |
| EQ002 | TFIM Hamiltonian and dispersion | all mode calculations | `dispersion`, `bogoliubov_angle` | verified |
| EQ003 | exact quench free energy | rate integral | `loschmidt_rate` | verified |
| EQ004 | Fisher-zero formula | Main Fig. 1 | `fisher_zero_lines` | verified |
| EQ005 | critical momentum/time | periodic cusp checks | `critical_momentum`, `critical_period` | verified |
| EQ006 | work cumulant | Main Fig. 2 | `cumulant_rate` | verified |
| EQ007 | Legendre transform | work-rate curves/surface | `work_rate_grid` | verified |
| EQ008 | cluster decomposition and Pfaffian | Main Fig. 3 bottom | `longitudinal_correlation_dynamics` | reconstructed and cross-checked |
| EQ009 | extreme-quench Loschmidt matrix | sector switching | `extreme_quench_loschmidt_rates` | source-sign discrepancy exposed |
| EQ010 | tilted postselection | normalized observable | `postselection_normalization_check` | source-normalization discrepancy exposed |
| EQ011 | complex-time identity | normalized characteristic function | `complex_time_postselection_check` | source-normalization discrepancy exposed |
| EQ012 | general time-dependent mode equation | ramp family | `ramp_mode_occupations` | reconstructed protocol |

Detailed algebra is in `DERIVATION.md`; machine gates are in
`outputs/checks/formula_verification.json`.
