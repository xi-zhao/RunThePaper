# Similarity Scorecard

## Case Score

- Overall score: **90.0/100**.
- Similarity level: top numerical similarity tier (`complete_reproduction` in
  the historical enum; this is not lifecycle completion).
- Direct scientific-region pixels: **92.7897** for T001 and **95.1998** for T002.
- Cap: `90`, because the paper supplies no author raw arrays and the accepted
  comparison class is `analytic_reference`.

## Scoring Policy

The primary metric is the direct per-pixel grayscale difference inside six
predeclared curve fields. Titles, legends and outer labels are excluded; full
figures, foreground-only scores and ink proximity remain diagnostics. Numerical
data were frozen before the source figures became available to rendering.

| Target | Weight | Feature | Numeric | Coverage | Capped score | Direct pixel score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T001 Main Fig. 2 | 1.0 | 45/50 | 31.5/35 | 13.5/15 | 90.0 | 92.7897 |
| T002 Main Fig. 4 | 1.0 | 45/50 | 31.5/35 | 13.5/15 | 90.0 | 95.1998 |

Both targets are `final_reproduction`, `paper_exact`, data-backed, critical to
the main claim, and generated with zero manual numerical intervention.
All six molecular panels also pass the separate machine-readable acceptance in
`outputs/checks/panel_target_acceptance.json`.

## What Prevents A Higher Score

Only the evidence-class cap: author-generated raw arrays are unavailable.
Fresh-context review affects lifecycle state, not this numerical score.

The propane `591x` discrepancy remains `inconclusive`. Neither the similarity
score nor the pixel evidence may emit `paper_error_candidate`; protocol-v2 still
requires a second distinct method, strict tolerance basis, falsification beyond
the four plotted comparator families, and fresh inventory-first review. The
completed claim-level self-audit is in `PAPER_REVIEW_PROTOCOL_V2.md`.

Machine-readable evidence is in `outputs/checks/similarity_scorecard.json` and
`outputs/checks/pixel_evidence.json`.
