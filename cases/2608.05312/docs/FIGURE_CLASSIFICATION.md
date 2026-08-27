# Figure and Table Classification

The frozen main text and supplement contain **74 atomic displayed items**:
72 eligible scientific numerical items and two non-numerical schematics. Existing
independent evidence covers 68/72 eligible items. The four uncovered items are
listed explicitly below; no grouped figure is allowed to hide them.

| Paper item | Atomic items | Eligible | Covered | Reproduction decision |
| --- | ---: | ---: | ---: | --- |
| Fig. 1(a,b) | 2 | 0 | 0 | excluded schematics |
| Fig. 1(c) | 4 | 4 | 4 | target T001 |
| Fig. 2(a-d) | 20 | 20 | 20 | targets T002-T003 |
| Fig. 3(a-c) | 8 | 8 | 8 | target T004 |
| Fig. S1(a,b) | 7 | 7 | 7 | targets T005 and T012 |
| Table S1 | 7 | 7 | 7 | target T006 |
| Table S2 | 4 | 4 | 4 | target T007 |
| Fig. S2(a,b) | 7 | 7 | 7 | target T008 |
| Fig. S3(a,b) | 8 | 8 | 8 | target T009 |
| Fig. S4 | 3 | 3 | 3 | targets T010 and T004 |
| Fig. S5(a,b) | 4 | 4 | 0 | target T011, source-blocked |
| **Total** | **74** | **72** | **68** | **94.44% coverage** |

## Explicit uncovered items

| Item ID | Paper location | Direct cause | Root cause | Code status | Next discriminating action |
| --- | --- | --- | --- | --- | --- |
| `supp_figs5a_phenomenological_time_trace` | Fig. S5(a) | Required QCLE benchmark parameters are absent | publication underspecified | not applicable before the calculation is defined | Acquire a citable parameter card, then implement independently |
| `supp_figs5a_qcle_time_trace` | Fig. S5(a) | same missing benchmark inputs | publication underspecified | not applicable before the calculation is defined | same |
| `supp_figs5b_phenomenological_coupling_curve` | Fig. S5(b) | same missing benchmark inputs | publication underspecified | not applicable before the calculation is defined | same |
| `supp_figs5b_qcle_coupling_curve` | Fig. S5(b) | same missing benchmark inputs | publication underspecified | not applicable before the calculation is defined | same |

The source figure raster is allowed for inventory and layout diagnosis only. It
is not digitized, and author numerical implementation or arrays are not used as
scientific inputs.

The source bundle's filenames are historically offset (`figS3_scaling...` is
paper Fig. S2, `figS2_eigenstate...` is paper Fig. S3, and
`figS5_temperature...` is paper Fig. S4). Paper numbering, not filenames, is
used in the target IDs.
