# Target Ledger

| Target | Paper item | Formula dependencies | Status | Frozen data | Rendered figure | Boundary |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(c), modes | EQC009 | partial | `mode_profiles.npz` | `T001_mode_profiles.png` | proxy scalar mode |
| T002 | Main Fig. 2, transfer | EQC002, EQC005 | physically_consistent | `mzi_transfer.csv` | `T002_mzi_transfer.png` | measured points missing |
| T003 | Main Fig. 3(b), `|11>` surface | EQC001–003 | physically_consistent | `quantum_surfaces.npz` | `T003_probability_surface_11.png` | measured points missing |
| T004 | Main Fig. 3(c), `|11>` cuts | EQC001–003 | physically_consistent | `quantum_cuts.csv` | `T004_phase_cuts_11.png` | measured points missing |
| T005 | Main Fig. 3(d), `|20>` surface | EQC001–003 | physically_consistent | `quantum_surfaces.npz` | `T005_probability_surface_20.png` | measured points missing |
| T006 | Main Fig. 3(e), `|20>` cuts | EQC001–003 | physically_consistent | `quantum_cuts.csv` | `T006_phase_cuts_20.png` | measured points missing |
| T007 | Main Fig. 3(f), `|02>` surface | EQC001–003 | physically_consistent | `quantum_surfaces.npz` | `T007_probability_surface_02.png` | measured points missing |
| T008 | Main Fig. 3(g), `|02>` cuts | EQC001–003 | physically_consistent | `quantum_cuts.csv` | `T008_phase_cuts_02.png` | measured points missing |
| T009 | Main Fig. 4(b), HOM | EQC006–007 | partial | `hom_curve.csv` | `T009_hom_delay_model.png` | paper subset |
| T010 | Supplement Fig. S1, bunched | EQC001, EQC003 | physically_consistent | `imperfection_scans.csv` | `T010_balance_bunched_probability.png` | theory complete |
| T011 | Supplement Fig. S1, split | EQC001, EQC003 | physically_consistent | `imperfection_scans.csv` | `T011_balance_split_probability.png` | theory complete |
| T012 | Supplement Fig. S2, bunched | EQC003–004 | physically_consistent | `imperfection_scans.csv` | `T012_purity_bunched_probability.png` | theory complete |
| T013 | Supplement Fig. S2, split | EQC003–004 | physically_consistent | `imperfection_scans.csv` | `T013_purity_split_probability.png` | theory complete |
| T014 | Supplement Fig. S5(b), spectral HOM | EQC006 | partial | `spectral_visibility.csv` | `T014_spectral_hom_visibility.png` | proxy spectrum |
| T015 | Supplement Fig. S6, coupler loss | printed trend | physically_consistent | `coupler_loss.csv` | `T015_coupler_loss.png` | measured points missing |
| T016 | Supplement Fig. S7, electrode loss | EQC009 | partial | `electrode_loss.csv` | `T016_electrode_overlap_loss.png` | proxy overlap model |
| T017 | brightness arithmetic | EQC008 | partial | `claim_arithmetic.json` | `T017_brightness_arithmetic.png` | rounded scalar subset |
| T018 | bandwidth conventions | EQC007–008 | partial | `claim_arithmetic.json` | `T018_bandwidth_conventions.png` | convention unresolved |

All data paths are under `outputs/data/feature/`, all figure paths under `outputs/figures/feature/`, and every target also has a post-freeze comparison under `comparison-artifacts/`. The authoritative machine contract remains `physics_reproduction_project.json`.
