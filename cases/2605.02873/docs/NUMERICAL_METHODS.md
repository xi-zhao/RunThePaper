# Numerical Methods

## MTH001

- Targets: T-FIG001A, T-FIG001B, T-FIG001C, T-FIG001D, T-FIGS001.
- Equations: EQ001--EQ008 as listed per target.
- Paper parameters: \(\lambda=633\) nm, \(L_1=L_2=0.35\) m,
  \(d=500\,\mu\mathrm m\), \(a=250\,\mu\mathrm m\),
  \(X_D=-L_2\lambda/(4d)\), \(y\in[-1.5,1.5]\) mm, and
  \(B=0.02\max R_0\).
- Grid: uniform full-window source samples; fixed Gauss--Legendre quadrature on
  each finite slit. Grid sizes are recorded in every check.
- Boundary conditions: exact finite slit endpoints; no Gaussian or point-slit
  replacement.
- Solver: vectorized deterministic NumPy quadrature and trapezoidal source
  integration.
- Tolerance: convergence and printed-value thresholds are target-specific and
  machine-readable.
- Random seed: not applicable; calculation is deterministic.
- Output schema: CSV numerical arrays plus JSON checks containing parameters,
  timing, metrics, tolerances, and verdict.
- Validation: central finite differences, doubled quadrature order, refined
  source grid, symmetry/positivity/orthogonality checks, and analytic-reference
  comparisons.

## Efficiency And Reuse

- Core model: one case-local `TryModel` implementation shared by all targets.
- Main cost: complex kernel evaluation over source-by-slit quadrature grids.
- Optimization: vectorization in bounded source chunks; no production
  dependency added.
- Scaling: \(O(N_yN_x)\) per slit width with \(O(N_{\rm chunk}N_x)\) working
  memory.
- Case boundary: optical parameters, expected values, plot contracts, and all
  target runners remain under this case.
