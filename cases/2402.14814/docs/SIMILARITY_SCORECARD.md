# Similarity Scorecard

## Case Score

- Overall score: `83.83 / 100`
- Similarity level: `numerical_feature_reproduction`
- 18/18 theory targets are data-backed and pass 36/36 declared physics assertions.

## Scoring Model

Each target starts from feature match (50), numeric closeness (35), and theoretical-scope coverage (15). Evidence gates then cap the result: analytic paper-exact targets at 90 without a registered primary pixel metric, paper-subset targets at 89, and proxy models at 55. This prevents an attractive plot from hiding missing parameters or experimental data.

## Figure Scores

| Targets | Count | Parameter match | Per-target score | Contribution |
| --- | ---: | --- | ---: | ---: |
| T001,T002,T005-T008,T016-T018 | 9 | paper_exact | 90 | 810 |
| T003,T004,T012-T015 | 6 | paper_subset | 89 | 534 |
| T009-T011 | 3 | proxy_model | 55 | 165 |
| **Total / mean** | **18** | mixed |  | **83.83** |

## Pixel Interpretation

Every target has a post-freeze source-vs-generated board. The paper panels often mix experimental dots, camera samples, annotations, and theory; therefore whole-canvas pixel difference is not used as a scientific score. A primary pixel score requires a predeclared same-geometry crop containing only the scientific theory region. Source figures never enter the numerical runner.

## What Prevents A Higher Score

- Three Supplement S2 targets lack paper-specific calibration and remain proxy models.
- Six targets reproduce only the ideal/theoretical component of mixed experimental panels.
- No fresh-context independent review result exists.
- No same-geometry scientific-region pixel contract is registered for this case.

Machine-readable record: `outputs/checks/similarity_scorecard.json`.
