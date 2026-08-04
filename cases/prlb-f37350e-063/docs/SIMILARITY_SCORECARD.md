# Similarity scorecard

The primary presentation diagnostic compares only predeclared scientific/theoretical regions after independent arrays are frozen.

- mean grayscale pixel similarity: **86.56/100**;
- mean scientific-region SSIM: **0.5330**;
- source pixels used in numerics: **false**;
- author numerical code used: **false**.

The two image metrics answer different questions. Grayscale similarity is high partly because backgrounds and large structures align; SSIM is lower because axes, aspect ratios, typography, density, and some partial scientific structures are not paper-identical. Neither metric can override a failed physics assertion.

Per-target pixel scores are stored in `../outputs/checks/pixel_metrics_summary.json`. The normalized scorecard additionally caps source-figure-only visual evidence and penalizes partial panel coverage. It is deliberately separate from the case lifecycle state.
