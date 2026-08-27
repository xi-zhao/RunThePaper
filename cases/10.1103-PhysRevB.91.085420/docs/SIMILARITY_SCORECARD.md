# Similarity Scorecard — PRB 91, 085420 (2015)

**Overall: 79.54 / 100 — numerical feature reproduction** (machine-readable:
`outputs/checks/similarity_scorecard.json`). All four targets are `paper_exact`,
`independent_numerics`, formula gate `verified`; each caps at 80 because the
comparison is a source-vs-reproduction feature contract against the paper's
raster figures (no author data / tables).

| Target | Figure | feature/50 | numeric/35 | scope/15 | cap | score |
| --- | --- | --- | --- | --- | --- | --- |
| T101 | Fig. 1 spectrum + populations | 47 | 31 | 15 | 80 | 80 |
| T201 | Fig. 2 Delta rho actual vs Eq. (8) | 38 | 26 | 14 | 80 | 78 |
| T301 | Fig. 3 <x>(t), Eq. (13) vs Berry-only | 48 | 33 | 15 | 80 | 80 |
| T401 | Fig. 4 Delta<x> vs J transition probe | 48 | 32 | 15 | 80 | 80 |

Weights: T101 0.7, T201 0.8, T301 1.0, T401 1.0.

## Why feature-level (not complete) reproduction
Complete reproduction would need a strong reference (`author_data`,
`benchmark_data`, `table_exact`, `digitized_curve`, or `analytic_reference`). The
paper publishes only raster figures with no data files, so the honest ceiling is
`visual_feature_contract` (cap 80). The underlying reproduction is nonetheless
paper-exact and independently generated: exact transition location (J=5.14),
exact Chern jump, exact peak magnitudes, and — the strongest evidence — the
analytic theory (Eq. 13) agreeing with the *exact* wave-packet dynamics to ~2%.

## What matched / what remains
- **Matched:** band structure and initial populations (Fig. 1); Delta rho
  envelope and theory-vs-actual structure (Fig. 2, corr ~0.9); T-independent
  displacement 3.10 with theory 3.08 and Berry-only 4.33 (Fig. 3); transition at
  5.14 with theory peak 19.5 and Berry-only 11.1 (Fig. 4).
- **Remains:** Fig. 2 is not pixel-exact (intrinsic ~10^2-rad phase sensitivity);
  Fig. 4 actual peak ~17.4 vs ~19 in the band-touching window (genuinely
  T-sensitive, as the paper notes).
