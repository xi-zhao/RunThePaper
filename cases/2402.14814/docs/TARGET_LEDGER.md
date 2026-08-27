# Target ledger

| ID | Paper item | Scientific object | Formula | Parameter match | Status | Data | Figure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2(a) | rotating HO levels | EQ001 | paper_exact | algorithmically_consistent | `outputs/data/T001_T008_rotating_levels.csv` | `outputs/figures/T001_main_fig2a_levels.png` |
| T002 | Main Fig. 2(d), theory | ideal Rabi occupation | EQ004 | paper_exact | algorithmically_consistent | `outputs/data/T002_main_fig2d_rabi.csv` | `outputs/figures/T002_main_fig2d_rabi.png` |
| T003 | Main Fig. 3(a), theory counterpart | single-particle marginals | EQ002, EQ003 | paper_subset | algorithmically_consistent | `outputs/data/T003_T004_main_fig3_theory_densities.npz` | `outputs/figures/T003_main_fig3a_theory.png` |
| T004 | Main Fig. 3(b), theory counterpart | COM/relative densities | EQ002, EQ003 | paper_subset | algorithmically_consistent | `outputs/data/T003_T004_main_fig3_theory_densities.npz` | `outputs/figures/T004_main_fig3b_theory.png` |
| T005 | Main Fig. 4(a), solid line | one-particle radial density | EQ002, EQ003 | paper_exact | algorithmically_consistent | `outputs/data/T005_main_fig4a_radial.csv` | `outputs/figures/T005_main_fig4a_radial.png` |
| T006 | Main Fig. 4(b), solid lines | COM/relative radial densities | EQ002, EQ003 | paper_exact | algorithmically_consistent | `outputs/data/T006_main_fig4b_radial.csv` | `outputs/figures/T006_main_fig4b_radial.png` |
| T007 | Main Fig. 4(c), solid line | relative-angle correlation | EQ005 | paper_exact | algorithmically_consistent | `outputs/data/T007_main_fig4c_angle.csv` | `outputs/figures/T007_main_fig4c_angle.png` |
| T008 | Supp. Fig. S1 | rotating HO levels | EQ001 | paper_exact | algorithmically_consistent | `outputs/data/T001_T008_rotating_levels.csv` | `outputs/figures/T008_supp_figs1_levels.png` |
| T009 | Supp. Fig. S2(a) | harmonic contact spectrum | EQ006 | proxy_model | reconstructed_model | `outputs/data/T009_supp_figs2_harmonic.csv` | `outputs/figures/T009_supp_figs2_harmonic.png` |
| T010 | Supp. Fig. S2(b) | Gaussian-quartic spectrum | EQ006, EQ007 | proxy_model | reconstructed_model | `outputs/data/T010_supp_figs2_anharmonic.csv` | `outputs/figures/T010_supp_figs2_anharmonic.png` |
| T011 | Supp. Fig. S2(c), grayscale | driven rotating-frame spectrum | EQ008 | proxy_model | reconstructed_model | `outputs/data/T011_supp_figs2c_driven_spectrum.npz` | `outputs/figures/T011_supp_figs2c_driven_spectrum.png` |
| T012 | Supp. Fig. S3(c), fit | Laughlin Ramsey curve | EQ009 | paper_subset | algorithmically_consistent | `outputs/data/T012_supp_figs3_laughlin.csv` | `outputs/figures/T012_supp_figs3_laughlin.png` |
| T013 | Supp. Fig. S3(d), fit | noninteracting Ramsey curve | EQ009 | paper_subset | algorithmically_consistent | `outputs/data/T013_supp_figs3_noninteracting.csv` | `outputs/figures/T013_supp_figs3_noninteracting.png` |
| T014 | Supp. Fig. S3(e), fit | COM Ramsey curve | EQ009 | paper_subset | algorithmically_consistent | `outputs/data/T014_supp_figs3_center_of_mass.csv` | `outputs/figures/T014_supp_figs3_center_of_mass.png` |
| T015 | Supp. Fig. S3(f), theory counterpart | +/-2 density evolution | EQ009 | paper_subset | algorithmically_consistent | `outputs/data/T015_supp_figs3f_density_evolution.npz` | `outputs/figures/T015_supp_figs3f_density_evolution.png` |
| T016 | Supp. Fig. S4, horizontal line | uniform azimuthal density | EQ002 | paper_exact | algorithmically_consistent | `outputs/data/T016_supp_figs4_azimuthal.csv` | `outputs/figures/T016_supp_figs4_azimuthal.png` |
| T017 | Supp. Fig. S6(b), fits | spin-down imaging kernel | EQ010 | paper_exact | algorithmically_consistent | `outputs/data/T017_supp_figs6_spin_down.csv` | `outputs/figures/T017_supp_figs6_spin_down.png` |
| T018 | Supp. Fig. S6(c), fits | spin-up imaging kernel | EQ010 | paper_exact | algorithmically_consistent | `outputs/data/T018_supp_figs6_spin_up.csv` | `outputs/figures/T018_supp_figs6_spin_up.png` |

T009-T011 are deliberately not promoted to paper-exact: the paper does not
print the complete coupled-channel map, interaction-state basis truncation,
or the drive amplitude used for Supplement Fig. S2(c). The runnable code and
all disclosed assumptions are retained for review and future parameter repair.
