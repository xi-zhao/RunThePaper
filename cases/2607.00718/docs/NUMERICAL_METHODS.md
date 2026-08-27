# Numerical Methods

## Method Cards

### NUM001

- Target: T001, Figure 1(c).
- Equations/method cards: EQ001 / MTH001.
- Parameters: representative `r=1`; `r_a+r_b=2r`; four asymmetry values.
- Grid: 721 uniformly spaced relative phases.
- Solver: direct vectorized analytic evaluation.
- Tolerance: `1e-11` across four hyperbolic identities.
- Random seed: not applicable.
- Output schema: CSV columns `delta_theta, delta_r, G`.
- Numerical risks: none beyond floating-point roundoff; the paper leaves the
  absolute representative `r` symbolic.

### NUM002

- Target: T002C, Figure 2(c).
- Equations/method cards: EQ002 / MTH001.
- Parameters: `J=1e-3`, `kappa=8e-5`, `epsilon=1e-4`, `r∈[0,2]`.
- Grid: 1000 points, matching the deposited author arrays.
- Solver: direct closed-form evaluation for cases a, b, and c.
- Tolerance: author-array maximum absolute error below `1e-10`.
- Random seed: not applicable.
- Output schema: CSV columns `r, Ea_over_E0, Eb_over_E0, Ec_over_E0`.
- Validation checks: every author point plus an independent steady-energy
  identity.

### NUM003

- Target: T003, Figure 3(a-d).
- Equations/method cards: EQ002, EQ003 / MTH001.
- Parameters: paper-exact `kappa`, drive, coupling and squeezing intervals.
- Grid: three `220 × 260` maps; four 1000-point fixed-`r` cuts.
- Solver: vectorized closed forms plus analytic coupling derivatives.
- Tolerance: author cuts below `1e-10`; invariant below `1e-11`.
- Random seed: not applicable.
- Output schema: compressed NPZ containing grids, maps, cuts, thresholds, and
  optimum branches.
- Validation checks: author arrays, energy invariant, derivative-zero branch
  classification.

### NUM004

- Target: T004, Figure 4(a-b).
- Equations/method cards: EQ004 / MTH001.
- Parameters: `kappa_a=kappa_b=8e-5`,
  `J=sqrt(kappa_a*kappa_b)/2`, `Gamma=2J`.
- Grid: `401 × 401` map and four 1001-point frequency cuts.
- Solver: direct evaluation of normal and anomalous scattering channels.
- Tolerance: general-to-reduced identity below `1e-11`.
- Random seed: not applicable.
- Output schema: compressed NPZ containing frequency grids, transmission map,
  and line configurations.
- Validation checks: formula reduction, local optimum, peak ordering, and
  explicit old-Zenodo-versus-final-version comparison.
- Numerical risk: the released transmission arrays are stale and therefore
  cannot be treated as a final-paper benchmark.

### NUM005

- Target: TS03, Figure S3(a-c).
- Equations/method cards: EQ002 / MTH001.
- Parameters: the three paper-exact couplings and `r∈[0,2]`.
- Grid: 1000 points per curve, nine curves in total.
- Solver: evaluate absolute `E_i^ss` and independently normalize each branch
  by its formula-derived nonsqueezed baseline `E^ss(J)`.
- Output schema: compressed NPZ retaining the squeezing grid, couplings,
  baselines, absolute energies, and normalized enhancements.
- Validation checks: exact energy identities, unit `r=0` enhancement,
  monotonicity, endpoint ordering, and source-axis semantic consistency.
- Evidence boundary: the source image is consulted only after generation. Its
  printed label conflicts with the visible unit intercepts and is never used
  as a numerical input.

## Efficiency And Reuse Plan

- Baseline implementation: one reusable NumPy model with a thin target runner.
- Main bottleneck: two-dimensional map generation and image rendering.
- Efficient implementation choice: broadcasting and vectorized formulas; no
  per-point Python loop for maps.
- Complexity: linear in the number of plotted grid points.
- Performance bottleneck removed: no master-equation Hilbert-space truncation
  is needed for the closed-form milestone.
- Optional harness promotion candidate: version-mismatch checks for released
  author data.
- Case-specific parts that should not enter the harness: the paper's closed
  squeezing, energy, and scattering formulas.
- Performance evidence: the local Apple M4 profile passes the compute gate; no
  external machine is required.
