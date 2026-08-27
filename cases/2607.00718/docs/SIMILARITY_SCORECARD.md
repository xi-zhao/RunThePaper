# Similarity Scorecard

## Case Result

- Scientific visual-fidelity score: `90.31/100`.
- Similarity level: `numerical_feature_reproduction`.
- Scorecard gate: `passed`.
- Paper numerical scope: `23/23` panels executed.
- Presentation-fidelity diagnostic: `66.23/100`, complete with four honest S1
  blockers. It does not contribute to the scientific score.

This percentage summarizes available numerical and visual evidence. Scientific
completion is independently determined by claim, formula, scope, and failure-
attribution gates; a real discrepancy must not be hidden to improve a score.

## Target Scores

| Target | Paper item | Score | Level | Evidence limit |
| --- | --- | ---: | --- | --- |
| T001 | Fig. 1(c) | 90.00 | complete reproduction | caption leaves absolute `r` symbolic |
| T002A | Fig. 2(a-b) | 100.00 | complete reproduction | none |
| T002C | Fig. 2(c) | 100.00 | complete reproduction | none |
| T002D | Fig. 2(d) | 100.00 | complete reproduction | none |
| T003 | Fig. 3(a-d) | 100.00 | complete reproduction | none |
| T004 | Fig. 4(a-b) | 80.00 | numerical feature reproduction | final-version author array unavailable |
| TS01 | Fig. S1(a-d) | 63.12 | numerical feature reproduction | published cutoff undisclosed; quantitative claim rejected |
| TS02 | Fig. S2(a-c) | 90.00 | complete reproduction | analytic feature evidence |
| TS03 | Fig. S3(a-c) | 90.00 | complete reproduction | formula-normalized curves match; source axis label conflicts; no released array |
| TS04 | Fig. S4(a-b) | 90.00 | complete reproduction | analytic feature evidence |

## Scoring Model

Each target can receive 50 points for physical feature recovery, 35 for
numerical closeness, and 15 for paper-scope coverage. Evidence-source caps stop
visual resemblance from receiving author-array credit. TS01 receives zero
numeric-closeness credit because the undisclosed cutoff prevents a valid source
benchmark and the source amplitude conflicts with the cutoff-free solution.
TS03 receives 30/35 numeric-closeness points: all formula-derived landmarks
agree with the source geometry, while the missing array and inconsistent axis
label prevent exact-array credit.

## Machine-Readable Record

`outputs/checks/similarity_scorecard.json`
