# Target Ledger

This is the author-side execution ledger. “Ready for fresh review” means the repaired checks passed, not that the prior independent disposition has been overwritten.

| Target | Eligible atomic items | Author-side scientific checks | Review state |
| --- | ---: | --- | --- |
| T001 Fig. 2g-h theory distributions | 2 | normalized distributions; PR/entropy regime separation | prior evidence retained |
| T002 Fig. 3 PT, entropy, SFF | 3 | `2000` realizations; finite triplet; extrema near `t*=1.79`; grid and late-domain convergence | ready for fresh review |
| T003 Fig. 4 OTOC and PR | 6 | `2000` realizations; conditional-normalized finite OTOCs; chaotic/integrable PR separation; time domain through `1000` | ready for fresh review |
| T004 Fig. S1 conditional PT | 1 | `D=28` analytic/PT distance tests | prior evidence retained |
| T005 Fig. S4 scaling | 3 | exact even `M=4,6,…,22`; `M=22` retained; `2000` chaotic realizations per mode; three scaling trends | ready for fresh review |
| T006 Fig. S5 ideal OTOCs | 2 | `2000` realizations; all `28` configurations including initial `(3,4)`; per-time sums equal one; all sectors | ready for fresh review |
| T007 Fig. S6 short time and FFT | 3 | shared conditional normalization; `t^2/t^4`; all non-initial FFT comparisons favor chaotic delocalization | ready for fresh review where affected |

Experimental measurements embedded in Fig. 2–4 are separately inventoried with `scientific_role=experimental_measurement` and excluded from the theory denominator.

Target evidence lives under `outputs/data/scientific_closure/` and `outputs/checks/scientific_closure/`. Execution identity is frozen in `outputs/runs/2605.25398-scientific-closure-v2-20260825/`. The historical v1 run and historical review remain immutable evidence rather than inputs to the new reviewer.
