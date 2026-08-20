# Numerical Methods

## Zigzag ribbon diagonalization

- Targets: T001 and the lattice part of T003.
- Deterministic widths: 16, 20, 24, 28, 32; main width 32.
- Momentum grid: 401 points over `0 <= k_x a <= 2 pi`.
- Intrinsic calculation: two conserved-spin 64 by 64 Hermitian blocks.
- Finite-Rashba probe: one full 128 by 128 spinful block with
  `lambda_R/t=0.02`.
- Outputs: all eigenvalues and edge weights, plus width-level feature metrics.

The zero-Rashba armchair implementation uses independent widths 20, 32 and 44
and checks the central half-gap and edge localization at `k=0`.  The finite-
Rashba TRIM diagnostic uses widths 56, 68 and 80.  The authoritative spectral-
flow channel instead uses zigzag widths 48/58/64 and armchair widths 80/104/128.
It first samples the full spinful bulk Brillouin zone, then searches only inside
those band edges, subtracts the exact uniform-state edge-weight baseline and
tracks the resulting states over nested 192-768 point momentum grids.  A
separate 121-point zigzag
calculation at `t2=0` covers the full analytic flat-band interval, including
endpoint delocalization and an edge-weighted zero-energy DOS ratio.

### Finite-ribbon convergence

The width and grid are publication-underspecified.  They are selected by the
analytic bulk-gap and adjacent-width convergence gates, never by source-image
fitting.  The formal width-32 gap error is 2.44% and the 28-to-32 change is
1.08%.

### Finite-Rashba probe

The paper gives only `lambda_R<Delta_so`, not a finite strip parameter set.
`lambda_R/t=0.02` is therefore a declared parameter-consumption probe: changing it must
change the spectrum while preserving Hermiticity, time reversal and Kramers
degeneracy.  Six ratios across `lambda_R/Delta_so=1` are tested in the legacy
TRIM diagnostic.  Separately, every subcritical ratio is tested over the full
Brillouin zone for both orientations and three increasing widths.  Acceptance
requires localized states on both edges, a branch spanning the bulk midgap and
stable extrema/midgap distance on two nested grids.  All 30 production
combinations pass.  No value is fitted to source pixels.

### Finite-Rashba Kubo boundary

The paper delegates its conserved-spin-current definition to another work.  A
24 by 24 full-Brillouin-zone quadrature therefore evaluates only the
conventional symmetrized current and records `[H,s_z]`.  This is a declared
response proxy: it can test continuity and parameter consumption, but it cannot
be promoted to the paper's exact finite-Rashba response.

## Berry-flux topology

- Targets: T004-T005.
- Grid: periodic 31 by 31 reciprocal-lattice mesh.
- Solver: dense two-band eigendecomposition and normalized Fukui links.
- Checks: integer quantization, opposite spin sectors, sign reversal under
  `t2 -> -t2`, spin Hall coefficient and flux pump.
- Finite-cylinder check: 17 levels per branch across 101 flux values, with
  circumference and ramp factors 20 relative to the correlation/adiabatic
  scales.  These finite choices are declared convergence parameters.

## Scattering and transport

- Targets: T006-T009.
- S-matrix: singular-value null space of the printed linear TR constraint.
- Disorder: 32 deterministic scalar-potential ensembles of length 512,
  propagated with the exact helical first-order transfer operator.
- Transport: explicit `(spin,destination,source)` transmission tensor and
  terminal-current solve; no returned conductance constants.
- Interaction: explicit Grassmann operator/TR transform, field and derivative
  dimension counting, a seven-temperature by three-coupling Kubo-kernel sweep,
  and a complete weak-perturbation inventory.

## Symmetry and parallel field

All 64 sublattice-valley-spin Pauli products are tested against both kinetic
Dirac matrices and the printed discrete symmetries.  A uniform parallel field
is tested directly only through its edge Zeeman avoided crossing.  The separate
two-segment 81 by 81 bulk path uses a T-odd intervalley bridge: its nonzero
translation residual is recorded, so it is evidence for generic broken-T
adiabatic connectivity, not evidence that a uniform field generates that
microscopic mass.

The paper does not specify the other symmetry-allowed terms in its claimed bulk
path.  A second candidate remains primitive-cell periodic and combines lattice
Rashba, uniform `s_x` Zeeman and staggered `sigma_z` fields.  Coarse/fine BZ
grids are retained as diagnostics, but acceptance is an active falsification:
three deterministic differential-evolution searches minimize the direct gap
continuously in path coordinate and reciprocal momentum.  The mass-rotation
segment closes below `1e-16 t`, so this candidate is rejected and the published
mechanism remains `publication_underspecified`.

## Material scales and RG

- Targets: T010-T013.
- SI constants: `scipy.constants`.
- External values not printed in the paper: `a=2.46 angstrom`, `vF=1e6 m/s`;
  both are marked not paper-exact.
- First star: explicit three-corner plane-wave matrix in the full
  sublattice-valley-spin basis before SI conversion.
- RG coefficients: Gauss-Legendre logarithmic radial shell and independent
  angular quadrature, projected by momentum/mass finite differences.  A
  five-shell sweep checks logarithmic slopes without reusing `1/4` or `1/2`.
- Screening: an independently integrated neutral four-flavor interband
  Lindhard function supplies `Pi(q)`.  Angular and doubled-cutoff convergence
  are checked before the screened potential is constructed; the analytic 1/4
  coefficient and `1/q` law are acceptance tests, not generator inputs.
- RG solution: only the independently derived coefficients feed the ODE and
  positive self-consistent half-gap root.

### Claim-level falsification sweeps

All widths, grids, disorder samples, `u/T` values, shell nodes, mass-path points
and finite-cylinder factors not printed by the paper are declared in
`parameter_provenance.json`.  They are selected for convergence, invariants and
active falsification, never by source-image fitting.

## Isolation and complexity

The v11 run contract copies the config, runner and nine declared scientific
modules into a raw/reference-free bundle.  Darwin sandboxing blocks network and
subprocesses, and the Python audit hook records all file access.  The dominant
ribbon cost remains `O(N_k W^3)`; the additional Kubo, shell, disorder and mass
sweeps have explicit fixed grids and remain CPU-minute scale.  The isolated v11
runtime was 243.246548 s, with 666 audited events and zero denied or forbidden
accesses.
