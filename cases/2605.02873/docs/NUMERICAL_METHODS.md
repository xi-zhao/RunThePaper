# Numerical Methods

## Shared Physical Solver

`src/try_fresnel.py` is the single case-local implementation of EQC001-EQC008.
It evaluates each slit on its exact finite interval with independent
Gauss--Legendre quadrature. The main final grid uses 1,201 source points and
192 nodes per slit. A second 1,801-point, 256-node calculation is used only as
a convergence check.

The solver returns the physical state
\((E_0,R_0,M_t,M_f,g_t,g_f)\). Full Fisher information, optimized codes, toy
codes, coded Fisher matrices, retention eigenvalues, and the width scan are
pure functions derived from that state. Original PNGs and paper reference
numbers do not appear in the solver.

## Target Isolation

`scripts/run_target.py --target <id>` requires both
`PRAGENT_GUARDED_TARGET_ID=<id>` and
`PRAGENT_GUARDED_STAGE=final_reproduction`. Each invocation writes only the
CSV, figure, scientific check, and run record belonging to that target.

## Independent Checks

- Fig. 1(a): intensity nonnegativity, unit normalization, denser-grid
  convergence.
- Fig. 1(b): analytic moment derivatives versus direct central finite
  differences of the field intensity.
- Fig. 1(c): nuisance zero mean, pair orthogonality, unit noise norm,
  fringe-oscillation count, and convergence.
- Fig. 1(d): full/coded Fisher matrices and four retention values versus paper
  text, projection bounds, and convergence.
- Fig. S1: analytic narrow-slit suppression, strict monotonicity, all five
  independently generated values versus Supplementary Table S1, and
  convergence.

Paper values are introduced only after independent generation in the
target-specific comparison/check functions.
