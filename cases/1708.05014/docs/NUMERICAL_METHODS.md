# Numerical Methods

## NUM001 — Symmetric-Sector Quantum Dynamics

- Targets: T001–T015.
- Equations: EQ001–EQ005.
- Representation: spin `S=N_b/2`, Hilbert dimension `N_b+1`, Liouville dimension
  `(N_b+1)^2`.
- Solver: sparse `expm_multiply` for dynamics, sparse trace-constrained stationary
  solve, dense spectrum at `N_b=16`, Arnoldi leading modes for scaling.
- Initial state: all spins along `+x`.
- Tolerances: eigen solver `1e-9`; accepted residual `2e-6`; stationary residual
  `2e-8`.
- Validation: trace preservation, density-matrix checks, eigenpair residuals, monotone
  finite-size trends, and nonempty output schemas.
- Main risk: non-Hermitian eigensolvers become memory/time intensive at paper scale.

### Paper-scale execution variant

- Dynamics is split by `N_b` and then into 50-new-sample time blocks.  A checkpoint
  retains only the final density vector, accumulated magnetization, trace diagnostics,
  and expanded-config hash.  A small-N test proves block propagation agrees with the
  monolithic `expm_multiply` path.
- Full spectra are independent `N_b=36`/coupling jobs using SciPy dense LAPACK.  The
  smoke preflight matches the complete complex spectrum against NumPy with optimal
  eigenvalue assignment.
- Leading spectra are immutable `(phase,N_b)` or `(N_b,coupling)` ARPACK jobs.  Every
  result records convergence and the maximum eigenpair residual before aggregation.
- The full campaign contains no PDF, image, reference-curve, author-code, author-array,
  or network input.

## NUM001B — Exact Shifted-Jump NESS Backend

- Targets: T011–T012.
- Identity: the master equation can be written
  `L rho=(kappa/S) D[S_-+i omega_0 S/kappa] rho`.
- For nonzero drive, the shifted jump `J` is invertible and
  `rho_ss proportional to (J^dagger J)^-1`.
- Algorithm: construct columns of the lower-bidiagonal `J^-1` in logarithmic scale,
  normalize their Gram weights by log-sum-exp, and form a positive semidefinite density
  matrix on only the `N_b+1` symmetric spin states.
- Independent checks: compare the full density matrix, moments, and variances against
  the trace-constrained Liouvillian solve at small N; then evaluate the paper-scale
  density residual against the independently assembled `(N_b+1)^2` Liouvillian.
- Acceptance: residual `<=2e-8`, trace error `<=2e-8`, Hermiticity error `<=2e-10`,
  nonnegative Gram weights, and passing direct/alternative parity.
- Scientific boundary: this derived backend is executable and cross-checked, but a
  successful run does not resolve which S2-right statistic the source intended.

## NUM002 — Thermodynamic Semiclassical Dynamics

- Targets: thermodynamic part of T001/T009 and T016–T024.
- Equations: EQ006–EQ007.
- Solver: adaptive DOP853 on the unit sphere.
- Time contract: `0..100`, 801 samples for phase portraits.
- Initial conditions: deterministic 12-trajectory grid.
- Tolerance: maximum norm drift below `2e-6`; observed `2.1657e-8`.
- Validation: symbolic and numerical conservation of `mx^2+my^2+mz^2`, plus direct
  evaluation of the conserved field and its branch-cut argument.
- Main risk: the paper's displayed trajectory density is not numerically specified;
  a denser independent grid needs a new frozen numerical run.

The paper-scale variant uses 48 deterministic equal-area initial conditions and 1601
time samples per S5/S7 panel.  Those coordinates are independent formula-generated
presentation samples, not recovered author data.  S6 evaluates the conserved field
and branch argument directly on one grid and integrates trajectories independently on
another path.

## NUM004 — Campaign Orchestration And Acceptance

- Config: `config/paper_scale.json`; smoke overlay:
  `config/paper_scale_smoke.json`.
- Public entrypoint: `scripts/run_paper_scale.py`.
- Job contract: immutable `(family,N_b,coupling-or-panel)` result plus config/result
  hashes; 215 paper jobs and 28 smoke jobs.
- Resume: completed jobs are skipped only when both hashes match.  Dynamics additionally
  resumes inside a job.  Changed config and corrupt/missing results fail closed.
- Aggregation: runs only after every job is valid and produces 11 CSVs, backend parity,
  24 per-target acceptance rows, machine contract, run summary, and frozen manifest.
- Review boundary: acceptance explicitly emits no paper assessment.  Stable mismatches
  remain under protocol-v2 and need paper-exact convergence plus two independent
  cross-checks before any `paper_error_candidate` consideration.

## NUM003 — Post-Freeze RenderContract

- Input: the 11 frozen generated CSVs and declarative render configuration.
- Allowed: canvas, axes, fonts, lines, palette, interpolation, and crop.
- Forbidden: changing physical parameters, numerical arrays, solver output, or target
  membership.
- Validation: compare all data hashes before and after rendering.

## Efficiency And Reuse

- The symmetric spin sector replaces a `2^N` Hilbert space with `N+1` states.
- Sparse propagation and leading-mode Arnoldi avoid dense Liouvillian work except for
  the deliberately reduced full spectrum.
- The generic reusable boundary is the isolated-run/frozen-data/render separation;
  the boundary-time-crystal equations remain case-local.
