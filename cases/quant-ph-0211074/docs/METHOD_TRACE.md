# Method Trace

## Method Cards

### NUM-XY — clean-room Gaussian covariance calculation

- Inputs: `gamma`, `a` (or the declared XX zero-field limit), integer block
  length, and Fourier quadrature size.
- Outputs: covariance singular values, entropy, and optional product spectrum.
- Steps: midpoint Fourier quadrature; antisymmetric Toeplitz assembly;
  Hermitian eigensolve of `iB`; binary-entropy sum.
- Checks: analytic critical-Ising coefficients, quadrature doubling, covariance
  antisymmetry, `0 <= nu <= 1`, and CFT slope regressions.
- Status: implemented. In addition to both figures, the runner now evaluates
  L=1..100 critical sequences, fixed-coordinate noncritical scaling, complete
  spectra through L=16, retained-weight ranks, and an explicitly non-paper-
  exact RG proxy. Final v5 whole-paper isolated attestation is required after
  every scientific-contract repair.

### NUM-XXX — independent finite-chain regime calculation

- Inputs: N=20, periodic boundary, `Delta=1` or declared noncritical `Delta=2`,
  zero field, fixed `S_z=0`, and an explicit coupling-sign convention.
- Outputs: ground energy/vector and block entropies for L=1..10.
- Steps: bit-basis sparse Hamiltonian; Lanczos ground state; expansion into the
  full computational basis; Schmidt singular values for each bipartition.
- Checks: Hermiticity, residual norm, translation symmetry, L versus N-L
  entropy symmetry, dense small-N parity, the exact negative-sign bond lower
  bound for `Delta>=1`, and analytic polarized/Dicke entropies for the printed
  ferromagnetic convention.
- Status: implemented at N=20 (sector dimension 184,756). Critical and gapped
  checkpoints cannot collide because `Delta` and coupling sign are part of the
  checkpoint identity; a regression test enforces that invariant.

### REVIEW-MAJ — exhaustive majorization check

- Inputs: generated XY covariance eigenvalues for a declared critical model
  and L range.
- Outputs: every worst partial-sum margin and the responsible index.
- Checks: spectrum normalization, non-negativity, dimension padding, and direct
  small-L density-matrix parity.
- Status: implemented and verified. The paper-scale contract enumerates both
  critical models at L=1..16, while explicitly refusing to turn a finite sweep
  into a proof of the all-L quantifier.
