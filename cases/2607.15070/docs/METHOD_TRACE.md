# Method Trace

## MTH001 - Stable proper-time quadrature

- Source: paper Eqs. (25), (27), (28); independent numerical reconstruction.
- Role: evaluate the two infinite sums and improper integrals without
  truncating a slowly convergent plate-mode sum.
- Inputs: positive \(\alpha_0\), non-negative \(m_0\), contribution selector.
- Outputs: dimensionless \(\mathcal E_L\), \(\mathcal E_c\), and their ratio.
- Status: `verified`.

### Algorithm

1. Substitute \(u=\log\tau\), turning \((0,\infty)\) into a smooth finite
   integration window. The tails are double-exponentially small.
2. Evaluate
   \(S(\tau)=\sum_{j\ge1}e^{-j^2/\tau^2}\) directly for small \(\tau\).
3. For large \(\tau\), use the Jacobi/Poisson identity
   \[
   S(\tau)=\frac{\sqrt\pi\tau-1}{2}
   +\sqrt\pi\tau\sum_{k\ge1}e^{-\pi^2k^2\tau^2}.
   \]
4. Use exponentially scaled algebra for both hyperbolic denominators so large
   \(\alpha_0\tau^2\) never overflows.
5. Integrate all \(\alpha_0\) values for one mass as a vector with adaptive
   Gauss-Kronrod quadrature.
6. Cross-check selected points against the independently derived positive
   \(K_1\) sums in EQC004.
7. Generate CSV data first, run scientific checks second, and render only from
   the accepted CSV third.

### Contracts

- Input contract: the runner must receive an explicit T001 or T002 and the
  same ID in `PRAGENT_GUARDED_TARGET_ID`.
- Output contract: T001 writes only `fig2_*` artifacts; T002 writes only
  `fig3_*` artifacts.
- Error contract: adaptive quadrature relative tolerance \(2\times10^{-9}\);
  Bessel cross-check relative difference at most \(2\times10^{-6}\).
- Provenance: all generated values are `independent_numerics`.

### Code

- `src/casimir_effective_mass.py`
- `scripts/reproduce.py`
- `scripts/build_comparisons.py`
