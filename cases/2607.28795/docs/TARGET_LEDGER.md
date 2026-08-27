# Target Ledger

| Target | Paper item | Scientific object | Formula gate | Parameter match | Status | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Tables I and VI (eight mitten rows) | Independently constructed `H_X,H_Z`, ranks, `n,k`, rate, check weight, CSS commutation, square invertibility, canonical logical weights | verified Q001-Q003 | `paper_exact` | partial: printed construction inconsistent | `outputs/data/T001_code_parameters.json`, `outputs/figures/T001_mitten_algebra_audit.png`, `outputs/checks/T001_science.json`, `outputs/checks/reported_result_comparison.json` |
| T002 | Table V | Parallel-magic resource counts from Eq. (E15) for all eight codes and `d_rep={5,7,9,11}` | verified Q004 | `paper_exact` | reproduced: 32/32 exact | `outputs/data/T002_magic_counts.csv`, `outputs/figures/T002_magic_resource_grid.png`, `outputs/checks/T002_science.json` |
| T003 | Fig. 8 / Algorithm 1 | Independently implemented sketch-ISD correctness plus bounded runtime scaling | verified Q005-Q006 | `proxy_model` | feature reproduced; paper benchmark identity unavailable | `outputs/data/T003_sqetch_benchmark.csv`, `outputs/figures/T003_fig8_reduced.png`, `outputs/checks/T003_science.json`, `outputs/runs/source-blind-render-v4/run_attestation.json` |
| T004 | Table X | Utilization `rho_i=f_i t_i/T_cyc` and mean latency `sum_i f_i t_i` | verified Q007 | `paper_exact` for printed arithmetic inputs | reproduced: 24/24 within printed rounding | `outputs/data/T004_realtime.csv`, `outputs/figures/T004_realtime_decoder.png`, `outputs/checks/T004_science.json` |

## Explicitly deferred numerical scope

- Fig. 2 and Table IX decoder experiments: the exact detector models, schedules,
  tuning, seeds, and baseline identities are absent. Their billion-shot scale is
  secondary; more compute cannot recover the missing scientific contract.
- Fig. 9: external detector-error model plus incompletely specified decoder
  tuning and seed ensemble.
- Fig. 12 and Table XI: exact hook-free schedules and optimized data-layout
  permutations are absent from the PDF and live only in the forbidden author
  release.
- Tables II-IV, VIII, XII: exact optimized gadget, schedule, or routed-layout
  artifacts are not fully specified in the paper.

These rows remain in `figure_coverage.json`; none are silently counted as
covered by T001-T004.

## Current gate state

- Numerical run: `source-blind-bounded-v7`, attested, 0 forbidden accesses.
- Render run: `source-blind-render-v4`, attested, 0 forbidden accesses.
- Author-code boundary: passed; the published repository was not opened.
- Pixel state: table-derived evidence figures are not paper-panel pixel targets;
  T003 is also not applicable
  because its reduced numerical object is not registerable to paper Fig. 8.
- Fresh-context falsification review: pending, so the case is not complete.
