# Similarity Scorecard

## Primary score

- Scientific-region point-wise foreground RGB similarity: **58.7592 / 100**
- Full-canvas similarity: **89.1830 / 100** (`layout_diagnostic_only`)
- Harness evidence score: **70 / 100** (`source_figure_only` reference cap)

The campaign-facing primary score is the first number: literal pixel differences in
predeclared theory/data regions after resizing the generated crop to the source crop.
The full-canvas score is not used to claim scientific success. The harness's 70-point
score is a separate evidence-tier result and is not substituted for the pixel score.

## Reproduction item measure

| Quantity | Value |
| --- | ---: |
| eligible numerical panels | 13 |
| covered panels | 12 |
| uncovered panels | 1 |
| coverage | **92.31%** |
| mean fidelity of covered items | **70.00 / 100** |
| reproduction degree, with uncovered items scored zero | **64.62 / 100** |

The historical 70-point evidence score averages the 12 generated targets. The
paper-level degree additionally includes `D001` as zero, so the missing panel cannot
disappear from the result.

## Per-target pixel scores

| Target | Paper panel | Scientific-region score | Full canvas | Scientific assessment |
| --- | --- | ---: | ---: | --- |
| T001 | Main Fig. 1(d) potential | 69.4933 | 78.4071 | periodic extrema and energy scale match |
| T002 | Main Fig. 2(a) bands | 48.7227 | 92.9209 | 10.915 meV isolated band and TB overlay match |
| T003 | Main Fig. 2(b) DOS | 66.2330 | 91.8692 | density scale matches; finite-grid peak heights differ |
| T004 | Main Fig. 2(c) Wannier | 59.8404 | 85.9100 | normalized localized orbital; camera/grid styling differs |
| T005 | Main Fig. 2(d) hopping | 55.7083 | 94.2903 | hierarchy and curves match |
| T006 | Main Fig. 3(a) interactions | 49.9860 | 92.3936 | U ordering and scales match |
| T007 | Main Fig. 3(b) exchange | 46.8218 | 92.2879 | exchange decay and 0.06 threshold match |
| T008 | Main Fig. 4(a) contour | 77.2357 | 82.4218 | nearly nested contour matches |
| T009 | Supp. Fig. 5(a) potential | 70.6263 | 80.3142 | periodicity and energy scale match |
| T010 | Supp. Fig. 5(b) bands | 49.6022 | 91.6858 | 20.607 meV top-band width matches |
| T011 | Supp. Fig. 5(c) hopping | 59.5268 | 93.9335 | hierarchy and trend match |
| T012 | Supp. Fig. 5(d) interactions | 51.3142 | 93.7611 | ordering and trend match |
| D001 | Main Fig. 1(c) DFT displacement map | not comparable | not comparable | uncovered: indispensable first-principles inputs are unpublished |

## Why the foreground score is lower than visual inspection suggests

For sparse line plots, a one-pixel displacement turns a colored source pixel into a
white-vs-colored mismatch even when the curves are visually and physically close. This
metric is intentionally strict. It was improved only through post-freeze crop/axes/style
alignment; physical parameters and frozen numerical arrays were not changed.

## Coverage effect

Twelve of thirteen numerical regions are executable. Main Fig. 1(c) remains blocked by
missing exact first-principles metadata and therefore prevents case completion. Its
absence is represented as a zero-fidelity uncovered item rather than hidden inside the
historical target or pixel averages. The machine-readable diagnosis records the direct
cause, publication-level root cause, code assessment and next discriminating action.
