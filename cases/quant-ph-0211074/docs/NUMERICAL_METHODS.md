# Numerical Methods

## Method Cards

### NUM001 — XY correlation matrix

- Target: T001, T002, T003.
- Equations/method cards: EQ001--EQ004, EQ006, NUM-XY.
- Parameters: paper `gamma` and `a`; L=1..20 for Fig. 1 and L=1..40 for Fig. 2.
- Grid or benchmark: uniform midpoint Fourier grid with explicit doubling
  convergence; the `a` grid is declared in config and never inferred from
  pixels.
- Boundary conditions: infinite translation-invariant chain, contiguous finite
  block.
- Solver: NumPy Fourier sums and Hermitian dense eigensolve.
- Tolerance: covariance and convergence tolerances live in the run config.
- Random seed: not applicable; deterministic.
- Output schema: long-form CSV with target, model, a, gamma, L, entropy, and
  quadrature size.
- Validation checks: analytic critical-Ising `g_l`, antisymmetry, physical
  covariance spectrum, quadrature convergence, and expected CFT slopes.
- Numerical risks: the critical phase ratio is undefined at isolated momenta;
  midpoint sampling avoids evaluating them.

### NUM002 — N=20 XXX exact diagonalization

- Target: T002 and the Hamiltonian-sign review.
- Equations/method cards: EQ001, EQ005, NUM-XXX.
- Parameters: N=20, Delta=1, lambda=0, periodic boundary, `S_z=0`, and both
  explicitly labeled signs.
- Grid or benchmark: all `binom(20,10)=184756` fixed-magnetization basis states.
- Boundary conditions: periodic.
- Solver: sparse Lanczos for the antiferromagnetic ground state; analytic Dicke
  Schmidt probabilities for the literal ferromagnetic representative.
- Tolerance: eigen-residual and entropy-symmetry thresholds live in config.
- Random seed: deterministic Lanczos start vector with a recorded seed.
- Output schema: one row per convention and block length, plus run/check JSON.
- Validation checks: dense N<=10 parity, residual, L/N-L entropy symmetry,
  energy bounds, and the printed-sign ground-state degeneracy.
- Numerical risks: treating the caption's intended antiferromagnet as the
  literal printed Hamiltonian would hide a scientific discrepancy; outputs keep
  these objects separate.

### NUM003 — density-spectrum majorization

- Target: T003.
- Equations/method cards: EQ002, EQ003, EQ006, REVIEW-MAJ.
- Parameters: declared Ising and XX critical models and L range.
- Solver: exact product-spectrum enumeration and sorted cumulative sums.
- Output schema: model, L, minimum margin, worst partial-sum index, tolerance,
  and verdict.
- Validation checks: normalization, non-negative weights, and direct small-L
  density-matrix parity.

## Efficiency And Reuse Plan

- Baseline implementation: direct Fourier quadrature and full-Hilbert XXX
  diagonalization.
- Main bottleneck: N=20 XXX eigensolve, not the covariance calculations.
- Efficient implementation choice: fixed-magnetization sparse basis and reuse a
  single ground vector for all ten bipartitions.
- Complexity or scaling: XY is O(n_a L^3); XXX stores O(N binom(N,N/2)) sparse
  entries and computes one extremal eigenpair.
- Performance bottleneck removed: full 2^20 Hamiltonian construction.
- Optional harness promotion candidate: deterministic fixed-magnetization XXZ
  basis builder after cross-case reuse exists.
- Case-specific parts that should not enter the harness: the Vidal sign-
  convention fork and figure-specific grids.
- Performance evidence: to be filled from smoke and final isolated runs.
