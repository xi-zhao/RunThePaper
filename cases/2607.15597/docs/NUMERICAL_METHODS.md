# Numerical Methods

## Core implementation boundary

`src/` owns scientific objects and invariants. Plotting and file I/O
stay in `scripts/run_reproduction.py`. This keeps a paper figure from
becoming the place where business/physics rules are hidden.

## NUM001 — single-ion gate (T001)

- Parameters: `q=1/(2 sqrt(2))`, `t/T in [0,2]`, 801 points, motional vacuum.
- Solver: closed-form displacements/phases; no time-step integrator.
- Observable: rotated-basis populations and Wootters concurrence.
- Checks: exact loop closure, trace/positivity, CZ phase, `C(T)=1`, `C(2T)=0`.
- Risk: source convention for clockwise/counter-clockwise loop orientation is
  physically immaterial.

## NUM002 — chain scaling (T002)

- Grid: integer `N=1..100`.
- Model: EQC007 duration surrogate plus EQC005 decay; technical floor `1e-3`.
- Status: reconstructed; exact optimized-duration vector is unavailable.

## NUM003 — architecture scaling (T003)

- Grid: 241 logarithmic distances and 241 operation counts.
- Hybrid and photon timing use disclosed values; QCCD is an affine source-plot
  reconstruction.
- Storage panel follows the caption's `2pT/Nops`, not the contradictory source
  raster. The discrepancy is an explicit check, not silently styled away.

## NUM004 — ion-chain modes and closure (T007)

- Equilibrium: minimize dimensionless harmonic-plus-Coulomb potential.
- Modes: eigenvalues/eigenvectors of its analytic Hessian.
- Toggle schedule: 25 positive durations represented by softmax logits;
  alternating amplitudes `+1,-0.84`; scipy least-squares with deterministic
  multi-starts.
- Acceptance: normalized mode frequencies agree with the source to 2%; maximum
  residual displacement below `1e-4` if optimizer convergence permits.
- Source conflict: the `2N+5` rule/Fig. S1 say 25 segments for N=10, while
  Table S4 says 17.

## NUM005 — thermal/circular figures (T008, T011-T014)

- Grid: `nbar=0.1..50`, log-spaced.
- Model: EQC006 feature approximation + EQC005 decay + disclosed technical
  floors; additive small-error approximation.
- Status: analytic feature reproduction, not QuTiP/Lindblad equivalence.

## NUM006 — qLDPC projections (T010)

- Grid: code distance `d=6..30`.
- Solver: direct Fowler power law with paper constants.
- Direct MC markers are reference anchors only and are never labeled as newly
  generated Monte Carlo data.

## Reproducibility

- Randomness: only deterministic optimizer starts in the closure problem;
  fixed seed `260715597`.
- Output: CSV first, figures second, JSON checks last.
- Dependencies: Python standard library, NumPy, SciPy, Matplotlib, pytest.
  No production dependency is added to the repository.
- Expected local runtime: under one minute and far below the 16 GiB memory
  limit; exact qLDPC runs are excluded from this local path.
