# Similarity scorecard

The machine-readable authority is
`outputs/checks/similarity_scorecard.json` (schema v4).

- overall Harness score: `81.11/100`;
- direct scientific-region pixel mean: `82.4093/100`;
- evidence tier: `numerical_feature_reproduction`;
- numerical target coverage: `9/9`;
- paper-scale execution: completed;
- scientific assertions in the generated run: `19/19` passed;
- complete scientific-region render contracts: `6/8` passed;
- final-reproduction eligible targets: `6/9`;
- independent review: missing.

## Primary image evidence

| Target | Score | Contract state |
| --- | ---: | --- |
| T001 | 97.0338 | passed |
| T002 | 91.6718 | passed |
| T003 | 80.0861 | passed |
| T004 | 90.0663 | passed |
| T005 | 84.6594 | passed |
| T006 | 80.3256 | passed |
| T007 | 66.4663 | needs repair |
| T008 | 68.9649 | needs repair |

These are direct comparisons of the complete, predeclared scientific regions
after the numerical arrays were frozen.  Whole-canvas appearance is not the
primary score.  The RenderContract may alter only presentation; it cannot
modify physical parameters or numerical data.

## Interpreting 81.11

Plotted targets use an 80-point visual-feature evidence cap and T009 uses a
90-point analytic-reference cap. The lifecycle decision still reads each
target's direct pixel score: T007 and T008 remain below the 80-point acceptance
line even though their physical feature checks pass. The aggregate is not a
percentage of physics correctness; the direct pixel column is the presentation
metric, while formula, provenance, isolation and review remain separate gates.
