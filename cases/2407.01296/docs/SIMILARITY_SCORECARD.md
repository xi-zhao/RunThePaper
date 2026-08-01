# Similarity scorecard

Public status: **full scientific reproduction; main-text pixel-registered, not identical**.

The scientific result is **35/35 numerical subplots and 8/8 scoped claims**.
All 15 formula cards and all 15 recorded execution runs pass their gates, and
no source-paper pixels enter generated data.

The separate pixel-layout evidence score is **89.27/100** over four registered
main-text targets (Fig. 2 full layout, Fig. 2(c), Fig. 3, and Fig. 4). It is not
a scientific-completion score and it is not a claim that 89.27% of pixels are
identical. The first-release evidence score `88.39` is retained in JSON only as
historical metadata.

| Target | Scientific status | Provenance | Pixel diagnostic |
| --- | --- | --- | ---: |
| Fig. 2(a–d) | passed | all panels independent; source assets post-generation only | SSIM `0.7958` |
| Fig. 3(a–b) | passed | independent GBZ numerics | SSIM `0.6969` |
| Fig. 4(a–f) | all six panels passed | independent numerics | SSIM `0.5823` |
| Supplementary Fig. S2(a–d) | passed | independent formulas/numerics; author arrays post-generation only | deferred: reference panels not separately frozen |
| Supplementary Fig. S4(a–b) | passed | independent finite numerics and exact middle-root TDL | deferred: reference panels not separately frozen |
| Supplementary Fig. S5(a–f) | passed | independent Eq. (S27)/Eq. (10) numerics | deferred: reference panels not separately frozen |
| Supplementary Fig. S6(a–b) | passed | independent winding numerics | deferred: reference panels not separately frozen |
| Supplementary Fig. S7(a–b) | passed with source-count correction | independent biorthogonal numerics; author arrays post-generation only | deferred: reference panels not separately frozen |

Fig. 4 panel SSIM values are `0.9107`, `0.5717`, `0.7042`, `0.4353`, `0.4181`,
and `0.4946` for panels a–f. Every panel has the exact target canvas dimensions
and passes its scientific acceptance checks, but none reaches the strict
pixel-exact threshold of `0.95`.

The main-text and supplementary numerical evidence chains are complete and
fully independent. There is no known formula-numericalization gap in the
declared scope. Pixel decisions are recorded for all 35 subplots: 18 main-text
subplots have passing registered evidence and 17 supplementary subplots are
explicitly deferred until source-PDF panels are separately cropped and frozen.
Unreported state-selection, boundary-discretization,
random-seed, probe-grid, and rendering choices still limit pixel identity in
Fig. 3 and several Fig. 4 panels.
