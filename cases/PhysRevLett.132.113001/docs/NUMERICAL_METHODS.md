# Numerical Methods

## NUM001 — Stark diagonalization

- Targets: T001, T002, T009, T010
- Method: dense Hermitian diagonalization of 19x19 and 23x23 matrices; branch
  continuity is chosen by successive eigenvector overlap.
- Cross-checks: exact parabolic eigenvalues, \(F^2\) ratio, all-finite output.
- Cost: below one second; CPU is more appropriate than A100.
- Boundary: high-n hyperfine factors and higher-order QED terms are approximate.

## NUM002 — Calculated spectrum

- Target: T003
- Grid: 2001 detuning points from -50 to 50 MHz.
- Method: six analytic asymmetric components with independently calculated
  Stark centers; normalize only the total intensity.
- Boundary: measured spectrum and fit covariance are missing author data.

## NUM003 — Metrology arithmetic

- Targets: T004-T008, T011-T012
- Method: analytic normalization, printed regression equations, quadrature and
  40-digit `Decimal` arithmetic.
- Boundary: point-level Fig. 5 arrays are unavailable; only theoretical bands
  and printed tables are reproduced.

## NUM004 — Experimental reanalysis contract

The code validates four exact CSV schemas, hashes each file, then performs
weighted regressions and the 525-estimate weighted mean.  It fails closed while
the author arrays are absent.  Synthetic data and source-image digitization are
explicitly disallowed.
