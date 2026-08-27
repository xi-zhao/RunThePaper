# Similarity Scorecard

The scorecard separates scientific validity from rendering fidelity. Formula gates,
physics assertions, provenance, and scope are acceptance gates. The numeric-closeness
component comes directly from foreground pixel differences inside predeclared
scientific regions after numerical freeze. Full-canvas similarity is diagnostic only.

## Case Score

- Scientific composite: `69.29/100` (`numerical_feature_reproduction`).
- Primary foreground-pixel diagnostic: mean `39.77/100`, median `38.96/100`.
- Full-canvas diagnostic: mean `89.27/100`; it is not used as scientific evidence.
- Pixel contracts: `24/24` passed.
- Parameter status: 1 paper-exact thermodynamic target, 9 paper-subset
  phase-space targets, and 14 reduced-scale quantum targets.

## Scoring Model

Each target has feature match (50), foreground-pixel numeric closeness (35), and
paper-scope coverage (15). The source-figure-only evidence cap is 70. A high visual
score cannot repair a failed physics assertion, copied data, or a closed formula gate.

## Target Scores

| Target | Foreground pixel | Feature | Numeric | Scope | Composite | Parameters |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| T001 | 48.4587 | 43 | 16.96 | 15 | 70.00 | reduced_scale |
| T002 | 40.0490 | 40 | 14.02 | 15 | 69.02 | reduced_scale |
| T003 | 31.6442 | 40 | 11.08 | 15 | 66.08 | reduced_scale |
| T004 | 40.6902 | 42 | 14.24 | 15 | 70.00 | reduced_scale |
| T005 | 32.7493 | 42 | 11.46 | 15 | 68.46 | reduced_scale |
| T006 | 46.7618 | 42 | 16.37 | 15 | 70.00 | reduced_scale |
| T007 | 25.6310 | 42 | 8.97 | 15 | 65.97 | reduced_scale |
| T008 | 39.3538 | 42 | 13.77 | 15 | 70.00 | reduced_scale |
| T009 | 35.5026 | 48 | 12.43 | 15 | 70.00 | paper_exact |
| T010 | 39.6632 | 42 | 13.88 | 15 | 70.00 | reduced_scale |
| T011 | 49.9158 | 42 | 17.47 | 15 | 70.00 | reduced_scale |
| T012 | 50.6574 | 34 | 17.73 | 15 | 66.73 | reduced_scale/source discrepancy |
| T013 | 47.3217 | 41 | 16.56 | 15 | 70.00 | reduced_scale |
| T014 | 45.4818 | 42 | 15.92 | 15 | 70.00 | reduced_scale |
| T015 | 43.1160 | 41 | 15.09 | 15 | 70.00 | reduced_scale |
| T016 | 35.9739 | 46 | 12.59 | 15 | 70.00 | paper_subset |
| T017 | 38.5574 | 46 | 13.50 | 15 | 70.00 | paper_subset |
| T018 | 37.0400 | 46 | 12.96 | 15 | 70.00 | paper_subset |
| T019 | 37.7926 | 46 | 13.23 | 15 | 70.00 | paper_subset |
| T020 | 73.0848 | 50 | 25.58 | 15 | 70.00 | paper_subset |
| T021 | 26.9714 | 46 | 9.44 | 15 | 70.00 | paper_subset |
| T022 | 32.1579 | 46 | 11.26 | 15 | 70.00 | paper_subset |
| T023 | 27.2118 | 46 | 9.52 | 15 | 70.00 | paper_subset |
| T024 | 28.7437 | 46 | 10.06 | 15 | 70.00 | paper_subset |

## Why The Pixel Mean Is Low

- Phase portraits use 12 independently integrated trajectories; the paper images are
  much denser. This is a real data-density difference, not a styling detail.
- Reduced `N_b` changes spectral branch positions and point counts.
- Text, ticks, and white background are excluded from the foreground metric, so they
  cannot inflate the reported scientific-region score.
- S2 right contains a source caption/curve conflict and is deliberately penalized in
  feature scoring despite a moderate pixel score.

## What Prevents A Higher Scientific Score

- Fourteen targets are reduced-scale, and nine more use unpublished
  phase-space initials/sampling reconstructed independently.
- Only the source images, not author numerical arrays, are available for comparison.
- A fresh-context reviewer has not yet attempted to falsify T009 or review the
  reconstructed phase-space boundary.

Machine-readable record: `outputs/checks/similarity_scorecard.json`.
