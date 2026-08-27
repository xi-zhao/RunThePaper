# Similarity Scorecard

## Case Score

- Expected normalized score: **91.6/100**
- Expected level: `complete_reproduction`
- Scope: all five frozen theory-numerical figure items
- Generated provenance: `independent_numerics` for every target
- Artifact stage: `final_reproduction` with `paper_exact` parameters

The four main panels are capped at 90 because no author curve arrays are
released; they use verified analytic/textual references plus source-panel
feature comparison. Fig. S1 uses Supplementary Table S1 as an exact reference
and scores 98.

## Per-Target Evidence

| Target | Feature /50 | Numeric /35 | Scope /15 | Effective score | Key evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| T-FIG001A | 50 | 25 | 15 | 90 | Nonnegative unit-normalized curve; cross-grid max difference \(2.81\times10^{-5}\) |
| T-FIG001B | 50 | 25 | 15 | 90 | Moment derivatives vs direct finite differences: \(8.03\times10^{-11}\) relative |
| T-FIG001C | 50 | 25 | 15 | 90 | Noise-metric residual \(2.78\times10^{-17}\); optimized crossings 11/7 vs toy 1/2 |
| T-FIG001D | 50 | 35 | 15 | 90 (analytic-reference cap) | Fisher matrices \(1.12\times10^{-6}\) relative; optimized retention \(7.72\times10^{-9}\) absolute |
| T-FIGS001 | 50 | 33 | 15 | 98 | All five widths; four rows within 0.42%; near-null row differs \(4.25\times10^{-7}\) absolute |

## Important Scientific Boundary

The Fig. S1 value at \(a=20\,\mu\mathrm m\) is independently stable at
\(1.79249\times10^{-5}\), while the rounded paper table gives
\(1.75\times10^{-5}\). Its 2.43% relative difference is driven by the
near-zero denominator; the absolute difference is \(4.25\times10^{-7}\).
This discrepancy is retained in the score and report rather than tuned away.

Pixel fidelity is evaluated separately and does not contribute to this
scientific score.
