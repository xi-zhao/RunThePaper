# Numerical Methods

## NUM001 - finite spectra and profiles

- Targets: T001, T003, T005
- Model: single-band 3-domain Laurent Hamiltonian with lengths `58,41,87`.
- Solver: dense complex eigendecomposition at `N=186`; no random seed.
- PBC curves: uniform `k` mesh evaluated directly from each `h_alpha(exp(ik))`.
- Winding regions: characteristic-root counts, not raster extraction.
- Checks: characteristic residual, normalized eigenvectors, interface-localization
  direction versus positive relative winding, and open-chain constituent-union distance.

## NUM002 - Ronkin and GBZ

- Targets: T002, T004
- Roots: polynomial coefficients after multiplying by `beta^s`, sorted by modulus.
- Constrained minimum: exhaustive pairwise breakpoint intersections of the
  convex piecewise-linear root/Jensen form.
- Spectrum/GBZ: residuals of the explicit Case-I and Case-II equations.
- DOS: common central-difference Laplacian for Ronkin and diagonal potentials.
- Checks: Ronkin slope/winding agreement, finite flat-region versus collapsed
  examples, GBZ characteristic residual, DOS support correlation.

## NUM003 - flux winding

- Target: T003
- Solver: eigenvalues along a closed uniform flux mesh; determinant phase is
  accumulated as the sum of eigenvalue phases relative to each base energy.
- Check: winding is integer within phase-discretization tolerance and the
  nonzero region is bounded by traveling-class spectrum.

## Efficiency And Reuse Plan

- Root arrays are vectorized over the energy grid; each polynomial has at most
  four roots.
- The 186-dimensional eigensystem is computed once and reused by Figs. 2-S2.
- Ronkin minima use a finite analytic candidate set instead of a nested
  optimizer.
- Expected wall time is minutes on the local M4; GPU transfer would add
  complexity without reducing the dominant small-polynomial work.
- The Laurent/root/Ronkin primitives are reusable, while this paper's plotting
  layout and representative-state policy remain case-specific.
