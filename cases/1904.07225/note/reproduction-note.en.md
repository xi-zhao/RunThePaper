# Adaptive mapping of spatially varying qubit noise

Gupta et al. use binary qubit measurements to infer a spatial phase map. A two-layer particle filter tracks phases and correlation lengths. Its uncertainty drives the choice of the next measurement location. We implemented the published equations and compared adaptive and uniform measurements on three synthetic fields and a six-ion readout. [Published paper](https://doi.org/10.1038/s41534-020-0286-0)

## Recalculation

The full audit addressed 35 numerical panels through new calculations or reanalysis of public data. Under the printed SSIM definition and per-budget retuning, the square-field comparison favored NMQA at eight of ten sampled budgets. Within the overlap of observed errors, the largest interpolated budget ratios were 1.75 for the square field and 1.49 for the six-ion readout. The six-ion maximum was 1.35 under the first-passage rule. The calculation did not recover the approximately 20-fold and threefold caption values.

We reclassified 25,500 published camera frames. A newly fitted cross-validated random forest achieved 98.87% label agreement with the release and a largest six-site phase difference of 0.033 rad. The reanalysis recovered the decreasing phase profile. [Pinned upstream data](https://github.com/qcl-sydney/nmqa/tree/810268706582fc81ac93733a3dc7660388f44e98)

The pinned code uses the variance of the estimated map twice in its SSIM denominator. We also isolated a coordinate indexing discrepancy and a different Gaussian exponent in its β likelihood. At λ₁ = λ₂ = 1, a two-site example with equal nonzero phases retains biased virtual messages with weight 1/2, so the stated convergence needs additional assumptions. [Derivation](../docs/DERIVATION.md)

## Scope

This is a partial reproduction. Historical simulation trajectories, filter configurations and plotting revisions are needed to resolve the efficiency gap. The original fitted forests and the exact Figure 4a frame selection are also unavailable. The package includes independent simulation outputs, computed curves and scalar checks. Use the upstream links for the camera archive and label bank. [Rerun instructions](../docs/NUMERICAL_METHODS.md) · [Missing inputs](../docs/DATA-AVAILABILITY.md)
