# Numerical methods and evidence boundary

## Independent numerical channel

The numerical implementation was written from the paper's equations and
reported parameters. It did not use author code, author-generated numerical
arrays, digitized curves, or figure pixels as numerical inputs. Paper images
were consulted only after generated arrays had been frozen, to diagnose canvas,
axes, typography, line styles, palette, and interpolation.

## Analytic calculation

`run_analytic.py` evaluates the one-photon branches, solves the nonlinear
second-order cumulant fixed points, constructs real-variable Jacobians, and
records physicality and stability checks. The fixed-point search is checked by
residual norms, spin length, covariance positivity, and finite-difference-step
stability.

## Quantum calculation

The three quantum runners use QuTiP to construct the Hamiltonian and collapse
operators, generate seeded Monte-Carlo trajectories, average reduced photonic
density matrices, and compute observables from those matrices. Cutoff tails,
trace errors, density-matrix eigenvalues, Wigner normalization, trajectory-count
drift, and parity leakage are recorded as machine-readable checks.

The shipped arrays are deterministic frozen evidence for the declared seeds and
configuration. The main finite-size jobs use 6–16 trajectories per job rather
than the paper's much larger ensembles, so their role is mechanism and feature
reproduction, not author-data-level equivalence.

## Rendering and scoring

Rendering reads only generated arrays. Pixel comparison is a subsequent audit:
the primary visual metric is foreground-pixel similarity over the declared
numerical figures. Full-canvas similarity is retained as a layout diagnostic
because white background can inflate it. Neither metric can override failed
physics checks or upgrade a reduced computation to paper-exact status.

Machine-readable evidence is available under `outputs/checks/`, including the
formula verification, per-figure science checks, frozen-data hashes, and final
scorecard.
