# Similarity Scorecard

- Overall score: **67.1/100**
- Level: `numerical_feature_reproduction`
- Scoring principle: numerical physics, not colors or plotting style

| Target | Weight | Raw scientific score | Applied cap | Final score |
| --- | ---: | ---: | --- | ---: |
| T001 small-\(q\) main/supplementary figures | 1.0 | 55.5 | source figure only; numerical protocol undisclosed | 55.5 |
| T002 exact trajectory and transition | 2.0 | 96 | source figure only; no author arrays | 70 |
| T003 local quantum geometry | 1.5 | 93 | source figure only; no author arrays | 70 |
| T004 interaction sweeps | 0.5 | 83 | source figure only; source mesh unknown | 70 |

The weighted score is
\[
\frac{1(55.5)+2(70)+1.5(70)+0.5(70)}{5}=67.1.
\]

The machine-readable calculation is
`outputs/checks/similarity_scorecard.json`. Its warnings note that linked
main/supplementary figures share a single physical trajectory; this case keeps
them under one target so they cannot drift into inconsistent reruns.
