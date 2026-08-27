# Similarity Scorecard

## Result

- Primary raw metric: scientific-region foreground pixel similarity.
- Mean raw pixel score: **61.82/100** across T001-T011.
- Full-canvas mean: 89.07/100, layout diagnostic only.
- Harness score: 70.00/100, capped because the only external reference is the source figure rather than author arrays.
- Level: `numerical_feature_reproduction`.

| Target | Raw pixel primary | Full canvas diagnostic | Parameter status |
| --- | ---: | ---: | --- |
| T001 | 75.54 | 71.15 | paper exact |
| T002 | 49.45 | 91.10 | paper exact |
| T003 | 59.69 | 92.67 | reduced grid |
| T004 | 71.31 | 78.96 | paper exact |
| T005 | 62.63 | 91.77 | paper exact |
| T006 | 64.85 | 94.11 | reduced sweep |
| T007 | 91.89 | 92.58 | reduced sweep |
| T008 | 59.58 | 91.78 | paper exact |
| T009 | 48.70 | 93.90 | paper exact |
| T010 | 55.62 | 90.84 | paper exact |
| T011 | 40.77 | 90.87 | paper exact |

The score does not grant lifecycle completion: D001-D002 remain deferred and a fresh-context independent review is still pending. Source pixels never entered numerical generation; they were opened only after array hashes were frozen.

Machine records: `outputs/checks/similarity_scorecard.json`, the case-specific scientific-region metrics in `outputs/checks/scientific_pixel_metrics.json`, and the Harness-authoritative crop contract in `outputs/checks/pixel_evidence.json`.
