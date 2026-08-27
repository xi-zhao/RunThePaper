# Similarity Scorecard

## Public reproduction measure

The whole-paper metric is evaluated over 76 atomic reproduction items. Existing
reduced-scale artifacts cover 58 items; 18 uncovered items receive zero rather
than disappearing from the denominator.

| Quantity | Value |
| --- | ---: |
| Eligible reproduction items | 76 |
| Covered items | 58 |
| Uncovered items | 18 |
| Coverage | 76.32% |
| Covered-item fidelity | 63.59/100 |
| Reproduction degree | 48.53/100 |
| Evidence grade | E2 |
| Paper-exact executions | 0 |

These W1 snapshot values are derived by `project inspect`. The historical
T001-T009 target scores remain unchanged. T010-T016 are explicit zero-coverage
bookkeeping targets and are excluded from the legacy target-score aggregate,
preventing the migration from rewriting old evidence. The live authoritative
values must always be queried through `project inspect` after later repairs.

Pixel similarity remains a secondary rendering diagnostic and is not part of
the scientific reproduction degree.
