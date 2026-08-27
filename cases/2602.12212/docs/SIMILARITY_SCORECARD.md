# Similarity Scorecard

## Case Score

- Overall score: `72.05/100`
- Similarity level: `numerical_feature_reproduction`
- Machine status: `passed`
- Final-reproduction gate: 10 eligible targets

## Figure Scores

| Target | Weight | Raw component total | Applied cap | Final score |
| --- | ---: | ---: | --- | ---: |
| T001 Main Fig. 1 | 1.0 | 98 | analytic reference: 90 | 90 |
| T002 Main Fig. 2 left | 2.0 | 88 | source figure only: 70 | 70 |
| T003 Main Fig. 2 right | 2.0 | 88 | source figure only: 70 | 70 |
| T004 Fig. S1 | 0.75 | 85 | source figure only: 70 | 70 |
| T005 Fig. S2 | 0.75 | 85 | source figure only: 70 | 70 |
| T006 Fig. S3 | 0.75 | 84 | source figure only: 70 | 70 |
| T007 Fig. S4 | 0.75 | 85 | source figure only: 70 | 70 |
| T008A Fig. S5 row 1 | 0.5 | 88 | source figure only: 70 | 70 |
| T008B Fig. S5 row 2 | 0.5 | 88 | source figure only: 70 | 70 |
| T009 Fig. S6 | 0.75 | 93 | source figure only: 70 | 70 |

## Evaluation Metadata

| Property | Result |
| --- | --- |
| Scored targets | 10 |
| Critical targets | 3 |
| Artifact pass rate | 1.0 |
| Data-backed rate | 1.0 |
| Formula gates | 10 verified |
| Parameter match | 10 paper exact |
| Generated provenance | 9 independent numerics, 1 analytic reference |
| Reference comparison | 9 source figure only, 1 analytic reference |

## Interpretation

The physical feature evidence is strong and complete in scope. The harness
does not allow a source PNG/PDF alone to support a score above 70 for a
curve-level claim. Consequently, the case remains in the feature-reproduction
band even though all published sizes and panels were generated.

## What Prevents A Higher Score

- No author code, arrays, or tables.
- No digitized source curves with a registered coordinate transform.
- Boundary, shell-edge, and confidence-interval conventions are omitted from
  the paper, although the chosen reconstructions match the source features.

## Machine-Readable Record

`outputs/checks/similarity_scorecard.json`
