# Target Ledger

## Locally executed theory targets

| Target | Paper item | Formula dependencies | Parameter state | Status | Data / figure |
| --- | --- | --- | --- | --- | --- |
| T001 | Main 1(a), Supp. 2(b) | EQ001-EQ003 | paper parameters, declared finite scans | physically_consistent | `T001_main_fig1a_velocity.*` |
| T002 | Main 1(b), A-D | EQ001-EQ004 | paper alphas, reduced loop grid | physically_consistent | `T002_main_fig1b_wilson.*` |
| T003 | Main 2(b) | EQ006 | paper exact | reproduced | `T003_main_fig2b_tb4_bands.*` |
| T004 | Main 2(c) | EQ004, EQ006 | paper exact, finite loop grid | physically_consistent | `T004_main_fig2c_tb4_wilson.*` |
| T005 | Supp. 2(a) | EQ001-EQ003 | paper parameters, declared alpha grid | physically_consistent | `T005_supp_fig2a_levels.*` |
| T006 | Supp. 3(a-i) | EQ001-EQ003 | all paper alphas, reduced path grid | physically_consistent | `T006_supp_fig3_bands.*` |
| T007 | Supp. 4(a) | EQ001-EQ003 | paper interval, declared alpha grid | physically_consistent | `T007_supp_fig4a_gamma_levels.*` |
| T008 | Supp. 5(a-l) | EQ001-EQ003 | all paper alphas, reduced node grid | physically_consistent | `T008_supp_fig5_magic_generation.*` |
| T009 | Supp. 6, eight panels | EQ001, EQ002, EQ005 | paper `(t,t')`, reduced path/cutoff | physically_consistent | `T009_supp_fig6_ph_breaking.*` |
| T010 | Supp. 7(a-d) | EQ001-EQ004 | paper alphas, reduced loop grid | physically_consistent | `T010_supp_fig7_wilson.*` |
| T011 | Supp. 9(a-b) | EQ004, EQ006, EQ007 | paper exact, finite grids | physically_consistent | `T011_supp_fig9_tb8.*` |
| T012 | Supp. 10(b-c) | EQ006-EQ009 | paper exact Hamiltonians, finite Wannier grid | physically_consistent | `T012_supp_fig10_tb4_2v.*` |

These data files are frozen in `outputs/checks/generated_data_manifest.json`.

All `T001-T012` now also share the executable production contract
`implementations.paper_scale_theory`, backed by
`config/theory_paper_scale.json`, `src/tbg_topology/paper_scale.py`, and
`run_contract.theory_paper_scale.json`. The expensive run has not been started;
its future outputs are isolated under `outputs/{data,checks}/paper_scale_theory`
and cannot overwrite the attested feature data. The contract covers all twelve
targets, while the fourteen figure entries whose current evidence is reduced-scale
explicitly reference it. Code readiness does not promote any target to
`paper_exact` or lifecycle complete.

## Code-ready external DFT targets

All rows below share `implementations.paper_scale_dft` in `figure_coverage.json`, `config/dft_paper_scale.json`, and `dft_run_contract.json`. Their state is `deferred_blocked` only because no licensed VASP/PAW paper-scale run has been attested; their structure generation, input decks, runner, parsers, output mapping, and acceptance checks are implemented.

| Target | Paper item | Campaign job(s) | Expected output | State / external boundary |
| --- | --- | --- | --- | --- |
| D001 | Main Fig. 3(a), Gamma-level evolution | angle `i=6,10,16,23,27,30` | `outputs/data/dft_paper_scale/D001_gamma_levels.csv` | code ready; VASP/POTCAR/HPC not run |
| D002 | Main Fig. 3(b), K-gap vs angle | angle `i=6,10,16,23` | `outputs/data/dft_paper_scale/D002_angle_k_gaps.csv` | code ready; VASP/POTCAR/HPC not run |
| D003 | Supp. Fig. 11, `i=6` | `angle_i06`, 508 atoms | `outputs/data/dft_paper_scale/D003_supp_fig11_i06_bands.csv` | code ready; external run not attested |
| D004 | Supp. Fig. 11, `i=10` | `angle_i10`, 1324 atoms | `outputs/data/dft_paper_scale/D004_supp_fig11_i10_bands.csv` | code ready; external run not attested |
| D005 | Supp. Fig. 11, `i=16` | `angle_i16`, 3268 atoms | `outputs/data/dft_paper_scale/D005_supp_fig11_i16_bands.csv` | code ready; external run not attested |
| D006 | Supp. Fig. 11, `i=23` | `angle_i23`, 6628 atoms | `outputs/data/dft_paper_scale/D006_supp_fig11_i23_bands.csv` | code ready; external run not attested |
| D007 | Supp. Fig. 12(a), `z/d0=1.00` | `distance_i10_z100` | `outputs/data/dft_paper_scale/D007_supp_fig12_z100_bands.csv` | code ready; external run not attested |
| D008 | Supp. Fig. 12(a), `z/d0=0.90` | `distance_i10_z090` | `outputs/data/dft_paper_scale/D008_supp_fig12_z090_bands.csv` | code ready; external run not attested |
| D009 | Supp. Fig. 12(a), `z/d0=0.86` | `distance_i10_z086` | `outputs/data/dft_paper_scale/D009_supp_fig12_z086_bands.csv` | code ready; external run not attested |
| D010 | Supp. Fig. 12(a), `z/d0=0.83` | `distance_i10_z083` | `outputs/data/dft_paper_scale/D010_supp_fig12_z083_bands.csv` | code ready; external run not attested |
| D011 | Supp. Fig. 12(a), `z/d0=0.80` | `distance_i10_z080` | `outputs/data/dft_paper_scale/D011_supp_fig12_z080_bands.csv` | code ready; external run not attested |
| D012 | Supp. Fig. 12(b), K-gap vs distance | all five distance jobs | `outputs/data/dft_paper_scale/D012_distance_k_gaps.csv` | code ready; external run not attested |

The five Supplement Fig. 12(a) values are exactly `1.00, 0.90, 0.86, 0.83, 0.80`. No source curve, source pixel, author code, or author numerical array enters the campaign at runtime.
