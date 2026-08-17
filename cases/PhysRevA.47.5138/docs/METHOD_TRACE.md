# Method Trace

## NUM-QPD — finite-spin Husimi distribution

- Inputs: S=20, printed initial coherent state, twisting family and mu.
- Output: frozen theta/phi axes, six complete Q arrays and computed Qmax values.
- Method: construct exact spin-S amplitudes; apply the unitary without time
  stepping; evaluate coherent-state overlaps on a 121x241 spherical grid.
- Checks: state norm, Q range, direct printed Qmax landmarks, independent
  `expm` evolution and grid refinement.
- Status: implemented, paper-parameter run attested, all checks passed.

## NUM-VAR — minimum variance campaign

- Inputs: 19 physical spins from S=1.5 through S=100.
- Output: exact OAT/TACT minima, optimal mu, CSS and asymptotic references.
- Method: scalar minimization of the OAT closed form; reused spectral TACT
  evolution and exact 2x2 covariance minimization.
- Checks: CSS limit, nonnegativity, OAT formula versus direct moments, Hermitian
  generator, independent matrix exponential, search interior and refinement.
- Status: implemented, paper-parameter run attested, all checks passed.

## RENDER-ONLY — frozen-data presentation

- Inputs: the eight SHA256-locked scientific datasets.
- Output: paper-like orthographic sphere projections and the log-log scaling plot.
- Allowed changes: canvas, axes placement, font, line style, palette,
  interpolation and camera.
- Forbidden changes: physical parameters, numerical arrays or source-pixel input
  to scientific calculations.
- Status: passed; all seven scientific regions meet the render policy.
