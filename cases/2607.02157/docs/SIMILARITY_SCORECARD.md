# Similarity Scorecard

This document explains how close the reproduction is to the original paper's
numerical result.

The score measures numerical similarity, not visual styling. Line width, color,
marker choice, layout, and 3D camera angle are not counted as scientific
mismatches when the underlying numerical feature matches.

## Case Score

- Overall score: **77.27 / 100**
- Similarity level: **numerical_feature_reproduction**
- Machine-readable record: `outputs/checks/similarity_scorecard.json`

The A100 campaign makes Fig. 2 and Fig. S2 paper-scale and eligible for
`final_reproduction`. Fig. S1 remains `reduced_scale` and therefore
exploratory. Every target uses
`reference_comparison = visual_feature_contract`: we compare physical curve
features against the published panels, not against author data or digitized
pixels.

## Targets

| Target | Figure | Score (capped) | Raw | Key evidence |
| --- | --- | ---: | ---: | --- |
| T001 (critical) | Fig. 2 | 80 | 89 | 16 essential checks pass at paper scale; cluster row is near quantitative; TFIM capacity and NMSE extrema lie in the critical region; the irreversible-work amplitude 0.396 vs paper reading ~0.49 is retained as one nonessential mismatch |
| T002 | Fig. S1 | 70 | 86 | Spectral features pass, but the data use 400 x 2500 rather than 5000 x 5000 drive samples and 400 rather than 10000 TFIM disorder realizations |
| T003 | Fig. S2 | 80 | 88 | 12/12 target checks pass; delayed capacities and all full-Pauli NMSE horizons place their extrema in the critical regions |

## What blocks a higher score

1. Fig. S1 is genuinely reduced-scale, so its score is capped at 70 and it
   cannot be labeled final.
2. The paper publishes no numerical arrays. Fig. 2 and Fig. S2 are therefore
   capped at 80 by feature-level comparison even though their run parameters
   are paper-scale.
3. Fig. 2 retains a real amplitude discrepancy in the TFIM irreversible-work
   peak. It does not break the critical peak or the Landauer inequality, but it
   must remain visible.

## Per-step identity as internal evidence

The central theoretical identity beta*W_irr = chi_d (Eq. 13) holds at machine
precision (max residual 5.7e-14) across every paper-scale run — the strongest
internal consistency evidence this framework admits.
