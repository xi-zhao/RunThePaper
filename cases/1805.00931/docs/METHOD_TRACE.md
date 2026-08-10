# Method Trace

## MTH001 — Exact finite-chain Floquet construction

- Source: main model equations and supplemental numerical-method section.
- Inputs: `L, J, b, h_1...h_L`.
- Output: the exact `2^L x 2^L` Floquet matrix.
- Steps: enumerate z-basis spins; compute periodic Ising/field phases; form the tensor
  product kick; multiply phases into kick columns.
- Code: `src/kicked_ising/model.py::floquet_matrix`.
- Checks: unitarity and direct-power/eigenvalue SFF agreement.
- Status: verified.

## MTH002 — Disorder-averaged SFF

- Source: supplement, "Numerical methods".
- Inputs: frozen seed, field mean/width, exact finite-chain solver.
- Output: mean and standard error of `K(t)` for every integer time.
- Executed feature method: reduced `L` permits one exact eigendecomposition and power
  sums. The observable is identical to basis propagation.
- Paper-scale method: matrix-free Floquet propagation with two independent
  random-phase trace groups; their real cross product is unbiased for the SFF. Shards
  use coordinate-derived seeds and online moments.
- Code: `src/kicked_ising/reproduction.py::compute_sff_ensemble`,
  `src/kicked_ising/model.py::random_phase_trace_sff`, and
  `src/kicked_ising/paper_scale.py::run_sff_shard`.
- Checks: dense/matrix-free action equality, stochastic small-system mean against the
  exact SFF, field moments, norm drift, independent ensemble splits, and bitwise
  fresh-vs-resumed shard equality.
- Status: feature run verified; paper-scale implementation verified by smoke, final
  ensemble not run.

## MTH003 — Matrix-free dual transfer operator

- Source: main duality equations and supplement numerical methods.
- Inputs: `t, hbar, sigma`.
- Output: `LinearOperator` implementing `T` on `4^t` coefficients.
- Steps: Gaussian replica dephasing; left local Floquet action; right conjugate action.
- Complexity: `O(t 4^t)` memory traffic per matvec, `O(4^t)` storage. Dephasing and
  kick butterflies use bounded row/column scratch rather than auxiliary `4^t` arrays.
- Code: `src/kicked_ising/model.py::TransferOperator`.
- Checks: explicit Kronecker equivalence at `t=3`.
- Status: verified.

## MTH004 — Unit-circle deflation and subunit restarted Arnoldi

- Source: supplement proofs and numerical power-method description.
- Inputs: matrix-free transfer action and formula-derived `±1` operator basis.
- Output: spectral gap and Arnoldi residual.
- Steps: store dihedral operators as permutation maps and exceptional operators as
  low-rank factors; solve the small component Gram system; project each matvec; use
  SciPy Arnoldi for small checks and a five-step, six-basis-slot explicitly restarted
  Arnoldi solver for `t=9..15`; evaluate `1-max|lambda|`.
- Code: `src/kicked_ising/model.py::ProtectedOperatorBasis`,
  `RestartedArnoldiGapSolver`, and `spectral_gap`.
- Checks: full diagonalization for `t<=5`; exceptional-operator residuals at
  `t=6,8,10`; exact protected ranks through `t=15`; restarted-Arnoldi small-spectrum
  equality.
- Status: feature run verified; paper-scale implementation and t=15 memory preflight
  verified, final grid not run.

## MTH006 — Deterministic campaign state and resume

- Inputs: config fingerprint, global realization/point coordinate, seed, shard id.
- SFF checkpoint: online moments, split moments, field diagnostics, next realization.
- Gap checkpoint: one restart vector, iteration/convergence history, parameter
  fingerprint, and vector SHA-256.
- Code: `src/kicked_ising/paper_scale.py`.
- Checks: an interrupted SFF shard is bitwise identical to a fresh run; an interrupted
  gap solve converges to the same gap and residual as a fresh run; changed config or
  corrupted vector is rejected.
- Status: verified at smoke scale.

## MTH005 — Dihedral Gram-rank multiplicities

- Source: main Theorem 1/Table I and supplement even-time constructions.
- Inputs: integer `t`.
- Output: dihedral rank and total `+1/-1` multiplicities.
- Steps: enumerate polygon shifts/reflections; calculate relative permutation cycles;
  form the Hilbert-Schmidt Gram matrix; add only proved exceptional sectors.
- Code: `src/kicked_ising/model.py::transfer_multiplicities`.
- Checks: rank sequence and explicit `t=6,8` operator identities.
- Status: verified, paper scale `t=2..17`.

## Prohibited route

No PDF/EPS/PNG curve digitization, tracing, image fitting or author numerical source
is part of any method. Original figures are comparison-only inputs after numeric hashes
are frozen.
