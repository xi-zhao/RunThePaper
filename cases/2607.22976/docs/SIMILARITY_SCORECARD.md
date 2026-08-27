# Similarity Scorecard

## Primary score

- Foreground-pixel mean: **69.28/100**
- Similarity level: `numerical_feature_reproduction`
- Scientific gates: **5/5 passed**

The headline is the literal grayscale difference over the union of source/generated foreground pixels. Whole-crop scores are secondary because white background raises them. The 50/35/15 scorecard components are fixed allocations of each measured pixel score; qualitative reasoning cannot inflate it.

| Target | Foreground score | Full-crop score | Science status |
| --- | ---: | ---: | --- |
| T001 Fig. 2 | 67.15 | 92.35 | passed |
| T002 Fig. 3 | 72.28 | 90.93 | passed |
| T003 Fig. 4 | 84.80 | 94.15 | passed |
| T004 Fig. S1 | 65.25 | 92.54 | passed |
| T005 Fig. S2(b-c) | 56.93 | 94.10 | passed |

T005 illustrates why physics and pixels are separate gates: its open-cut spectrum passes the quantitative distance contract, while exact marker/layout placement remains below the raster feature threshold.

Machine-readable evidence: `outputs/checks/similarity_scorecard.json` and `outputs/checks/pixel_evidence.json`.
