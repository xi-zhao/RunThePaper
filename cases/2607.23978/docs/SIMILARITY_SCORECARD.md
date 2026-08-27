# Similarity Scorecard

## Primary score

- Harness similarity score: **86.92/100**
- Comparable-target masked theory-region mean before evidence caps: **87.16/100**
- Harness similarity enum: `numerical_feature_reproduction`
- Scientific gate: **4/4 passed**

The score is the measured pixel difference inside predeclared theory-curve
regions, not a subjective science score. Each target's 50/35/15 components are
fixed allocations of the same masked pixel value, so physics reasoning cannot
inflate the raster result. Physics assertions remain mandatory gates.

| Target | Theory-region score | Render band | Science status | Note |
| --- | ---: | --- | --- | --- |
| T001 Fig. 2(c-d) | 90.11 | high fidelity | passed | experimental points excluded by frozen mask |
| T002 Fig. 2(e-f) optimal | — | — | passed | no like-for-like raster crop |
| T003 Fig. 3(a) | 81.75 | accepted | passed | experiment excluded; printed-order issue isolated |
| T004 Fig. 3(b-c) | 89.62 | accepted | passed | target capped at 89 by unpublished finite `Delta gamma` |

## Interpretation

The legacy full-crop scores are background-dominated, while the legacy
foreground scores punish the theory reproduction for omitting experimental
symbols. Neither is the primary scientific render metric. Each binary mask is
rendered from the frozen independent numerical arrays, hashed in
`pixel_evidence.json`, and applied only after the isolated run. It does not read
paper pixels or change the generated data.

The machine-readable record is `outputs/checks/similarity_scorecard.json`, and raw metrics are in `outputs/checks/pixel_evidence.json`.
