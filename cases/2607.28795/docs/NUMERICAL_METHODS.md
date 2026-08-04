# Numerical Methods

## Method Cards

### NUM001 — finite-group mitten-code constructor

- Target: T001, Tables I/VI algebraic columns.
- Equations/method cards: Q001-Q003, Eqs. (1)-(4).
- Parameters: all eight SmallGroup IDs and four three-element supports from
  Table XIII.
- Discrete representation: exact GAP 4.16.0 / SmallGrp 1.5.4 multiplication
  tables in the paper's declared zero-based `Elements(G)` order.
- Solver: vectorized binary RREF and exact inversion over `GF(2)`.
- Tolerance: exact; every residual is binary zero or nonzero.
- Output schema: one JSON row per code with ranks, `n,k`, rate, check weights,
  pivot ranks, canonical weights, and invariant results.
- Validation checks: CSS commutation, row weight 9, full ranks, 1/5 rate,
  square invertibility, kernel membership, and delta pairing.
- Numerical risk: a paper/GAP element-order inconsistency cannot be hidden by
  floating-point tolerance; singular pivots are reported as such.

### NUM002 — resource-count identities

- Target: T002, Table V.
- Equation card: Q004, Eq. (E15).
- Grid: eight group orders times `d_rep={5,7,9,11}`.
- Solver/tolerance: exact integer arithmetic.
- Output schema: 32 CSV rows.
- Validation check: `n-X-Z=|G|` for every row.

### NUM003 — bounded sQetch

- Target: T003, reduced-scale Fig. 8 / Algorithm 1.
- Equation cards: Q005-Q006.
- Benchmark: reconstructed `n=150,200` code matrices; 80 sketch trials and 8
  full-nullspace-RREF baseline trials per code.
- Random seed: `260728795`.
- Solver: sampled null-space rows, random column permutation, binary RREF,
  inverse permutation, and opposite-null-space logical test.
- Validation: a separate 500-trial Steane test must recover distance 3;
  inclusion-exclusion probabilities must be bounded and monotone.
- Non-claim: the baseline is our transparent full-nullspace RREF, not the
  unpublished QDistRnd implementation; the run is not paper-scale.

### NUM004 — real-time arithmetic

- Target: T004, Table X.
- Equation card: Q007, Eq. (I1).
- Inputs: rounded stage fractions and times printed in Table X.
- Solver: exact formula evaluation in double precision at `T_cyc=1 ms`.
- Output: per-stage utilization/contribution plus per-experiment mean latency.
- Validation: all mean and worst-stage utilizations stay below one and all
  reconstructed mean latencies stay below one cycle.
- Numerical risk: comparison to the printed last digit requires a disclosed
  rounding tolerance because the upstream cells are rounded.

## Efficiency And Reuse Plan

- Baseline implementation: explicit dense binary matrices and readable RREF.
- Main bottleneck: repeated row reduction, not group-table generation.
- Efficient implementation choice: NumPy row-wise XOR and vectorized regular
  permutation matrices; no new production dependency.
- Complexity or scaling: the largest bounded matrix is `390 x 975`, well
  inside local memory; the intentionally skipped workloads are dominated by
  trial count, not matrix size.
- Performance bottleneck removed: group multiplication is frozen once instead
  of repeatedly calling GAP during the isolated numerical run.
- Optional harness promotion candidate: the general GF(2) and group-algebra
  helpers after another independent paper validates their conventions.
- Case-specific parts that should not enter the harness: mitten block layout,
  Table-XIII supports, and Table-X stage inputs.
- Preflight performance evidence: all four bounded targets complete in about
  one second on the local M4.
