# Similarity Scorecard

This document separates the historical T001 render/feature score from the
whole-paper atomic reproduction measure.

The primary score is the foreground-pixel difference in two predeclared
scientific theory regions. The arrays are independently derived and hash-frozen
before the source render becomes available to the presentation-only channel.

## Historical T001 Score

- Overall score: `80.64 / 100`
- Similarity level: `numerical_feature_reproduction`
- Short explanation: all 13 formula-derived curves and all paper parameters are
  present. Residual pixels come from legacy rasterization, text, antialiasing,
  and coincident-curve visibility rather than a changed physical array.

## Whole-Paper Reproduction Measure

- Eligible items: **4**.
- Reproduced items: **4**.
- Unresolved items: **0**.
- Coverage: **100.00%**.
- Fidelity and reproduction degree: **87.66/100**.

The three analytic claims use exact factorization/rank witnesses plus frozen
sanity checks. They are not raster-comparable and each is capped at 90 until
fresh review; T001 retains its measured 80.64 scientific-region pixel score.

## Scoring Model

Each in-scope numerical figure, table, or panel is scored out of 100:

- feature match: 50 points;
- numeric closeness: 35 points;
- paper-scope coverage: 15 points.

Each component must include a reason. The case score is the weighted average of
targets with a comparable declared primary metric. A critical target may be
excluded from aggregation only with `score_aggregation=excluded` and an
explicit `score_exclusion_reason`; it remains required for lifecycle
completion.

## Figure Scores

| Figure/Table/Panel | Weight | Feature match | Numeric closeness | Paper-scope coverage | Score |
| --- | ---: | --- | --- | --- | ---: |
| T001 Main Fig. 2 | 1.0 | `40.32/50` - all branches present | `28.22/35` - frozen paper-exact arrays | `12.10/15` - all 13 curves | `80.64` |
| T002 arbitrary multi-point theorem | 1.0 | `50/50` | `35/35` | `15/15` | `90.00` capped |
| T003 protected-chain theorem | 1.0 | `50/50` | `35/35` | `15/15` | `90.00` capped |
| T004 protected all-to-all theorem | 1.0 | `50/50` | `35/35` | `15/15` | `90.00` capped |

## Evaluation Metadata

| Figure/Table/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T001 Main Fig. 2 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T002 general theorem | final_reproduction | not_applicable | true | main_claim | true | true | 0 | none |
| T003 chain theorem | final_reproduction | not_applicable | true | main_claim | true | true | 0 | none |
| T004 all-to-all theorem | final_reproduction | not_applicable | true | main_claim | true | true | 0 | none |

`final_reproduction` is allowed only when the target uses the original paper
parameters and records an auditable paper-vs-generated parameter mapping.
Small-system, coarse-grid, subset, and proxy runs must remain `exploratory`.

## Interpretation

- `90-100`: top similarity tier (historical enum `complete_reproduction`; not lifecycle completion).
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted as reproduced.

## What Prevents A Higher Score

- The paper raster was produced by Matplotlib 1.5.3 and Ghostscript 9.16;
  modern font and antialiasing differences remain after legally matching the
  canvas, axis box, palette, line width, dash sequences, and draw order.
- The right-bottom crop contains few foreground pixels, so subpixel edge
  differences have a larger effect on its foreground-only score.
- Fresh-context scientific review remains a lifecycle gate, independent of the
  similarity score.
- T002-T004 are capped at 90 because fresh review is pending; rendering cannot
  and should not raise their analytic score.

## Machine-Readable Record

The matching JSON record should live at:

```text
outputs/checks/similarity_scorecard.json
```
