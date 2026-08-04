# Derivation trace

| Formula | Source | Independent implementation | Check |
|---|---|---|---|
| Exact linear dispersion | `source publication material/SM.tex:108-119` | `src/nonlocal_ch_audit.py::exact_growth_rate` | source transcription + regression test |
| Discrete (T_c) | Exact dispersion + torus spectrum | `search_discrete_modes_2d` | proof-bounded search and 1000-shell cross-check |
| Finite-(k) criterion | Interior vertex of (D(q)) | `finite_wavenumber_threshold` | exact algebra and Task 2 classification |
| Mapping singularity | `source publication material/SM.tex:170-192` | `mapping_singular_density`, `mapping_exponent` | denominator zero and residue test |
| (A_4) | Taylor series of exact dispersion | `gradient_coefficients` | small-(s) coefficient recovery |
| (k_{sel}) | Stationarity of conserved growth | `selected_wavenumber` | derivative equals zero |
