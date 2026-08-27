# Similarity Scorecard

| Target | Status | Score | Scientific interpretation |
| --- | --- | ---: | --- |
| `F5A_PROXY` | exploratory proxy | 45 | public channel/direction pass; different circuit model prevents paper parity |
| `T_TABLE3` | paper-exact | 100 | every printed numeric entry independently reproduced |
| `T_FIG10` | paper-exact | 100 | all 25 matrix entries within `1e-4` |
| `T_FIG5B` | uncovered | 0 | leakage-aware QEC implementation missing |
| `T_FIG6A` | uncovered | 0 | distance-three transmon scan missing |
| `T_FIG6B` | uncovered | 0 | distance-nine scan and convergence missing |
| `T_FIG7` | uncovered | 0 | finite-size threshold pipeline missing |
| `T_FIG8` | uncovered | 0 | neutral-atom threshold surface missing |
| `T_FIG11` | uncovered | 0 | non-stationary sector-history QEC fit missing |

## Case Score

- Overall: **81.67/100**
- Level: `numerical_feature_reproduction`
- Science checks: 3/3 targets passed for their declared model and scope
- Whole-paper inventory: 9 eligible numerical items, 3 covered, 6 uncovered
- Coverage: **33.33%**
- Covered-item scientific fidelity: **82.35/100**
- Reproduction degree: **27.45/100** (`coverage × covered fidelity`)
- Lifecycle: not complete; six independent methods remain unimplemented and
  fresh-context review is missing

The historical 81.67 score remains the mean of the three implemented target
scores and is retained only for backward comparison. The public whole-paper
measure counts every uncovered item as zero, so 27.45 is the appropriate answer
to “how much of this paper has been reproduced?” The 45-point proxy is not
promoted by styling or pixel comparison; the two exact targets use direct
numeric/table comparisons, for which raster pixels are not a more meaningful
scientific metric.

The authoritative machine record is
`outputs/checks/similarity_scorecard.json`.
