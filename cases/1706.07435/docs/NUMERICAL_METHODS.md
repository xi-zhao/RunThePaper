# Numerical Methods

## Method Cards

### NUM001 — canonical exceptional point (T002)

- Target: Main Fig. 2(a–c).
- Equations/method cards: EQC004, EQC007, MTH001.
- Parameters: `H=sigma_+ + kx sigma_x + ky sigma_y`; loop radius 1;
  `kx=0` cut.
- Grid: 721 loop points, `181×181` surface grid, 801 cut points.
- Boundary conditions: none; local 2×2 momentum-space problem.
- Solver: closed-form complex square root with phase-unwrapped continuous
  branches, cross-checked against direct eigendecomposition.
- Tolerance: eigenvalue-set mismatch `<1e-10`; endpoint branch-swap error
  `<1e-10`; fitted EP exponent within `0.01` of `1/2`.
- Random seed: not applicable.
- Output schema: loop CSV, surface NPZ, cut CSV, JSON scientific checks, PNG.
- Numerical risks: principal-square-root branch cuts must not be mistaken for
  physical discontinuities; branch continuity is tracked explicitly.

### NUM002 — remaining targets

- T001/T004 use continuation of a nonlinear domain-wall matching root.
- T003 uses only closed phase-boundary and EP-position formulas.
- T005 diagonalizes `80×80` complex cylinder matrices over `k_y`.
- T006 reuses MTH001 and fits the two hybrid-point exponents.

## Efficiency And Reuse Plan

- Baseline implementation: vectorized NumPy for 2×2 formulas; dense LAPACK for
  the small `80×80` cylinder matrices.
- Main bottleneck: domain-wall root continuation, not the EP formulas.
- Efficient implementation choice: generate structured arrays once and render
  from those arrays; never recompute inside plotting functions.
- Complexity or scaling: T002/T003/T006 are linear in grid size; T005 is
  `O(N_k n^3)` with `n=40` and is still minute-scale on CPU.
- Performance bottleneck removed: analytic eigenvalues avoid per-grid Python
  eigensolver calls while direct diagonalization remains a sampled check.
- Optional harness promotion candidate: continuous complex-square-root branch
  tracker and unordered eigenvalue-set comparator.
- Case-specific parts that should not enter the harness: paper Hamiltonians,
  captions, palettes, and camera angles.
- Performance evidence: recorded after each target run.
