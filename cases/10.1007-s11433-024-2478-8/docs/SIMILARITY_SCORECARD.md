# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result.

The score measures numerical similarity, not visual styling. Line width, color,
marker choice, layout, and 3D camera angle are not counted as scientific
mismatches when the underlying numerical feature matches.

## Case Score

- Overall score:
- Similarity level:
- Short explanation:

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
| T000 | 1.0 | `/50` - reason | `/35` - reason | `/15` - reason |  |

## Evaluation Metadata

| Figure/Table/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T000 | exploratory/final_reproduction | paper_exact/reduced_scale/... | true | main_claim | true | true | 0 | none |

`final_reproduction` is allowed only when the target uses the original paper
parameters and records an auditable paper-vs-generated parameter mapping.
Small-system, coarse-grid, subset, and proxy runs must remain `exploratory`.

## Interpretation

- `90-100`: complete reproduction.
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted as reproduced.

## What Prevents A Higher Score

- TBD

## Machine-Readable Record

The matching JSON record should live at:

```text
outputs/checks/similarity_scorecard.json
```
