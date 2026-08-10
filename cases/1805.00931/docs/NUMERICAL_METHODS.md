# Numerical Methods

## Method Cards

### NUM001 — Exact finite-chain SFF

- Target: T001/T002.
- Equations/method cards: EQ001--EQ004, EQ008--EQ009; MTH001--MTH002.
- Parameters: `J=b=pi/4`, `L=8`, `hbar=0.6`, three paper widths, 128 realizations.
- Grid or benchmark: all integer `t=1..1000`; paper/reduced COE curves.
- Boundary conditions: periodic spin chain.
- Solver: exact dense Floquet eigenspectrum, followed by eigenvalue power sums.
- Tolerance: unitary eigenvalue drift recorded; no fitted tolerance.
- Random seed: `180500931`.
- Output schema: one CSV row per `(sigma,t)` with mean, SEM, references and scale fields.
- Validation checks: nonnegative finite SFF, unitarity, disorder moments, deterministic hash.
- Numerical risks: small-ensemble fluctuations and finite-`L` plateau.

### NUM001P — Paper-scale finite-chain SFF

- Target: T001/T002 code-ready final campaign.
- Paper parameters: `L=15`, `hbar=0.6`, three widths, 9490 realizations, every
  integer `t=1..1000`.
- Solver: exact matrix-free Floquet action with two independent groups of 256
  random-phase probes; the group cross product is unbiased for `|tr(U^t)|^2`.
- Sharding: 949 deterministic realization shards per width; coordinate-derived RNG
  seeds make results invariant to scheduling order.
- Output/acceptance: online mean/SEM, split-ensemble agreement, field moments, state
  norm drift, checkpoint hashes, and exact parameter disclosure.
- Numerical risks: trace-estimator variance and long aggregate GPU time. The final
  result is accepted only after all 9490 samples and split checks complete.

### NUM002 — Matrix-free transfer gap

- Target: T003/T004.
- Equations/method cards: EQ005--EQ007, EQ009; MTH003--MTH004.
- Parameters: left `t=5..9`, right `t=7`, printed mean fields and width interval.
- Solver: protected-sector projection plus deterministic ARPACK Arnoldi.
- Tolerance: residual `<=3e-6`; maximum observed `2.9013544e-6`.
- Random seed: `264101`.
- Output schema: gap, leading modulus, protected rank, residual and runtime per point.
- Validation checks: gap bounds, `sigma=0` unitary limit, positive-disorder contraction,
  small-`t` full diagonalization.
- Numerical risks: exponential vector dimension and clustered eigenvalues.

### NUM002P — Paper-scale transfer gap

- Target: T003/T004 code-ready final campaign.
- Parameters: left `t=9..15`, right `t=13` and six mean fields, declared uniform
  `sigma=0..0.8` reconstruction grid.
- Solver: implicit permutation/low-rank protected projector plus five-step,
  six-basis-slot explicitly restarted Arnoldi on CuPy complex64 arrays.
- Tolerance: two seeds, Ritz residual `<=3e-5`, leading-modulus disagreement `<=2e-3`.
- Checkpoints: one restart vector with config fingerprint, iteration history and hash.
- Memory: conservative t=15 preflight peak 72 GiB under the 80 GiB contract.
- Numerical risks: clustered leading modes and accelerator memory fragmentation; both
  are stop conditions rather than reasons to weaken acceptance.

### NUM003 — Transfer multiplicities

- Target: T005.
- Equations/method cards: EQ005, EQ008; MTH005.
- Grid: every integer `t=2..17`.
- Solver: exact dihedral permutation Gram rank plus derived exceptional-sector counts.
- Output schema: rank, `+1/-1` multiplicities and sector label.
- Validation checks: every printed Table I cell is tested after generation.

## Efficiency And Reuse Plan

- Baseline implementation: direct Floquet matrices and explicit transfer matrices.
- Main bottleneck: transfer-space dimension `4^t` and dense Floquet diagonalization.
- Efficient implementation choice: feature-scale eigendecomposition; paper-scale
  matrix-free unbiased trace estimation; implicit protected projection; bounded-memory
  restarted Arnoldi; tiny permutation Gram matrices for multiplicities.
- Complexity or scaling: feature Figure 2 `O(R 2^(3L))`; paper Figure 2
  `O(R q t L 2^L)` for `2q` probes; Figure 3 `O(k t 4^t)` with six stored Krylov
  vectors; Table I `O(t^4)` at small matrices.
- Performance bottleneck removed: the long analytic curve no longer recomputes a
  Gram rank at every time.
- Optional harness promotion candidate: profile analytic reference builders separately
  from stochastic/iterative solvers.
- Case-specific parts that should not enter the harness: kicked-Ising protected-sector
  algebra.
- Performance evidence: v3 completed in `249.43 s`; paper-route smoke completed in
  `0.43 s`; paper preflight and all 21 unit/integration tests pass. Final A100 numerics
  remain unexecuted.
