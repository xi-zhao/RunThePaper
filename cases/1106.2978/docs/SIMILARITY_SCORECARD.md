# Similarity Scorecard

## Case score

- Harness score: `86.58/100`
- Similarity band: `numerical_feature_reproduction`
- Direct scientific-region pixel mean: `90.7604/100`
- Scientific status: 21/21 targets are paper-parameter, data-backed and isolated-run attested; 19 formula gates pass and two are explicitly blocked by stable source discrepancies.

The aggregate includes every body-level quantitative claim, rather than only the figure. T005 and T014 are capped at 55 by failed essential paper-claim assertions; this is a scientific gate, not a rendering penalty.

## Target scores

| Target | Feature | Numeric | Scope | Primary pixel | Harness score |
| --- | ---: | ---: | ---: | ---: | ---: |
| T001 Fig. 2(a) | 50/50 | 35/35 | 15/15 | 94.0463 | 90.00 |
| T002 Fig. 2(b) main | 50/50 | 35/35 | 15/15 | 88.4407 | 88.44 |
| T003 inset | 50/50 | 35/35 | 15/15 | 89.7941 | 89.79 |
| T004 easy-plane claim | 50/50 | 35/35 | 15/15 | N/A | 90.00 |
| T005 correlation claim | 35/50 | 20/35 | 7.5/15 | N/A | 55.00 |
| T006 weak-coupling claim | 50/50 | 35/35 | 15/15 | N/A | 90.00 |
| T007-T013 | 50/50 | 35/35 | 15/15 | N/A | 90.00 each |
| T014 root cutoff index/parity/dimension | 35/50 | 20/35 | 7.5/15 | N/A | 55.00 |
| T015-T019 | 50/50 | 35/35 | 15/15 | N/A | 90.00 each |
| T020 easy-plane spectral convergence | 50/50 | 35/35 | 15/15 | N/A | 90.00 |
| T021 infinite transfer rank | 50/50 | 35/35 | 15/15 | N/A | 90.00 |

All targets use `analytic_reference`, so the general evidence model caps them at 90 even when the formula and independent implementation agree more closely. The whole-canvas score `94.6497` is layout-only and is not substituted for panel-level scientific scores.

## Remaining lifecycle gap

Fresh-context independent scientific review of the repaired whole-paper package is still missing. Machine-readable evidence is in `outputs/checks/similarity_scorecard.json`.
