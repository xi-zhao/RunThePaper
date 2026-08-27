# Numerical Methods

## Method Cards

### MTH001 — Stable proper-time quadrature

- Targets: T001 and T002
- Equations: EQC002–EQC007
- Parameters: \(m_0=0,0.5,1,1.5\); paper-exact displayed ranges
- T001 grids: 301 Landau points on `[0,30]`; 240 correction points on `[0.1,12]`
- T002 grid: 250 points on `[0.1,25]`
- Solver: vector-valued adaptive Gauss–Kronrod quadrature after
  \(u=\log\tau\)
- Plate sum: direct at small \(\tau\), Jacobi/Poisson-resummed at large
  \(\tau\)
- Hyperbolic factors: exponentially scaled to avoid overflow
- Relative quadrature tolerance: \(2\times10^{-9}\)
- Random seed: not applicable; the calculation is deterministic
- Output: `fig2_energy_contributions.csv` (2,164 rows) and
  `fig3_energy_ratio.csv` (1,000 rows)
- Independent oracle: positive modified-Bessel \(K_1\) sums
- Maximum representation discrepancy: `2.0875e-11`

## Efficiency And Reuse Plan

- Baseline: direct proper-time integral definitions from the paper
- Main risk: slowly convergent Gaussian mode sum and large exponential arguments
- Efficient choice: Poisson transform plus vector integration
- Scaling: linear in the number of requested \(\alpha_0\) grid points, with a
  short exponentially convergent auxiliary sum
- Paper-scale data generation: about 0.05 s per target on the Trial host
- Reusable candidate: the stable Gaussian mode-sum helper
- Case-local logic: physical prefactors, sector definitions, limits, and all
  formula-error diagnostics

## Validation Sequence

1. exploratory Bessel-versus-quadrature benchmark;
2. guarded final data generation;
3. sign, monotonicity, ordering, identity, and limit checks;
4. guarded rendering from accepted CSV;
5. registered scientific and pixel comparison.
