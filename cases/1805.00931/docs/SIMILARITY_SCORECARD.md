# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result. For line figures, the 35-point numerical-closeness component is
derived from the post-freeze foreground pixel difference inside predeclared scientific
regions. Full-figure SSIM is a layout diagnostic and does not replace the scientific
crop. Table I is scored by exact cell equality.

## Case Score

- Overall score: `75.01/100`
- Similarity level: `numerical_feature_reproduction`
- Short explanation: all formula and physics checks pass; Table I is exact, while
  four figure targets remain capped by reduced parameters.

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
| T001 Fig. 2 main | 2.0 | `38/50` - finite-L SFF route passes | `20.28/35` - crop pixel score 57.9399 | `15/15` | `70.00` (scale cap) |
| T002 Fig. 2 inset | 1.0 | `42/50` - short-time route passes | `20.28/35` - crop pixel score 57.9381 | `15/15` | `70.00` (scale cap) |
| T003 Fig. 3 left | 2.0 | `38/50` - transfer-gap checks pass | `17.03/35` - crop pixel score 48.6448 | `7.5/15` | `62.53` |
| T004 Fig. 3 right | 2.0 | `42/50` - mean-field sweep checks pass | `17.17/35` - crop pixel score 49.0696 | `15/15` | `70.00` (scale cap) |
| T005 Table I | 2.0 | `50/50` - multiplicity derivation exact | `35/35` - all cells exact | `15/15` | `100.00` |

## Evaluation Metadata

| Figure/Table/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T001 | exploratory | reduced_scale | true | main_claim | true | true | 0 | not_paper_parameters |
| T002 | exploratory | reduced_scale | false | supporting | true | true | 0 | not_paper_parameters |
| T003 | exploratory | reduced_scale | true | main_claim | true | true | 0 | not_paper_parameters |
| T004 | exploratory | reduced_scale | true | main_claim | true | true | 0 | not_paper_parameters |
| T005 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |

`final_reproduction` is allowed only when the target uses the original paper
parameters and records an auditable paper-vs-generated parameter mapping.
Small-system, coarse-grid, subset, and proxy runs must remain `exploratory`.

## Interpretation

- `90-100`: top similarity tier (historical enum `complete_reproduction`; not lifecycle completion).
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted as reproduced.

## What Prevents A Higher Score

- Figure 2 uses `L=8`, 128 realizations instead of `L=15`, 9490 realizations.
- Figure 3 left omits paper `t=10..15`; `t=9` is sampled at only three widths.
- Figure 3 right uses `t=7` instead of `t=13`.
- A fresh-context independent review is still pending.

## Machine-Readable Record

The matching JSON record should live at:

```text
outputs/checks/similarity_scorecard.json
```
