# Numerical Methods

## NUM001: zero-mode quadrature

- Target: `T_BENCH`.
- Equations: EQ001-EQ003.
- Parameters: diagnostic `lambda=0.04`, `V=1`; 120 logarithmic `K^2` points
  from 0.08 to 8.
- Solver: SciPy adaptive quadrature after dimensionless rescaling.
- Tolerance: absolute and relative `1e-12`.
- Random seed: none; deterministic.
- Output: `outputs/data/idx10_analytic_audit.json`.
- Validation: direct moments versus Gamma formulas; monotonic regime check.

## NUM002: symbolic asymptotics

- Target: `T_BENCH`.
- Equations: EQ004-EQ005.
- Solver: exact SymPy series and algebraic solve.
- Output: strings embedded in the same audit JSON.
- Validation: expected correction and source expressions.

## Efficiency

The complete audit runs in under one second after environment startup and uses
negligible memory. A100 execution is scientifically unnecessary; GPU kernels
would only add transfer and environment complexity to one-dimensional
quadrature and symbolic algebra.
