# Similarity Scorecard

## Case Score

- Overall: **90.0/100**.
- Level: `complete_reproduction`.
- Both targets use paper-exact parameters, verified formulas, independent
  numerical provenance, final artifacts, and complete figure coverage.
- The score is capped at 90 because the paper supplies analytic formulas and
  source figures rather than a separate author numeric table/CSV.

## Scientific And Pixel Components

Pixel difference contributes to the 35-point numeric-closeness component; it
cannot substitute for the formula, provenance, or full-scope gates.

| Target | Weight | Feature | Pixel/numeric closeness | Scope | Raw total | Applied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T001 / Fig. 1 | 1 | 50/50 | 30.96/35 (`SSIM=0.884565`) | 15/15 | 95.96 | 90 |
| T002 / Fig. 2(a-c) | 3 | 50/50 | 27.34/35 (`SSIM=0.781102`) | 15/15 | 92.34 | 90 |

## Pixel Evidence

| Target | Canvas | Axis IoU | Ink density ratio | Ink proximity | SSIM |
| --- | --- | ---: | ---: | ---: | ---: |
| T001 | exact `933 x 625` | 0.972454 | 0.999173 | 0.954913 | 0.884565 |
| T002 | exact `2723 x 625` | 0.924759 | 0.944133 | 0.907293 | 0.781102 |

Absolute-difference boards are in `docs/comparisons/`. They expose real font,
title, label, and antialiasing differences instead of hiding them by copying
the source. Curve data remain formula-generated.

## Why It Is Scientifically Complete

- All `7/7` formula cards are open.
- All `4/4` numerical panels are covered.
- All six essential physics assertions pass.
- There are no proxy parameters, reduced grids, missing author inputs, or
  unresolved methods.
- Source pixels enter only terminal evaluation.

Machine record: `outputs/checks/similarity_scorecard.json`.
