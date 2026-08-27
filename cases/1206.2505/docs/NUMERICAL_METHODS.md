# Numerical Methods

## Integrable thermodynamic channels

Fisher and work targets use deterministic quadrature with `1601` and `2401`
momentum points. Work rates use a 401-point conjugate-field grid and monotone
saddle interpolation. These methods scale linearly with grid size and need no
GPU.

## Local-observable channels

The upper trajectory and postselection panels use sparse Krylov evolution of an
`N=12` spin chain. The bottom order-parameter panel uses the paper's stated
Pfaffian route at `N=256`, distance 48. Only a `96 x 96` covariance submatrix is
factorized per time, so the method avoids the exponential spin Hilbert space.
Production checks `N/r = 128/24, 192/36, 256/48`.

## Ramp channel

For an arbitrary continuous across-critical ramp, the endpoint occupations
retain opposite signs at `k=0` and `k=pi`; continuity therefore guarantees at
least one half-occupied mode. This is the reproduced theorem and requires no
single ramp parameter set. Two-component modes are additionally evolved by
analytic midpoint exponentials over 401 momenta. Linear and smoothstep
protocols are declared reconstructions used only to falsify the mechanism.

## Reproducibility

- deterministic grids; no random seed;
- isolated run with network and subprocess blocking;
- output hashes frozen before rendering;
- exact-spin and Majorana implementations provide independent cross-checks;
- no author code, author arrays, digitized curves or source pixels.
