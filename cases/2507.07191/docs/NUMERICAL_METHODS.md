# Numerical Methods

## Method Cards

### NUM001 — high-precision dual solution

- Target: T001, PRL-Bench idx 91 Tasks 1-7
- Equations/method cards: EQ001-EQ008
- Parameters: `E=(0,1,2,4,7,11)`, `M=(4,9,16,25,36,49)`, `m=2`
- Grid or benchmark: frozen PRL-Bench commit `f37350e`, JSON index 91
- Boundary conditions: scalar dual domain `nu<E1`
- Solver: bracketed bisection of the strictly decreasing `h'(nu)` at 100
  decimal digits; inverse-square weights are then normalized directly
- Tolerance: root interval below `1e-70`; acceptance residuals below `1e-40`
- Random seed: not applicable
- Output schema: one CSV row per energy level, one JSON gate record, one PNG
- Validation checks: raw benchmark SHA, source/topic identity, stationarity,
  normalization, active compression constraint, primal-dual equality, SciPy
  SLSQP agreement, HM support bound, nonconstant log slopes, exact coarse groups
- Numerical risks: an unconstrained root finder can jump across the `E_i` poles;
  the implementation uses the paper's concavity proof to maintain a bracket

## Efficiency And Reuse Plan

- Baseline implementation: generic constrained minimization over six `p_i`.
- Main bottleneck: none; correctness and provenance dominate runtime.
- Efficient implementation choice: reduce to the paper's one-dimensional dual.
- Complexity or scaling: each derivative evaluation is `O(k)`; bisection is
  `O(k log(1/tol))`.
- Performance bottleneck removed: no multidimensional iterative optimizer on
  the primary path.
- Optional harness promotion candidate: none yet; this is domain-specific.
- Case-specific parts that should not enter the harness: stable-rank equations,
  frozen idx91 inputs and gold tolerances.
- Performance evidence: recorded by `outputs/checks/idx91_reproduction.json`.
