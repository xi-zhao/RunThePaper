# Similarity Scorecard

## Final score

- Primary score: **46.72/100 raw foreground-pixel similarity** across seven
  comparable numerical figures (**46.71/100** after per-target two-decimal
  normalization in the harness).
- Visual tier: **feature_not_accepted**.
- Atomic scientific coverage: **29/31 numerical items (93.55%)**.
- Covered-item mean fidelity: **48.23/100**.
- Paper reproduction degree: **45.12/100** = coverage × fidelity, with each
  uncovered item contributing zero.
- Full-canvas SSIM: **0.768**.
- Full-canvas pixel similarity: **90.41/100**, retained only as a layout
  diagnostic because white background inflates it.

The primary metric is evaluated only after each figure's data pass scientific
checks and are frozen. Source pixels are comparison evidence only. A low visual
score does not erase a valid physical result, and a high visual score cannot
upgrade reduced sampling, a method mismatch, or blocked coverage.

The old `7/8` number counted implementation targets and is retained only as a
diagnostic grouping. It is not the public coverage metric: T001 represents seven
panels, whereas T007 represents one. The authoritative denominator therefore
counts every independently adjudicable numerical item.

## Score by numerical figure

| Target | Figure | Foreground pixel score | Scientific state | Main gap |
| --- | --- | ---: | --- | --- |
| T001 | Fig. 2 | 47.65 | analytic exact; quantum artifact valid | finite-time QT replaces ED |
| T002 | Fig. 3 | 39.90 | artifact valid, feature-level | 6-16 trajectories/job |
| T003 | Fig. 4 | 62.66 | artifact valid, feature-level | Z4 residual 0.13-0.62 |
| T004 | Fig. S1(a-b) | 63.42 | artifact valid, equation-exact | rendering mismatch |
| T005 | Fig. S2(a-c) | 48.19 | artifact valid with discrepancy | plotted branch is nonlinearly unstable, but its stated positive-eigenvalue evidence conflicts with the printed equations |
| T007 | Fig. S5 | 28.50 | artifact valid, reduced | 4 vs 6-16, not 500 vs 3000 |
| T008 | parity panels (a-c) | 36.68 | exact kernel/parity invariants | sampled distribution mismatch |
| T006 | formal Fig. S3 | 0.00 | uncovered | formal source, panel inventory, parameters, and observable unavailable |
| T006 | formal Fig. S4 | 0.00 | uncovered | formal source, panel inventory, parameters, and observable unavailable |

Each scored target allocates its foreground-pixel score over the harness's
50/35/15 feature, numeric, and scope components. This keeps the final scalar
anchored to pixel difference while the independent physics assertions remain a
non-negotiable prerequisite.

## Explicit Uncovered-item Markers

- **Formal Fig. S3** — source/input blocker. It remains a separate zero-score
  item; no substitute panel or author numerical array is allowed.
- **Formal Fig. S4** — source/input blocker. It remains a separate zero-score
  item; no substitute panel or author numerical array is allowed.

These are coverage failures, not visual-score failures. Their exact panel
counts may increase the denominator after the formal supplement is acquired;
the current one-item-per-confirmed-figure representation is deliberately the
minimum non-guessing inventory.

Exact registration, foreground masks, SSIM values, and frozen data hashes are
in `outputs/checks/render_similarity.json`. The schema-normalized target gates
and score are in `outputs/checks/similarity_scorecard.json`.
