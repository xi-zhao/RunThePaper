# Similarity Scorecard

## Metric policy

- Primary metric: point-wise foreground RGB similarity in predeclared scientific regions.
- Mean primary score: `69.4855/100`.
- Full-canvas diagnostic: `79.2010/100`.
- Reference figures are used only after numerical freeze and carry the source-figure score cap.

| Target | Scientific-region score | Full-canvas diagnostic | Formula/science gate | Parameter status |
| --- | ---: | ---: | --- | --- |
| T001 | 79.4314 | 88.4702 | passed | paper-exact |
| T002 | 64.2386 | 71.4203 | passed | reconstructed metadata |
| T003 | 77.7280 | 79.5228 | passed | reconstructed metadata |
| T004 | 56.5441 | 77.3909 | passed | reduced scale |
| T005 | not comparable | not applicable | passed with source-discrepancy candidate | analytic reference; score 90 |

T004's lower foreground score mainly reflects a different independently trained decision field and noisy minibatch loss path. T002--T004 cannot be upgraded by matching source pixels; only the missing scientific parameter contract could remove the current cap.

The pixel table is not the coverage denominator. The whole-paper inventory has
15 eligible reproduction items: all 14 displayed numerical items and the
independent universal-separability claim T005 are covered. T005 contributes
scientific fidelity through analytic/rank evidence and has no pixel score by
construction. Fresh review controls its evidence grade and paper-error status.

Machine-readable record: `outputs/checks/similarity_scorecard.json`.
