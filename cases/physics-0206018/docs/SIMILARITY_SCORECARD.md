# Similarity Scorecard

## Result

- Comparison role: post-run evidence only, after the independent NPZ was frozen.
- Primary metric: scientific-foreground pixel similarity,
  `100 * (1 - foreground-union grayscale MAE / 255)`.
- Raw comparable-target mean: `58.16/100`.
- Harness-normalized mean: `50.49/100`; reduced-scale and
  source-figure-only comparisons cap each target at `70`.
- Secondary layout diagnostic: mean full-image SSIM `0.7151`.
- Pixel contract: `needs_repair` for Figs. 5 and 7; Fig. 6 passes the `60/100` feature band.
- Scientific result: all three targets pass their independent physical checks.

| Target | Foreground pixels | Full-image SSIM | Normalized score | Scientific reading |
| --- | ---: | ---: | ---: | --- |
| Fig. 5 cross section | 38.35 | 0.8711 | 38.35 | Envelope and resonance sequence appear, but sparse peak shifts receive a strict pixel penalty. |
| Fig. 6 near field | 93.00 | 0.4736 | 70.00 | Coupled rings and radiation region match; the target is capped because the run is reduced-scale. |
| Fig. 7 far field | 43.11 | 0.8006 | 43.12 | Principal directions and narrow-lobe sequence match, with angular peak drift. |

The foreground score is primary because the almost-white background would
otherwise inflate full-image pixel similarity to `95.32/100`. SSIM remains
useful for diagnosing layout and texture but is not the final score.

## Evidence Boundary

The numerical runner could not read `raw/`, `references/`, original figures, or
pixel-layout directories. Its frozen data SHA-256 is
`34cc9005d5b14b6eb57e729810712864580af83da6de22a2dec8a7a8f4a33420`.
Only the post-run RenderContract read the source images. It adjusted canvas,
axes, fonts, grayscale, line width, and interpolation without changing any
physical parameter or numerical array.

## Why The Pixel Score Is Not Higher

- the paper does not disclose the rounding curve or nonuniform element map;
- the run used 432 boundary elements rather than the paper's 1600;
- the cross-section scan has 73 independent points before render interpolation;
- narrow resonances and far-field peaks amplify small mesh-dependent shifts;
- Fig. 6 fills almost the whole panel, whereas Figs. 5 and 7 have sparse dark
  curves, so foreground MAE behaves differently across those image types.

Machine-readable evidence lives in
`outputs/checks/render_similarity.json`,
`outputs/checks/pixel_evidence.json`, and
`outputs/checks/similarity_scorecard.json`.
