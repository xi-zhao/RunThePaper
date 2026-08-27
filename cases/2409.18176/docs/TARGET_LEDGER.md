# Target ledger

| ID | Paper item | Scientific object | Formula cards | Parameter level | Initial state | Planned data | Planned figure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(b), right | vacuum scattering amplitude | EQ002 | proxy_model | evidence_compared | `outputs/data/T001_scattering_amplitude.csv` | `outputs/figures/T001_main_fig1b_scattering.png` |
| T002 | Main Fig. 1(c) | hole dc resistivity vs detuning | EQ001, EQ003--EQ006 | reconstructed_model | pending_quantitative_convergence | `outputs/data/T002_hole_resistivity.csv` | `outputs/figures/T002_main_fig1c_resistivity.png` |
| T003 | Main Fig. 2 | exciton drag vs detuning | EQ001, EQ003, EQ004, EQ006 | paper_subset | evidence_compared | `outputs/data/T003_exciton_drag.csv` | `outputs/figures/T003_main_fig2_exciton_drag.png` |
| T004 | Main Fig. 3, main | many-body resistivity vs temperature | EQ003--EQ006 | paper_subset | evidence_compared | `outputs/data/T004_temperature_resistivity.csv` | `outputs/figures/T004_main_fig3_temperature.png` |
| T005 | Main Fig. 3 inset, solid | near-resonant total resistivity with acoustic phonons | EQ004--EQ006, EQ009 | proxy_model | partially_reproduced | `outputs/data/T005_total_resistivity.csv`, contribution=`total` | `outputs/figures/T005_main_fig3_inset.png` |
| T006 | Main Fig. 4(a) | hole ac conductivity | EQ003, EQ004, EQ006, EQ008 | proxy_model | pending_missing_fit_densities | `outputs/data/T006_ac_hole.csv` | `outputs/figures/T006_main_fig4a_ac_hole.png` |
| T007 | Main Fig. 4(b) | exciton ac conductivity | EQ003, EQ004, EQ006, EQ008 | proxy_model | pending_missing_fit_densities | `outputs/data/T007_ac_exciton.csv` | `outputs/figures/T007_main_fig4b_ac_exciton.png` |
| T008 | Main Fig. 4(c) | trion ac conductivity | EQ003, EQ004, EQ006, EQ008 | proxy_model | pending_missing_fit_densities | `outputs/data/T008_ac_trion.csv` | `outputs/figures/T008_main_fig4c_ac_trion.png` |
| T009 | Supplement Fig. 6 | Kubo minus Boltzmann resistivity | EQ004, EQ005, EQ007 | paper_subset | pending_paper_scale_convergence | `outputs/data/T009_kubo_difference.csv` | `outputs/figures/T009_supp_fig6_kubo_difference.png` |
| T010 | Supplement Fig. 7 | trion drag vs detuning | EQ001, EQ003, EQ004, EQ006 | paper_subset | evidence_compared | `outputs/data/T010_trion_drag.csv` | `outputs/figures/T010_supp_fig7_trion_drag.png` |
| T011 | Main Fig. 3 inset, dash-dot | far-detuned total resistivity with acoustic phonons | EQ009, EQ010 | proxy_model | evidence_compared | `outputs/data/T011_far_detuned_total_resistivity.csv` | `outputs/figures/T011_main_fig3_inset_far_detuned.png` |

T006--T008 cannot be `paper_subset`: although all six fit coefficients are
printed, the species densities used in that fit are not.  They remain
`reconstructed_model`; no density is inferred from source pixels.  No target
is promoted merely because a plot looks similar.

## Whole-paper item accounting

The 41 display items are atomized in `figure_coverage.json`.  Thirty are
eligible numerical series and all 30 now bind formula-derived implementations
through T001--T011.  The remaining 11 display items are schematics, diagrams, or a
qualitative regime ribbon and are explicitly excluded from the scientific
denominator.

### T011 cause card

- Historical direct cause: the target scope was incomplete.  The T005 CSV contains
  one near-resonant total, its many-body value, and a phonon component; it does
  not contain the paper's second far-detuned total.
- Historical root cause: confirmed reproduction-code defect.  The grouped
  implementation interpreted the inset legend as contribution types rather
  than two detuning regimes.
- Repair: T011 evaluates the paper's asymptotic limit directly,
  `rho_total/rho0 = 1 + rho_ph/rho0`; no arbitrary finite detuning is guessed.
- Evidence: the isolated run completed in under one second, read all declared
  inputs, attempted no forbidden access, and passed the component-sum and
  zero-many-body checks.
- Remaining boundary: the absolute acoustic-phonon calibration is not printed,
  so the runnable curve stays `proxy_model`; this limits fidelity but no longer
  reduces implementation coverage.
