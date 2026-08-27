# Similarity Scorecard

## Case Score

- Overall scientific score: `93.75 / 100`
- Similarity level: `complete_reproduction`
- Scorecard status: `passed`
- Final-reproduction readiness: `true`
- Pixel-fidelity score: `60.88 / 100` in a separate lane

## Target Scores

| Target | Role | Weight | Feature | Numeric | Scope | Evidence cap | Final score |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `T_FIG2` | main claim | 3 | 50 | 35 | 15 | 90, analytic reference | 90 |
| `T_TABLE1` | supporting | 1 | 50 | 35 | 15 | 100, exact table | 100 |
| `T_TABLE2` | main claim | 2 | 50 | 35 | 15 | 100, exact table | 100 |
| `T_FIGA` | method validation | 2 | 50 | 35 | 15 | 90, analytic reference | 90 |

Weighted score:

```text
(3*90 + 1*100 + 2*100 + 2*90) / 8 = 93.75
```

## Scientific Contracts

- `10 / 10` physics assertions pass.
- `4 / 4` targets use paper-exact parameters.
- `4 / 4` final figures are backed by generated data.
- `4 / 4` formula gates are verified at target level.
- `0` manual interventions are attributed to scored items.
- `0` failure types are open.

## Pixel Lane

| Pixel target | Contract | Pixel score | Axis-box IoU | Density ratio |
| --- | --- | ---: | ---: | ---: |
| `PXT_FIG2` | passed | 57.26 | 0.899944 | 0.565140 |
| `PXT_TABLE1` | passed | 57.94 | 0.763599 | 0.741312 |
| `PXT_TABLE2` | passed | 68.28 | 0.959537 | 0.920304 |
| `PXT_FIGA` | passed | 60.02 | 0.876072 | 0.786868 |

Pixel results measure presentation fidelity only. They do not add scientific
points. The normalized machine-readable scorecard is
`outputs/checks/similarity_scorecard.json`.
