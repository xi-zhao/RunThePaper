# Numerical Methods

## Method Cards

### NUM001 — XY correlation matrix and whole-spectrum audit

- Target: T001, T002, T003, T004--T008, T010--T013, T015--T017.
- Equations/method cards: EQ001--EQ004, EQ006--EQ011, NUM-XY.
- Parameters: paper `gamma` and `a`; L=1..20 for Fig. 1 and L=1..40 for Fig. 2.
- Grid or benchmark: uniform midpoint Fourier grid with explicit doubling
  convergence; the `a` grid is declared in config and never inferred from
  pixels.
- Boundary conditions: infinite translation-invariant chain, contiguous finite
  block.
- Solver: NumPy Fourier sums and Hermitian dense eigensolve.
- Tolerance: covariance and convergence tolerances live in the run config.
- Random seed: not applicable; deterministic.
- Output schema: long-form entropy, coefficient-audit, scaling-collapse,
  product-spectrum, labelled occupation-sign, three-rank-semantics, and proxy CSV files plus target-level
  causal diagnoses.
- Validation checks: analytic critical-Ising `g_l`, antisymmetry, physical
  covariance spectrum, quadrature convergence, and expected CFT slopes.
- Numerical risks: the critical phase ratio is undefined at isolated momenta;
  midpoint sampling avoids evaluating them.

### NUM002 — N=20 XXZ exact diagonalization

- Target: T002, T009, and T014.
- Equations/method cards: EQ001, EQ005, NUM-XXX.
- Parameters: N=20, periodic boundary, `S_z=0`; `Delta=1` for the critical
  caption convention and declared `Delta=2` as the noncritical comparison.
  The literal printed and caption-implied coupling signs remain separate.
- Grid or benchmark: all `binom(20,10)=184756` fixed-magnetization basis states.
- Boundary conditions: periodic.
- Solver: sparse Lanczos for critical and easy-axis antiferromagnetic ground
  states; exact two-spin bond-spectrum certificates plus analytic polarized and
  Dicke entropies for the literal ferromagnet. Checkpoint identity includes
  both `Delta` and coupling sign.
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

### NUM004 — atomic whole-paper claim checks

- Target: T004--T017.
- Purpose: keep every quantitative statement independently classifiable rather
  than treating two figures as a proxy for the whole paper.
- Checks: L=1..100 critical scaling, printed coefficient shortcuts and offsets,
  nearcritical successive slopes, fixed-coordinate collapse, N=20 regime
  discrimination, Eq. (20) spectrum identities, three effective-rank
  thresholds, and the explicitly non-paper-exact RG proxy.
- Scientific boundary: T010, T015, and T017 cannot become universal or paper-exact
  from finite execution because the publication omits the required numerical
  definition. T004 separately audits an Eq. (11) sign conflict whose label
  exchange leaves entropy invariant. The 2D/3D area-law citation remains the sole missing-source
  deferral.

## Efficiency And Reuse Plan

- Baseline implementation: direct Fourier quadrature and full-Hilbert XXX
  diagonalization.
- Main bottleneck: the two N=20 XXZ eigensolves, not the covariance calculations.
- Efficient implementation choice: fixed-magnetization sparse basis and reuse a
  single ground vector for all ten bipartitions.
- Complexity or scaling: XY is O(n_a L^3); XXX stores O(N binom(N,N/2)) sparse
  entries and computes one extremal eigenpair.
- Performance bottleneck removed: full 2^20 Hamiltonian construction.
- Optional harness promotion candidate: deterministic fixed-magnetization XXZ
  basis builder after cross-case reuse exists.
- Case-specific parts that should not enter the harness: the Vidal sign-
  convention fork and figure-specific grids.
- Performance evidence: all 27 scientific gates pass; the clean whole-paper
  isolated run completed in 6.720 s and is recorded in the v6 attestation.
