# Numerical methods

## Provenance boundary

Numerical runners read only independent code and declared parameters. They do not read `raw/`, source figures, digitized curves, or author numerical source code. Generated NPZ arrays are frozen and hashed before the RenderContract stage reads source figures.

## Linear and PBC calculations

- NumPy complex eigensolvers diagonalize independently constructed OBC/PBC matrices.
- PBC traveling-wave stability is obtained by diagonalizing the displayed 2x2 matrix on declared momentum grids.
- The matrix result, not the paper's inconsistent printed closed form, controls the stability map.

## Static OBC calculations

- At `theta=pi`, a real gauge-fixed boundary equation provides residual and Jacobian checks.
- Stable kink profiles are selected by long-time integration of the full complex Eq. (2) from seed 7. Direct root finding alone is not a physical selector because exact but unstable roots exist in the non-normal boundary problem.
- CEP curves use high-kappa attractor selection, nonlinear continuation, and the exact `2N x 2N` real Jacobian.

## Dynamic calculations

- Primary integrator: fixed-step RK4 with `dt=0.05`.
- Seeds, burn times, observation windows, and sampling intervals are declared in the generated checks because the paper does not provide them.
- Lyapunov exponents use the exact tangent equation advanced with the state and periodic QR orthonormalization.
- Particle-hole delays are evaluated with fractional-sample interpolation; no source curve is fitted.

## Phase maps

The local phase-map run uses `N=100`, burn time `3000`, observation time `100`, `dt=0.05`, and seed `101`. It is a coarse basin scan. It is not promoted to the paper's unresolved fine multistable structure.

## Rendering

PNG/PDF/SVG figures are rendered only from frozen NPZ arrays. The separate source-reading script crops predeclared scientific regions and computes SSIM, grayscale MAE, and pixel similarity. It cannot alter parameters or arrays.
