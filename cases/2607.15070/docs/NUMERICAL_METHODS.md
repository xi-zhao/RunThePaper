# Numerical Methods

## Method Cards

### NUM001

- Target: T001, paper Figure 2(a,b).
- Equations/method cards: EQC002-EQC006; MTH001.
- Parameters: `m_0={0,0.5,1,1.5}`; left `alpha_0=0..30`; right
  `alpha_0>0..12`; paper normalization `8 pi^2 L^3/A`.
- Grid or benchmark: deterministic dense display grid; all claim-relevant
  masses and full paper axes.
- Boundary conditions: encoded by `j=1,2,...` Poisson image sum for two
  Dirichlet plates.
- Solver: positive modified-Bessel series; original proper-time quadrature for
  independent checkpoints.
- Tolerance: Bessel-argument cutoff 42 (production) and 46 (convergence
  check); adaptive quadrature relative tolerance `2e-9`.
- Random seed: not applicable; calculation is deterministic.
- Output schema: tidy CSV columns
  `target_id,panel_id,alpha0,m0,normalized_energy,series_id`.
- Validation checks: analytic zero-coupling Landau values, quadrature
  agreement, tail stability, monotonic suppression, mass ordering, correction
  divergence.
- Numerical risks: cancellation is absent because all magnitudes are
  positive; underflow at very large Bessel arguments is harmless and occurs
  below the tail bound.

### NUM002

- Target: T002, paper Figure 3.
- Equations/method cards: EQC002-EQC004, EQC006-EQC007; MTH001.
- Parameters: `m_0={0,0.5,1,1.5}`; `alpha_0>0..25`; full paper axes.
- Solver: independently recompute both positive series within the T002
  authorization, then form `1+S_c/S_L`.
- Output schema: tidy CSV columns
  `target_id,panel_id,alpha0,m0,energy_ratio,series_id`.
- Validation checks: `R>1`, monotone decrease over the rendered range,
  explicit algebraic ratio identity, direct-quadrature checkpoint, approach
  to unity.

## Efficiency And Reuse Plan

- Baseline implementation: direct adaptive quadrature for every curve point.
- Main bottleneck: nested quadrature over a slowly converging image sum.
- Efficient implementation choice: analytically integrate each positive
  exponential term to `K_1`, then truncate by Bessel argument.
- Complexity or scaling: deterministic finite positive sums; required term
  count falls approximately as `1/alpha_0` and exponentially with image index.
- Performance bottleneck removed: quadrature is retained only at a few
  independent checkpoints.
- Optional harness promotion candidate: none during this frozen Trial.
- Case-specific parts that should not enter the harness: Casimir integrals,
  asymptotic corrections, target axes and plotting styles.
- Performance evidence: recorded in
  `outputs/checks/T001_scientific_checks.json`,
  `outputs/checks/T002_scientific_checks.json`, and `PERFORMANCE_PROFILE.md`.
