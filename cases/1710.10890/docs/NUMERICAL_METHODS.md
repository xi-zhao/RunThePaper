# Numerical Methods

## NUM001 — Interaction curves

- Targets: T001--T005
- Method: centered quadratic Lagrange interpolation through three published
  coupled-channel parameter rows.
- Checks: exact table recovery, single `delta_a` crossing, printed `B_c`.

## NUM002 — Universal radial droplet

- Targets: T004--T005
- Equation: EQ005.
- Grid: spherical radius `1e-5 <= r_tilde <= 20`, 1500 initial nodes.
- Solver: SciPy collocation BVP with regular origin and vanishing far boundary.
- Tolerance: `1e-7`; maximum adaptive nodes 30000.
- Stable branch: scalar root in chemical potential for `N_tilde=22.55`.
- Metastability fold: printed `mu=-0.061`, independently yielding 18.649.
- Validation: normalization, zero-energy stable threshold, positive profile,
  monotone tail, and fold recovery.

## NUM003 — Levitating potential

- Target: T006
- Quadrature: 20001 uniform phase points over one modulation period.
- Spatial grid: 1601 points over `[-80,80]` micrometres.
- Derivatives: analytic Gaussian first/second derivatives evaluated under the
  same quadrature.
- Signed display convention: `sgn(-V'')`, matching Fig. S1(c)'s force-gradient
  orientation.
- Validation: central gradient cancels `mg`; curvature has the plotted sign
  and agrees with the supplement's 20 Hz scale.

## NUM004 — Frozen expansion proxy

- Target: T007
- Solver: adaptive `solve_ivp` for six coupled TF scale-factor variables.
- Initial condition: TF ground state using the printed trap frequencies,
  `a=7.5 a0`, and the stated maximum preparation `N=4e5`.
- Final vertical trap: 0 or `2*pi*12` Hz.
- Validation: initial scale factors equal one; free curve exceeds confined
  curve at late times.

This remains the previously attested baseline artifact. It is not substituted
for the paper's stated GPE method.

## NUM005 — Paper-scale 3D GPE campaign

- Targets: T007 method-faithful rerun and T008/Main Fig. 4 code-ready dynamics.
- Initial state: imaginary-time state-2 GPE ground state in the printed
  `(250,240,280) Hz` trap.
- Main Fig. 4: instantaneous 50/50 transfer followed by the two coupled 3D
  GPEs with the printed local two-species LHY derivative; three-body losses are
  disabled as stated by the paper.
- Supplement Fig. S2: single-component mean-field GPE at `a=7.5 a0`, released
  into free space or `2*pi*12 Hz` vertical confinement.
- Propagation: second-order Strang splitting with FFT kinetic half-steps and
  local potential/interaction full-steps.
- Primary profile: `512^3` and `2 us`; Main Fig. 4 uses a `128 um` box
  through `25 ms`, while S2 uses a `224 um` box through `12 ms`.
- Spatial refinement: `640^3` at the same physical boxes and production step.
- Time refinement: `512^3` with imaginary- and real-time steps halved.
- Observable: `2*sqrt(RMS_x*RMS_z)` for Main Fig. 4 and
  `sqrt(7)*RMS_z` for S2.
- Acceptance: norm drift `<1e-4`, outer-10%-shell norm `<1e-4`, dynamic
  refinement gap `<8%`, converged radial reference `<2e-4`, finite/bounded
  observables, and correct free-vs-confined S2 ordering.
- Independent checks: finite-difference derivative of the LHY energy density
  and Pohozaev scaling identity for both radial branches.
- Recovery: atomic task outputs; checkpoints bind the canonical task hash and
  support job-array sharding and restart.
- Parameter limit: both Fig. 4 and S2 use `N=4e5` only as the paper's stated
  maximum-preparation assumption. Exact plotted/calibration atom numbers are
  not published, so production results remain proxy/sensitivity evidence.

## Efficiency And Reuse Plan

- The frozen T001--T007 baseline is CPU-sized; universal radial profiles are
  solved once and reused across the magnetic-field lane.
- The method-faithful dynamics is a distinct GPU workload. Four 80 GiB GPUs can
  process the twelve independent production/refinement tasks with concurrency
  four; local execution is intentionally limited to the same-path NumPy smoke.
- The isolated runner writes structured NPZ data before any rendering.
