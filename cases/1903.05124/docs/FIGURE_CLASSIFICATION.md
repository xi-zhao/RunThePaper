# Figure Classification

Only independently generable theory-numerical figures, panels, or visible
series become executable targets. Experimental measurements/images,
schematics, context, and tables are inventoried but never generated.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). Split mixed figures into panels and mixed panels into
`figure_series` items. Only ids frozen in
`physics_reproduction_project.json` under
`reproduction_scope.target_item_ids` may be targeted. Skipping a selected
theory-numerical item because it is "supporting" or "similar" is
not allowed. A selected target is regenerated from a verified formula/method;
source-image pixels are reference-only.

| Paper item | Parent item | Item type | Scientific role | Selected? | Decision | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| `MAIN_FIG1` | — | figure | schematic_context | no | excluded | Bell-pair and partition drawing contains no plotted observable; its decoupling claim is derived in EQC001–EQC002. |
| `MAIN_FIG2_A` | `MAIN_FIG2` | figure_panel | schematic_context | no | excluded | Circuit-layout drawing defines MTH001 but is not a numerical result. |
| `MAIN_FIG2_B` | `MAIN_FIG2` | figure_panel | theory_numerical | yes | target → T001 | Half-chain entropy density versus time from independent stabilizer dynamics. |
| `MAIN_FIG2_C` | `MAIN_FIG2` | figure_panel | theory_numerical | yes | target → T001 | Measurement-induced entropy change from the same trajectories. |
| `MAIN_FIG2_D` | `MAIN_FIG2` | figure_panel | theory_numerical | yes | target → T001 | Steady-state entropy density versus measurement fraction for three `(d,m)` settings. |
| `MAIN_FIG2_E` | `MAIN_FIG2` | figure_panel | theory_numerical | yes | target → T001 | Entropy-density heatmap and independently fitted transition markers. |
| `SUPP_FIG_S1_A` | `SUPP_FIG_S1` | figure_panel | schematic_context | no | excluded | Brick-circuit composition drawing; it defines the sampled ensemble. |
| `SUPP_FIG_S1_B` | `SUPP_FIG_S1` | figure_panel | schematic_context | no | excluded | Binary matrix layout drawing; its algebra is reproduced in EQC004/MTH002. |
| `SUPP_FIG_S2_A` | `SUPP_FIG_S2` | figure_panel | theory_numerical | yes | target → T002 | First frame potential versus circuit depth. |
| `SUPP_FIG_S2_B` | `SUPP_FIG_S2` | figure_panel | theory_numerical | yes | target → T002 | Second frame potential versus circuit depth. |
| `SUPP_FIG_S2_C` | `SUPP_FIG_S2` | figure_panel | theory_numerical | yes | target → T002 | Third frame potential versus circuit depth. |
| `SUPP_FIG_S2_D` | `SUPP_FIG_S2` | figure_panel | theory_numerical | yes | target → T002 | Fourth frame potential versus circuit depth. |
| `SUPP_FIG_S3_A_ENTROPY` | `SUPP_FIG_S3_A` | figure_panel | theory_numerical | yes | target → T003 | Entropy growth at `d=3,p=0.1`. |
| `SUPP_FIG_S3_A_MEAS` | `SUPP_FIG_S3_A` | figure_panel | theory_numerical | yes | target → T003 | Measurement entropy change at `d=3,p=0.1`. |
| `SUPP_FIG_S3_B_ENTROPY` | `SUPP_FIG_S3_B` | figure_panel | theory_numerical | yes | target → T003 | Entropy growth at `d=3,p=0.2`. |
| `SUPP_FIG_S3_B_MEAS` | `SUPP_FIG_S3_B` | figure_panel | theory_numerical | yes | target → T003 | Measurement entropy change at `d=3,p=0.2`. |
| `SUPP_FIG_S3_C_ENTROPY` | `SUPP_FIG_S3_C` | figure_panel | theory_numerical | yes | target → T003 | Entropy growth at `d=3,p=0.3`. |
| `SUPP_FIG_S3_C_MEAS` | `SUPP_FIG_S3_C` | figure_panel | theory_numerical | yes | target → T003 | Measurement entropy change at `d=3,p=0.3`. |
| `SUPP_FIG_S3_D_ENTROPY` | `SUPP_FIG_S3_D` | figure_panel | theory_numerical | yes | target → T003 | Entropy growth at `d=3,p=0.4`. |
| `SUPP_FIG_S3_D_MEAS` | `SUPP_FIG_S3_D` | figure_panel | theory_numerical | yes | target → T003 | Measurement entropy change at `d=3,p=0.4`. |
| `SUPP_FIG_S3_E_ENTROPY` | `SUPP_FIG_S3_E` | figure_panel | theory_numerical | yes | target → T003 | Entropy growth at `d=44,p=0.2`. |
| `SUPP_FIG_S3_E_MEAS` | `SUPP_FIG_S3_E` | figure_panel | theory_numerical | yes | target → T003 | Measurement entropy change at `d=44,p=0.2`. |
| `SUPP_FIG_S3_F_ENTROPY` | `SUPP_FIG_S3_F` | figure_panel | theory_numerical | yes | target → T003 | Entropy growth at `d=44,p=0.4`. |
| `SUPP_FIG_S3_F_MEAS` | `SUPP_FIG_S3_F` | figure_panel | theory_numerical | yes | target → T003 | Measurement entropy change at `d=44,p=0.4`. |
| `SUPP_FIG_S3_G_ENTROPY` | `SUPP_FIG_S3_G` | figure_panel | theory_numerical | yes | target → T003 | Entropy growth at `d=44,p=0.6`. |
| `SUPP_FIG_S3_G_MEAS` | `SUPP_FIG_S3_G` | figure_panel | theory_numerical | yes | target → T003 | Measurement entropy change at `d=44,p=0.6`. |
| `SUPP_FIG_S3_H_ENTROPY` | `SUPP_FIG_S3_H` | figure_panel | theory_numerical | yes | target → T003 | Entropy growth at `d=44,p=0.8`. |
| `SUPP_FIG_S3_H_MEAS` | `SUPP_FIG_S3_H` | figure_panel | theory_numerical | yes | target → T003 | Measurement entropy change at `d=44,p=0.8`. |
| `SUPP_FIG_S4_A` | `SUPP_FIG_S4` | figure_panel | theory_numerical | yes | target → T004 | Entanglement density versus size for `d=1`. |
| `SUPP_FIG_S4_B` | `SUPP_FIG_S4` | figure_panel | theory_numerical | yes | target → T004 | Entanglement density versus size for `d=7`. |
| `SUPP_FIG_S4_C` | `SUPP_FIG_S4` | figure_panel | theory_numerical | yes | target → T004 | Entanglement density versus size for `d=31`. |
| `SUPP_FIG_S4_D` | `SUPP_FIG_S4` | figure_panel | theory_numerical | yes | target → T004 | Entanglement density versus `p` for `d=1`. |
| `SUPP_FIG_S4_D_INSET` | `SUPP_FIG_S4_D` | figure_panel | theory_numerical | yes | target → T004 | Independently fitted collapse inset for `d=1`. |
| `SUPP_FIG_S4_E` | `SUPP_FIG_S4` | figure_panel | theory_numerical | yes | target → T004 | Entanglement density versus `p` for `d=7`. |
| `SUPP_FIG_S4_E_INSET` | `SUPP_FIG_S4_E` | figure_panel | theory_numerical | yes | target → T004 | Independently fitted collapse inset for `d=7`. |
| `SUPP_FIG_S4_F` | `SUPP_FIG_S4` | figure_panel | theory_numerical | yes | target → T004 | Entanglement density versus `p` for `d=31`. |
| `SUPP_FIG_S4_F_INSET` | `SUPP_FIG_S4_F` | figure_panel | theory_numerical | yes | target → T004 | Independently fitted collapse inset for `d=31`. |
| `SUPP_FIG_S4_G` | `SUPP_FIG_S4` | figure_panel | theory_numerical | yes | target → T004 | Half-chain-collapse critical exponent versus depth. |
| `SUPP_FIG_S5_A` | `SUPP_FIG_S5` | figure_panel | theory_numerical | yes | target → T005 | Tripartite mutual information versus `p` for `d=1`. |
| `SUPP_FIG_S5_B` | `SUPP_FIG_S5` | figure_panel | theory_numerical | yes | target → T005 | Tripartite mutual information versus `p` for `d=7`. |
| `SUPP_FIG_S5_C` | `SUPP_FIG_S5` | figure_panel | theory_numerical | yes | target → T005 | Tripartite mutual information versus `p` for `d=31`. |
| `SUPP_FIG_S5_D` | `SUPP_FIG_S5` | figure_panel | theory_numerical | yes | target → T005 | `I3` collapse for `d=1`. |
| `SUPP_FIG_S5_E` | `SUPP_FIG_S5` | figure_panel | theory_numerical | yes | target → T005 | `I3` collapse for `d=7`. |
| `SUPP_FIG_S5_F` | `SUPP_FIG_S5` | figure_panel | theory_numerical | yes | target → T005 | `I3` collapse for `d=31`. |
| `SUPP_FIG_S5_G` | `SUPP_FIG_S5` | figure_panel | theory_numerical | yes | target → T005 | `I3` critical exponent versus depth. |
| `SUPP_TABLE_SI` | — | table | context | no | excluded | Numerical fit values are acceptance checks for T005; case policy excludes table rendering. |
| `SUPP_FIG_S6_A` | `SUPP_FIG_S6` | figure_panel | theory_numerical | yes | target → T006 | Critical measurement fraction versus block size. |
| `SUPP_FIG_S6_B` | `SUPP_FIG_S6` | figure_panel | theory_numerical | yes | target → T006 | Critical exponent versus block size. |
| `SUPP_FIG_S6_C` | `SUPP_FIG_S6` | figure_panel | theory_numerical | yes | target → T006 | Logarithmic critical-entropy coefficient versus block size. |
| `SUPP_FIG_S7_A` | `SUPP_FIG_S7` | figure_panel | schematic_context | no | excluded | Measurement-channel input/output drawing contains no numerical observable. |
| `SUPP_FIG_S7_B` | `SUPP_FIG_S7` | figure_panel | schematic_context | no | excluded | Unitary dilation/dephasing drawing supports EQC009. |
| `SUPP_FIG_S8_A` | `SUPP_FIG_S8` | figure_panel | schematic_context | no | excluded | Toy-model tensor layout supports EQC002. |
| `SUPP_FIG_S8_B` | `SUPP_FIG_S8` | figure_panel | schematic_context | no | excluded | Swap-contraction diagram supports EQC002. |
| `SUPP_FIG_S8_C` | `SUPP_FIG_S8` | figure_panel | schematic_context | no | excluded | Swap-contraction diagram supports EQC002. |
| `SUPP_FIG_S9` | — | figure | schematic_context | no | excluded | Weingarten contraction network is an analytic diagram, not plotted data. |

Allowed classes:

- `theory_numerical`
- `experimental_measurement`
- `experimental_image`
- `schematic_context`
- `context`
