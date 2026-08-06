# Similarity Scorecard

## Final score

- Primary score: **46.72/100 raw foreground-pixel similarity** across seven
  comparable numerical figures (**46.71/100** after per-target two-decimal
  normalization in the harness).
- Visual tier: **feature_not_accepted**.
- Scientific artifact coverage: **7/8 (87.5%)**; these are separate gates.
- Full-canvas SSIM: **0.768**.
- Full-canvas pixel similarity: **90.41/100**, retained only as a layout
  diagnostic because white background inflates it.

The primary metric is evaluated only after each figure's data pass scientific
checks and are frozen. Source pixels are comparison evidence only. A low visual
score does not erase a valid physical result, and a high visual score cannot
upgrade reduced sampling, a method mismatch, or blocked coverage.

## Score by numerical figure

| Target | Figure | Foreground pixel score | Scientific state | Main gap |
| --- | --- | ---: | --- | --- |
| T001 | Fig. 2 | 47.65 | analytic exact; quantum artifact valid | finite-time QT replaces ED |
| T002 | Fig. 3 | 39.90 | artifact valid, feature-level | 6-16 trajectories/job |
| T003 | Fig. 4 | 62.66 | artifact valid, feature-level | Z4 residual 0.13-0.62 |
| T004 | Fig. S1 | 63.42 | artifact valid, equation-exact | rendering mismatch |
| T005 | Fig. S2 | 48.19 | artifact valid with discrepancy | plotted branch is nonlinearly unstable, but its stated positive-eigenvalue evidence conflicts with the printed equations |
| T007 | Fig. S5 | 28.50 | artifact valid, reduced | 4 vs 6-16, not 500 vs 3000 |
| T008 | parity | 36.68 | exact kernel/parity invariants | sampled distribution mismatch |
| T006 | formal S3-S4 | unscored | blocked | formal parameters unavailable |

Each scored target allocates its foreground-pixel score over the harness's
50/35/15 feature, numeric, and scope components. This keeps the final scalar
anchored to pixel difference while the independent physics assertions remain a
non-negotiable prerequisite.

Exact registration, foreground masks, SSIM values, and frozen data hashes are
in `outputs/checks/render_similarity.json`. The schema-normalized target gates
and score are in `outputs/checks/similarity_scorecard.json`.
