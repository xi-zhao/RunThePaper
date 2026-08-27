# Target Ledger

## Existing reduced-scale targets

| ID | Correct paper scope | Current evidence state |
| --- | --- | --- |
| T001 | Main Fig. 1 | 9 atomic series covered; H0 inset missing |
| T002 | Main Fig. 2 | 7 series covered; two sector P(s) curves missing |
| T003 | Main Fig. 3 | 5/5 series covered |
| T004 | Actual Supplement Fig. S2, low-energy states | 3/3 series covered; legacy filenames retain `s1` |
| T005 | Actual Supplement Fig. S1, optimization | 9/9 series covered; legacy filenames retain `s2` |
| T006 | Supplement Fig. S3 | 13/26 series covered; fit evidence missing |
| T007 | Supplement Fig. S4 | 6/6 panels covered |
| T008 | Supplement Fig. S5 | 3/4 series covered; linear fit missing |
| T009 | Supplement Fig. S6 | 3/3 panels covered for an independent random realization |

All nine are reduced-scale evidence. The code-ready paper-scale campaign has
not run and cannot be called paper-exact.

## Explicit uncovered targets

| ID | Atomic items | Direct reason | Root cause | Next action |
| --- | ---: | --- | --- | --- |
| T010 | 1 | lemma has no claim-specific check | figure-centered scope gap | independent analytic derivation + fresh review |
| T011 | 1 | H0 inset branch absent | confirmed output completeness defect | split/freeze both inset branches; rerun T001 |
| T012 | 2 | two sectors pooled into one histogram | confirmed aggregation defect | split/freeze sector histograms; rerun T002 |
| T013 | 6 | short fits discarded | confirmed evidence-schema defect | freeze coefficients/grids and intersection checks |
| T014 | 6 | long fits discarded; paper lane unrun | confirmed schema defect, then execution question | fix schema, then run paper-scale T006 |
| T015 | 1 | exponent computed in renderer | confirmed architecture defect | move fit to numeric runner; freeze checks |
| T016 | 1 | wrong fit object selected | confirmed branch-selection defect | fit second series linearly and logarithmically |

Machine-readable detail is authoritative in `figure_coverage.json`,
`causal_diagnoses.json`, and `outputs/checks/similarity_scorecard.json`.
