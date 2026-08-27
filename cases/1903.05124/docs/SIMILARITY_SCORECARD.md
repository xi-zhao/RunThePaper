# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result.

The score measures numerical similarity, not visual styling. Line width, color,
marker choice, layout, and 3D camera angle are not counted as scientific
mismatches when the underlying numerical feature matches.

## Case Score

- Overall score: `78.41/100`
- Similarity level: `numerical_feature_reproduction` for the complete paper scope
- Short explanation: T001–T004 and T006 each reach `80`; T005 reaches `70` because all seven panels and core physics checks pass but `nu(d)` stability remains partial. All 44 numerical items now contribute independent evidence to the panel-weighted denominator.

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
| T001 / Main Fig. 2(b–e) | 4 | `50/50` - all frozen physics features pass | `15/35` - `p_c` MAE 0.00409, but reduced sampling/grid and no author raw data | `15/15` - 4/4 panels at paper geometry | 80 |
| T002 / Supp. Fig. S2 | 4 | `50/50` - design moments match | `15/35` - no author points/samples | `15/15` - 4/4 panels, paper scale | 80 |
| T003 / Supp. Fig. S3 | 16 | `50/50` - protection/loss features match | `15/35` - no author trajectories; SD/SE conflict | `15/15` - 16/16 panels, paper scale | 80 |
| T004 / Supp. Fig. S4 | 10 | `50/50` - all ten items and frozen checks pass | `15/35` - `p_c` MAE 0.01182 and mean `nu=1.074`, but reduced sizes/statistics | `15/15` - 10/10 items at feature scale | 80 |
| T005 / Supp. Fig. S5 | 7 | `40/50` - all panels/core checks pass; `nu(d)` varies too strongly | `15/35` - `p_c` MAE 0.00484 and mean `nu=1.114`, but reduced sizes/statistics | `15/15` - 7/7 panels at feature scale | 70 |
| T006 / Supp. Fig. S6 | 3 | `50/50` - all three panels and frozen block-size checks pass | `15/35` - reduced `L≤24` campaign, no author raw data, and noisier `alpha` | `15/15` - 3/3 panels across all paper `m` values | 80 |

## Evaluation Metadata

| Figure/Panel | Stage | Parameter match | Critical | Role | Artifact pass | Data-backed | Manual interventions | Failure type |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| T001 | exploratory | paper_subset (paper geometry, reduced sampling/grid) | true | main_claim | true | true | 0 | reduced_sampling_or_grid |
| T002 | final_reproduction | paper_exact | false | method_validation | true | true | 0 | none |
| T003 | final_reproduction | paper_exact | true | main_claim | true | true | 0 | none |
| T004 | exploratory | paper_subset (`L≤24`, 17 `p` points, 8 realizations/cell) | true | main_claim | true | true | 0 | reduced_sampling_or_grid |
| T005 | exploratory | paper_subset (`L≤24`, 17 `p` points, 8 realizations/cell) | true | main_claim | true | true | 0 | reduced_sampling_or_grid |
| T006 | exploratory | paper_subset (all `m`, exact `d/m=3`, reduced `L≤24` and statistics) | true | supporting | true | true | 0 | reduced_sampling_or_grid |

`final_reproduction` is allowed only when the target uses the original paper
parameters and records an auditable paper-vs-generated parameter mapping.
Small-system, coarse-grid, subset, and proxy runs must remain `exploratory`.

## Interpretation

- `90-100`: complete reproduction.
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted as reproduced.

## What Prevents A Higher Score

- T001 uses reduced statistics, four transition sizes through `L=24`, and coarse probability grids; its `80` score is capped at feature level.
- T004 covers all ten items but uses four sizes through `L=24` and eight realizations per cell; its `80` score is capped at feature level.
- T005 covers all seven panels but uses four sizes through `L=24` and eight realizations per cell; fitted `nu` spans `0.679`, so its score is `70` rather than paper-level credit.
- T006 covers all three panels and six paper block sizes, but sizes stop at `L=24`; mean `nu=0.989` and noisy `alpha` estimates support the feature claim without paper-level numeric precision.
- Original random seeds and raw trajectories are unavailable for T002/T003.
- T003's caption uncertainty label conflicts with the visible source error-bar scale.

## Machine-Readable Record

The matching JSON record should live at:

```text
outputs/checks/similarity_scorecard.json
```
