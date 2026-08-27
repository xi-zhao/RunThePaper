# Numerical Methods

## NUM001 — geometry and boundary matrix

- Targets: T001-T003
- Equations: BEM001-BEM003, BEM006
- Geometry: two regular hexagons of side `R=1`; center displacement
  `(1.8R,-0.5R)` from Fig. 4's axes; interior/exterior indices `1.466/1.0`.
  The prose prints `+0.5R`, so this is an explicit publication-variant choice,
  not a hidden paper-exact assertion.
- Discretization: constant straight elements, Gauss-Legendre quadrature off
  diagonal, analytic diagonal limits.
- Fidelity declaration: the production run uses a source-pixel-independent
  circular-fillet representative. The paper explicitly says the result does
  not depend on the particular rounding/discretization and defines the class
  through `N=1600`, `rho/lambda≈0.11`, and `rho/Delta s≈11.2`.
- Checks: normal orientation, matrix shape, circle analytic benchmark,
  `b=lambda_local/Delta s`, and mesh convergence.

## NUM002 — cross-section scan

- Target: T001 / Fig. 5
- Equations: BEM004
- Incidence: 15 degrees to the horizontal side faces.
- Scan: 151 uniformly spaced real `kR` samples in `[20,25]`, plus the printed
  resonance `22.94444` and spurious-solution anchor `23.25`; no source curve is
  digitized and maximum spacing is checked independently.
- Solver: dense complex linear solve at the paper's `N=1600` scale.
- Observable: Fig. 5 stores the optical-theorem estimator from Eq. (22), exactly
  as stated in the paper. The angular integral is retained only as an
  independent consistency check and never substituted into the plotted array.
- Checks: finite residual, nonnegative optical-theorem cross section, agreement
  with the independent angular integral, and exact sampling of the reported
  mode.
- Output: immutable NPZ arrays plus JSON hashes and run parameters.

## NUM003 — resonance, near field, and far field

- Targets: T002-T003 / Figs. 6-7
- Equations: BEM005
- Initial seed: `kR=22.95-0.098i`, explicitly printed in the paper.
- Solver: the printed final resonance is evaluated by smallest-singular-vector
  SVD on four meshes. The independently implemented trace-Newton formula is a
  method check, while Figs. 6-7 use the paper's printed final complex `kR`.
- Near field: boundary-integral reconstruction on a declared Cartesian grid.
- Far field: outgoing asymptotic amplitude on a declared angular grid.
- Shared-data invariant: both panels must consume the same frozen resonance
  wave number and boundary vector; plotting cannot modify either.
- Checks: Newton residual trend, smallest singular value, boundary residual,
  mesh drift of `k_res`, and far-field normalization.

## Efficiency and reuse plan

- Baseline bottleneck: repeated assembly and dense solution of a `2N x 2N`
  non-Hermitian complex matrix.
- Efficient choice: vectorized pair geometry, fixed quadrature nodes, adaptive
  frequency sampling, and coarse-to-fine resonance refinement.
- Scaling: storage `O(N^2)`; a dense solve/SVD `O(N^3)`.
- Reusable module: generic two-dimensional TM constant-element BEM kernels,
  validation, and immutable-result writer.
- Case-specific module: coupled-hexagon geometry, scan interval, and rendering.
- Runner isolation: only `src/`, `scripts/`, and config are copied into the
  run directory. `raw/`, references, EPS, and author data are inaccessible.

## Paper-scale executable channel

- `src/paper_scale.py` adds an explicit count for each of the twelve straight
  and twelve rounded segments while leaving the attested feature BEM module
  unchanged. This permits exactly `N=1600` boundary elements without
  pretending that 1600 is divisible by a uniform twelve-segment map.
- `config/paper_scale.json` freezes four symmetric 122-element sides, eight
  121-element sides, and twelve 12-element corner arcs. The resulting
  `2N=3200` matrix and both printed rounding ratios are checked before any
  production matrix is allocated.
- The same config carries a first-class `publication_parameter_resolution`:
  prose `+0.5R`, Fig. 4 `-0.5R`, selected figure value `-0.5R`, and
  `paper_exact_claim_allowed=false`. This keeps a source contradiction from
  being laundered into a parameter-exact status.
- `scripts/run_paper_scale.py` stores one config-hashed checkpoint per scan
  point and near-field row, plus resonance-mesh and far-field checkpoints.
  Fig. 6 and Fig. 7 cannot diverge because both load the same final resonance
  checkpoint.
- `--validate-only` checks the full configuration without a dense solve;
  `--smoke` runs the same stages at 48 elements. Neither mode is production
  evidence, and neither changes target status before the paper-scale
  attestation passes.
- Aggregation writes immutable arrays and hashes without importing or carrying
  the renderer. Rendering is a separate post-freeze command, so later changes
  to canvas, axes, fonts, line style, palette, or interpolation cannot
  invalidate the numerical attestation. The numerical runner has no path to
  `raw/`, `references/`, source EPS, digitized curves, or author code/data.
