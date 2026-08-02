# Scientific and presentation scorecard

The primary score measures scientific numerical evidence, not visual styling.
Each theory-numerical item receives feature, numerical-closeness, and scope
credit only after its formula and generated-data gates pass. Raster comparison
is reported separately and contributes no scientific points.

## Scientific score

| Target | Paper items | Scale | Scientific score | Boundary |
| --- | --- | --- | ---: | --- |
| T001 | Main Fig. 2(b–e), 4 items | feature | 80 | paper geometry; reduced statistics, grids, and `L<=24` transition sizes |
| T002 | Supplement Fig. S2(a–d), 4 items | paper | 80 | author random samples unavailable |
| T003 | Supplement Fig. S3(a–h), 16 upper/lower items | paper | 80 | author seeds unavailable; caption/raster uncertainty conflict recorded |
| T004 | Supplement Fig. S4, 10 items including insets | feature | 80 | four sizes through `L=24` and reduced statistics |
| T005 | Supplement Fig. S5, 7 items | feature | 70 | transition locations pass; fitted `nu(d)` stability remains partial |
| T006 | Supplement Fig. S6(a–c), 3 items | feature | 80 | all paper block sizes, but sizes stop at `L=24` |

The 44-item weighted result is **78.41/100**, classified as
`numerical_feature_reproduction`. All seven scoped claims and ten formula
objects are resolved. Twenty numerical items are at paper scale and 24 are at
feature scale; no unresolved numerical item is removed from the denominator.

## Presentation audit

| Target | Presentation score | Full-image SSIM |
| --- | ---: | ---: |
| T001 | 75.09 | 0.649179 |
| T002 | 62.05 | 0.764540 |
| T003 | 71.90 | 0.736214 |
| T004 | 67.27 | 0.699569 |
| T005 | 67.03 | 0.816190 |
| T006 | 66.45 | 0.882153 |

The aggregate presentation score is **68.30/100**. Remaining differences come
from reduced finite-size branch sets, independent Monte Carlo fluctuations,
font metrics, marker/error-bar rasterization, and line density. The reference
image is bound only after independent numerical evidence passes; no source
pixel or digitized point enters simulation, fitting, or scientific scoring.

Machine-readable records live in
`outputs/checks/similarity_scorecard.json` and
`outputs/checks/presentation_fidelity.json`.
