# Target Ledger

| Target | Paper item | Numerical panels | Formula cards | Parameter match | Scientific status | Data | Figure |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(b) plus inset | 2 | EQ001--EQ003 | `reduced_scale` | passed; crossing at 0.16 | `outputs/data/T001_main_fig1b_transition.npz` | `outputs/figures/T001_main_fig1b_transition.png` |
| T002 | Main Fig. 2(a) | 1 | EQ001, EQ002, EQ004 | `reduced_scale` | passed; 98.97% causal weight | `outputs/data/T002_main_fig2a_lightcone.npz` | `outputs/figures/T002_main_fig2a_lightcone.png` |
| T003 | Main Fig. 2(b) | 1 | EQ001, EQ002, EQ008 | `reduced_scale` | passed in clean attested v4; exact partial-record channel and paired data-processing order | `outputs/data/T003_main_fig2b_cutoff_decoder.npz` | `outputs/figures/T003_main_fig2b_cutoff_decoder.png` |
| T004 | Main Fig. 3(a) | 1 | EQ001, EQ003, EQ005 | `reduced_scale` | passed; beta_s=0.551 | `outputs/data/T004_main_fig3a_surface_order.npz` | `outputs/figures/T004_main_fig3a_surface_order.png` |
| T005 | Main Fig. 3(b) | 1 | EQ002, EQ006 | `reduced_scale` | passed; two nonnegative branches | `outputs/data/T005_main_fig3b_cylinder.npz` | `outputs/figures/T005_main_fig3b_cylinder.png` |
| T006 | Main Fig. 3(c) | 1 | EQ002, EQ006 | `reduced_scale` | passed; two nonnegative branches | `outputs/data/T006_main_fig3c_strip.npz` | `outputs/figures/T006_main_fig3c_strip.png` |
| T007 | Supplement Fig. S1(a,b) | 2 | EQ001, EQ002, EQ004 | `reduced_scale` | passed; both light cones nonzero | `outputs/data/T007_supp_figS1_lightcones.npz` | `outputs/figures/T007_supp_figS1_lightcones.png` |
| T008 | Supplement Fig. S2(a,b) | 2 | EQ001, EQ002, EQ007 | `reduced_scale` | passed; both purification curves decay | `outputs/data/T008_supp_figS2_purification.npz` | `outputs/figures/T008_supp_figS2_purification.png` |

The current corrected reduced artifacts are attested by isolated run `1910.00020-independent-v5-20260825`; its eight NPZ hashes exactly reproduce the accepted v4 data, all five declared inputs were read, and no forbidden path was accessed. Retained `v1`--`v4` runs are historical evidence of the repaired T003 channel, sampling-design defects, and evidence-chain repair and do not supersede v5 as the current attestation. None of the reduced artifacts is `paper_exact`: the paper omits sampling metadata and reaches L=512, while the reduced campaign uses L<=48. All targets also have a paper-scale implementation contract; code readiness does not imply the final campaign ran.
