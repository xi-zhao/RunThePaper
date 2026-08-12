# Numerical Methods

## Scientific object

The numerical state is a half-filled pure fermionic Gaussian state on a periodic
chain.  It is represented by an `L x (L/2)` occupied-orbital matrix `Q`; the
one-body projector is `G = Q Q†`.  This is the smallest state model that closes
under both the paper's quadratic long-range hopping and continuous local number
monitoring.

## NUM001 — monitored Gaussian trajectories

- Targets: T001–T009.
- Source: Main Eqs. (1)–(2), Eqs. (4a,b), Supplement Eqs. (7)–(9).
- Initial state: the printed half-filled Néel product state.
- Boundary condition: periodic ring with minimum lattice distance.
- Hamiltonian: `h_sm = 1/d(s,m)^p` for `s != m`, with zero diagonal.
- Evolution: symmetric unitary/measurement split step.  Translation invariance
  makes the unitary step an exact FFT phase multiplication.  The normalized
  Ito equation gives the diagonal measurement multiplier
  `exp[xi_s - gamma (1-<n_s>) dt]`; QR restores an orthonormal occupied basis.
- Randomness: independent Gaussian measurement increments, with immutable
  condition seed bases and a non-overlapping seed stride.
- Observables: Gaussian subsystem entropy; positive plotted correlation
  `|G_xy|^2`; literal connected covariance `-|G_xy|^2`, retained separately for
  the paper audit.
- Fits: CFT chord-length central charge, the printed mixed entropy ansatz, the
  printed two-term correlation ansatz, and direct log-log slopes.
- Outputs: one CSV and one PNG for each T001–T009, plus ensemble diagnostics and
  a hash manifest.
- Required invariants: particle number `L/2`, `Q†Q=I`, `G†=G`, and `G²=G`.
- Main risk: the paper omits the time step, stationary-time rule, trajectory
  count, finite-ring distance convention, fit weights, and random seeds.  These
  settings are independently converged and remain `reconstructed`, never
  `paper_exact`.

## NUM002 — dark-state and RG cross-checks

- Targets: analytic lanes for T002, T003, T007 and paper review.
- Source: Main Eqs. (3), (6)–(10), Supplement Eqs. (10)–(23).
- Method: independent infrared-kernel quadrature, closed-form dark-state
  exponents `a=p+1/2`, `b=3/2-p`, and numerical integration of the printed RG
  equations.
- Checks: `a+b=2`; the nonanalytic kernel crosses to `q²` at `p=3/2`; both RG
  flow and kernel scaling select relevance for `p<3/2`.
- Purpose: these checks do not replace trajectory data.  They provide an
  independent scientific lane and expose source inconsistencies.

## Scale profiles

| Profile | Conditions | Trajectories | Largest L | Purpose |
| --- | ---: | ---: | ---: | --- |
| smoke | bounded | bounded | 12 | formula, schema, and code-path check |
| feature | 168 | 672 | 96 | local feature evidence for all targets |
| paper-scale smoke | 58 | 58 | 400 | scheduler, checkpoint, aggregate, and resume check |
| paper-scale | 450 | 37,440 | 1600 | printed-size production candidate on A100 |

The paper-scale runner checkpoints each condition atomically, binds every
checkpoint to both configuration and implementation SHA-256 values, assigns
conditions to exactly 32 shards, and refuses aggregation when any condition is
missing or stale.

## Efficiency and reuse

- CPU reference: NumPy/SciPy complex128.
- A100 path: Torch complex128 batched FFT and QR, with NumPy parity in the
  unitary limit.
- Dominant cost: repeated QR of an `L x L/2` orbital matrix.
- Memory policy: process a bounded trajectory batch; store only averaged
  observables and condition checkpoints, never full time histories.
- Reuse boundary: the Gaussian solver and checkpoint pattern are reusable;
  phase labels, target aggregation, and fit contracts remain case-local.
