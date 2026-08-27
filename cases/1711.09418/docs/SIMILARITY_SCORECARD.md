# Similarity Scorecard

## Case Score

- Overall score: **90.0/100**.
- Numerical tier: `complete_reproduction` in the historical score enum.
- Lifecycle implication: none by itself; `complete` additionally requires a
  passing fresh-context independent review.

## Scoring Policy

The primary visual metric is the direct grayscale difference of every pixel in
predeclared scientific curve regions. Legends, text, and outer labels are
excluded. Full-figure, foreground-union, and ink-proximity metrics remain
diagnostics. The numerical runner never reads source pixels; only the later
RenderContract may tune presentation while numerical hashes stay locked.

The target score is capped at 90 because the paper provides no raw numerical
arrays and the comparison role is `analytic_reference`.

## Figure Scores

| Target | Direct scientific-region pixel score | Feature match | Numeric closeness | Scope coverage | Capped target score |
| --- | ---: | ---: | ---: | ---: | ---: |
| T001 Main Fig. 2 | 99.4359 | 45/50 | 31.5/35 | 13.5/15 | 90.0 |
| T002 Main Fig. 3 | 95.1851 | 45/50 | 31.5/35 | 13.5/15 | 90.0 |

## Region Diagnostics

| Pixel target | Scientific content | Direct pixel score | Foreground sensitivity score |
| --- | --- | ---: | ---: |
| PXT_T001_CORE | central Fig. 2 curves | 99.4306 | 72.9799 |
| PXT_T001_TAILS | Fig. 2 low-amplitude tails | 99.4411 | 75.3022 |
| PXT_T002_RIGHT_FIELD | Fig. 3 main spectrum field | 95.6147 | 51.9147 |
| PXT_T002_LOW_FIELD | Fig. 3 sector onsets | 94.7556 | 47.3533 |

Foreground-only scores are deliberately not substituted for the direct
per-pixel score: they amplify subpixel antialiasing and line-rasterization
changes. They are retained to reveal line-placement sensitivity.

## Scientific discrepancy boundary

The source Fig. 3 prints sector labels `0,1,2,3,5,6`. Equations (9) and (11),
the independent enumeration, and the plotted onset sequence support the
formula-derived interpretation `0,1,2,3,4,5`. The reproduction displays that
interpretation, while the conflict with the literal paper claim remains
`inconclusive`. A pixel score cannot decide the scientific identity, and no
current score emits `paper_error_candidate`.

## Machine-Readable Record

See `outputs/checks/similarity_scorecard.json` and
`outputs/checks/pixel_evidence.json`.
