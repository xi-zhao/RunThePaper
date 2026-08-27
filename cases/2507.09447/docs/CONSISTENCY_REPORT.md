# Consistency Report

## Current State

| Level | Count | Meaning |
| --- | ---: | --- |
| paper-scale feature match | 3 | Fig. 3–5 pass all configured scientific gates. |
| strict pixel match | 0 | Exact canvas, but SSIM remains below 0.95. |
| not in scope | 4 | Fig. 1–2 and Fig. S1–S2. |

## Per-Target Consistency

| Target | Scientific result | Pixel result | Main residual |
| --- | --- | --- | --- |
| Fig. 3 | classification, density support, and both scaling laws pass | SSIM `0.7721` | unpublished state windows/seeds and non-normal ED sensitivity |
| Fig. 4 | PBC support and winding sectors pass | SSIM `0.7735` | density microstructure and source layout |
| Fig. 5 | contour shrinkage and `W_c=2.1` pass | SSIM `0.8521` | unpublished alpha integration/selection details |

## Numerical Stability Decisions

- Finite spectra and Fig. 5 alpha use the ordinary ED path that matches the paper's
  stated numerical observable.
- Fig. 3(d) uses a banded sparse-LU `log|det(E-H)|/L`; large non-normal OBC
  eigenvalues are not used for this convergence observable.
- Fig. 3(b) uses a radius-0.95 diagonal similarity gauge only to stabilize selected
  eigenpairs, then maps right eigenvectors back to site space.
- The thermodynamic reference averages 32 independent transfer runs of length
  one million; standard errors are approximately `3.28e-5` and `3.01e-5`.

## Claim Boundary

The case supports independent reproduction of the paper's main numerical claims at
the reported ED scale. It does not support a source-pixel identity claim.
