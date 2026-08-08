# Similarity Scorecard

## Case Score

- Overall score: `72.0/100`
- Similarity level: `numerical_feature_reproduction`
- Reason: Figure 8 passes at full scale, while Figure 9's central threshold
  classification is independently computed but not reproduced.

## Figure Scores

| Target | Weight | Feature | Numeric | Scope | Raw | Capped score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T008 / Figure 8 | 1.0 | 50/50 | 30/35 | 15/15 | 95 | 89 |
| T009 / Figure 9 | 1.0 | 40/50 | 18/35 | 15/15 | 73 | 55 |

T008 is capped at 89 because the benchmark scale and search-step budget match,
but the optimizer implementation and seed ensemble do not exactly match the
paper. T009 is capped at 55 because the essential `5e-4` threshold assertion
fails on nine additional circuits.

## Numerical Axes

- Figure 8: overhead Pearson correlation `0.9881`, MAE `0.0600`, law residual
  `4.44e-16`.
- Figure 9: overhead-series correlations `0.9857–0.9905`; gap correlation
  `0.3359`; threshold agreement `58/67`.
- All generated data have `independent_numerics` provenance.

The machine-readable scorecard is
`outputs/checks/similarity_scorecard.json`.
