# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result.

The score measures numerical similarity, not visual styling. Line width, color,
marker choice, layout, and 3D camera angle are not counted as scientific
mismatches when the underlying numerical feature matches.

## Case Score

- Overall score: 78.75/100
- Similarity level: numerical feature reproduction
- Short explanation: exact agreement on Tables V and X is offset by a failed
  essential mitten-pivot assertion and a reduced-scale Fig. 8 benchmark.

## Scoring Model

Each in-scope numerical figure, table, or panel is scored out of 100:

- feature match: 50 points;
- numeric closeness: 35 points;
- paper-scope coverage: 15 points.

Each component must include a reason. The case score is the weighted average of
the per-figure/table/panel scores.

## Figure Scores

| Figure/Table/Panel | Weight | Feature match | Numeric closeness | Paper-scope coverage | Score |
| --- | ---: | --- | --- | --- | ---: |
| Tables I/VI (T001) | 1.0 | 35/50 - CSS/rate/weight structure reproduced | 18/35 - 4/8 rows, 9/16 weight components exact | 15/15 - all eight mitten rows audited | 55* |
| Table V (T002) | 1.0 | 50/50 - Eq. E15 structure exact | 35/35 - 32/32 rows exact | 15/15 - full table | 100 |
| Fig. 8 (T003) | 1.0 | 45/50 - independent Algorithm-1 validation | 5/35 - paper hardware/timing not comparable | 10/15 - one panel, two bounded sizes | 60 |
| Table X (T004) | 1.0 | 50/50 - Eq. I1 structure exact | 35/35 - 24/24 within rounding | 15/15 - all three experiments | 100 |

`*` T001's component total is 68, but the failed essential pivot-invertibility
assertion applies the harness physics cap of 55.

## Evaluation Metadata

| Figure/Table/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T001 | exploratory | paper_exact | true | main_claim | true | true | 0 | numeric_mismatch |
| T002 | final_reproduction | paper_exact | false | supporting | true | true | 0 | none |
| T003 | exploratory | reduced_scale | true | method_validation | true | true | 0 | insufficient_compute |
| T004 | final_reproduction | paper_exact | false | supporting | true | true | 0 | none |

`final_reproduction` is allowed only when the target uses the original paper
parameters and records an auditable paper-vs-generated parameter mapping.
Small-system, coarse-grid, subset, and proxy runs must remain `exploratory`.

## Interpretation

- `90-100`: top similarity tier (historical enum `complete_reproduction`; not lifecycle completion).
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted as reproduced.

## What Prevents A Higher Score

- T001 cannot exceed the feature threshold while an essential printed
  invertibility claim fails under the literal, version-matched construction.
- T003 is capped by `reduced_scale` and `source_figure_only`; its pixel status
  is explicitly `not_applicable`, not silently missing.
- Thirteen additional numerical items are transparently deferred for missing
  inputs, excessive compute, or user-descoping.
- A fresh-context independent review has not yet been supplied.

## Machine-Readable Record

The matching JSON record should live at:

```text
outputs/checks/similarity_scorecard.json
```
