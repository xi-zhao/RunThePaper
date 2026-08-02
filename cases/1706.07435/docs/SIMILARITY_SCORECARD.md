# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result.

The primary score measures scientific/numerical similarity. Line width, color,
marker choice, layout, and 3D camera angle are tracked separately by the pixel
presentation score and cannot create scientific credit.

## Case Score

- Scientific visual fidelity score: `90.0/100`.
- Presentation pixel fidelity score: `60.28/100`.
- Similarity level: `complete_reproduction`.
- Short explanation: all six formula/model targets, 15 numerical panel items,
  and paper-exact parameter contracts pass. The scientific score is capped at
  90 because the numerical reference is analytic rather than author arrays;
  the lower pixel score reflects remaining layout and styling differences.

## Scoring Model

Each selected numerical figure or numerical figure panel is scored out of 100:

- feature match: 50 points;
- numeric closeness: 35 points;
- paper-scope coverage: 15 points.

Each component must include a reason. The case score is the weighted average of
the per-figure/panel scores.

## Figure Scores

| Figure/Panel | Weight | Feature match | Numeric closeness | Paper-scope coverage | Score |
| --- | ---: | --- | --- | --- | ---: |
| T001 Main Fig. 1 | 1.0 | `50/50` – bulk sheets and localized edge branch | `35/35` – residuals ≤ `1.43e-14` | `15/15` – 1/1 panel | `90`* |
| T002 Main Fig. 2 | 1.0 | `50/50` – sheets, branch swap, cut | `35/35` – errors ≤ `1.03e-15` | `15/15` – 3/3 panels | `90`* |
| T003 Main Fig. 3 | 1.0 | `50/50` – phases and EP trajectories | `35/35` – residuals ≤ `4.44e-16` | `15/15` – 2/2 panels | `90`* |
| T004 Supp. Fig. 2 | 1.0 | `50/50` – edge-energy surface and zero plane | `35/35` – root error ≤ `6.20e-16` | `15/15` – 1/1 panel | `90`* |
| T005 Supp. Fig. 3 | 1.0 | `50/50` – both cylinder spectra and edge branches | `35/35` – residuals ≤ `1.60e-15` | `15/15` – 4/4 panels | `90`* |
| T006 Supp. Fig. 4 | 1.0 | `50/50` – hybrid sheets and both cuts | `35/35` – exponents `0.5/1.0` | `15/15` – 4/4 panels | `90`* |

`*` Each scientific score is capped at 90 by the harness because the reference
comparison is analytic rather than an author-supplied numerical array.

## Evaluation Metadata

| Figure/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T001 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T002 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T003 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T004 | final_reproduction | paper_exact | false | supporting | true | true | 0 | none |
| T005 | final_reproduction | paper_exact | false | supporting | true | true | 0 | none |
| T006 | final_reproduction | paper_exact | false | supporting | true | true | 0 | none |

`final_reproduction` is allowed only when the target uses the original paper
parameters and records an auditable paper-vs-generated parameter mapping.
Small-system, coarse-grid, subset, and proxy runs must remain `exploratory`.

## Interpretation

- `90-100`: complete reproduction.
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted as reproduced.

## What Prevents A Higher Score

- No author numerical arrays are available, so analytic/direct-model evidence
  caps the primary score at 90.
- The initial pixel mean is `60.28`; the main gaps are aspect ratio, 3D camera,
  typography, occupied bounding box, and mesh/ink density.
- Pixel optimization may change render-only parameters but must not change or
  infer scientific arrays from original pixels.

## Machine-Readable Record

The matching JSON record should live at:

```text
outputs/checks/similarity_scorecard.json
```
