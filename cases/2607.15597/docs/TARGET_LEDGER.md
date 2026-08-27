# Target Ledger

| Target | Paper item | Object | Formula cards | Gate | Status | Data / figure / check |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2 | Single-ion gate dynamics | EQC001-004 | verified | guarded final run passed; evidence_compared | `fig2_gate_dynamics.csv`; `fig2_reproduction.png`; `target_runs/T001.final_reproduction.json` |
| T002 | Fig. 3 | Chain-size infidelity and duration | EQC005,007 | reconstructed | partially_reproduced | `fig3_chain_scaling.csv`; `fig3_reproduction.png` |
| T003 | Fig. 4 | Interconnect and hybrid-memory scaling | EQC008-010 | source_only | blocked_missing_formula; historical evidence only | `fig4_architecture.csv`; `fig4_reproduction.png`; `source_consistency.json` |
| T004 | Table S1 | Operating point | EQC003,012 | verified | guarded final run passed; reproduced | `table_s1_operating_point.csv`; `target_runs/T004.final_reproduction.json` |
| T005 | Table S2 | Lifetime/decay conversion | EQC005 | verified | guarded final run passed; reproduced | `table_s2_decay.csv`; `target_runs/T005.final_reproduction.json` |
| T007 | Fig. S1 / Table S4 | Multi-mode closure | EQC011 | verified | partially_reproduced | `figs1_modes.csv`; `figs1_schedule.csv`; `figs1_closure_reproduction.png` |
| T008 | Fig. S3 / Table S6 | Thermal feature model | EQC005-006 | reconstructed | partially_reproduced | `figs3_thermal.csv`; `figs3_thermal_reproduction.png` |
| T009 | Table S7 | Steane/BB gate accounting | method arithmetic | not_applicable | guarded final run passed; reproduced | `table_s7_gate_counts.csv`; `target_runs/T009.final_reproduction.json` |
| T010 | Table S11 / Fig. S5 | qLDPC Fowler projections | EQC010 | source_only | blocked_source_discrepancy; historical evidence quarantined | `figs5_qldpc_projection.csv`; `figs5_qldpc_projection_reproduction.png` |
| T011 | Table S13 | Circular operating points | EQC005,012-013 | reconstructed | runnable (exploratory only) | `table_s13_circular.csv` |
| T012 | Fig. S6 | Circular gate dynamics | EQC001-005,013 | reconstructed | runnable (exploratory only) | `figs6_circular_dynamics.csv`; `figs6_circular_dynamics_reproduction.png` |
| T013 | Fig. S7 | Circular thermal curves | EQC005-006,013 | reconstructed | runnable (exploratory only) | `figs7_circular_thermal.csv`; `figs7_circular_thermal_reproduction.png` |
| T014 | Table S14 | Ten-ion circular budget | EQC005,013 | reconstructed | runnable (exploratory only) | `table_s14_crystal_budget.csv` |

## Derivation-first migration note

The data and figures listed above predate the target-readiness seam and are
preserved as historical evidence. Their existence does not retroactively
authorize a new numerical run.

- Fig. 2, Table S1, Table S2, and Table S7 each passed an independent guarded
  final run with verified formula/method dependencies and paper-exact
  parameters. Fig. 2 remains `evidence_compared` because author curve points
  are unavailable; the three tables use exact or rounded table comparisons.
- T011-T014 use the independently reconstructed circular error budget and are
  open for exploratory runs only.
- T003 and T010 remain blocked because direct substitution into EQC010 does not
  reproduce Table S11 under one consistent parameter mapping.

## Blocked numerical items

| Paper item | Blocker | Concrete next step |
| --- | --- | --- |
| Table S3 | missing_source_input | Obtain component simulation/calibration notebooks; decay row already checked by T005 |
| Table S5, Fig. S2 | missing_source_input | Export PairInteraction Stark maps, basis config, and overlap-tracking labels |
| Tables S8-S10 | missing_benchmark_metadata / compute | Obtain exact BB matrices, schedules, Stim circuit generator, decoder and seeds; then run staged shots |
| Table S12 | missing_benchmark_metadata | Obtain exact APM matrix/circuit, decoder settings, seeds, and shot contract before profiling any pilot |

See `PLANNED_LARGE_SCALE_RUNS.md` and `config/blocked_reruns.json` for a
machine-readable rerun plan.

## Pixel-registered artifacts

| Target | Generated PDF/PNG | Full-image SSIM | Pixel frontier |
| --- | --- | ---: | --- |
| T001 | `fig2_pixel_registered` | 0.8276 | eligible; layout passed, strict SSIM failed |
| T002 | `fig3_pixel_registered` | 0.8073 | rendered only; formula reconstructed |
| T003 | `fig4_pixel_registered` | 0.7115 | blocked; historical layout evidence only |
| T007 | `figs1_multimode_pixel_registered` | 0.7491 | eligible; layout passed, strict SSIM failed |
| T008 | `figs3_thermal_pixel_registered` | 0.7135 | rendered only; proxy formula |
| T010 | `figs5_qldpc_pixel_registered` | 0.7418 | rendered only; source-only projection |
| T012 | `figs6_circular_pixel_registered` | 0.8297 | rendered only; proxy open-system model |
| T013 | `figs7_circular_thermal_pixel_registered` | 0.6385 | rendered only; proxy formula |

All files are under `outputs/pixel_registered/`. “Rendered only” is deliberate:
a presentation match cannot promote incomplete scientific provenance. Active
pixel validation is limited to targets whose current derivation and target
contracts pass readiness; T003's earlier layout result remains historical only.
