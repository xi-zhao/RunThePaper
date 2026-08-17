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
- Status: implemented and verified. The paper-scale run used 1100 XY points;
  covariance invariants, Fourier-grid doubling and the critical Ising/XX slopes
  all pass.

### NUM-XXX — independent finite-chain calculation

- Inputs: N=20, periodic boundary, `Delta=1`, zero field, fixed `S_z=0`, and
  an explicit coupling-sign convention.
- Outputs: ground energy/vector and block entropies for L=1..10.
- Steps: bit-basis sparse Hamiltonian; Lanczos ground state; expansion into the
  full computational basis; Schmidt singular values for each bipartition.
- Checks: Hermiticity, residual norm, translation symmetry, L versus N-L
  entropy symmetry, dense small-N parity, and a second analytic Dicke-state
  calculation for the printed ferromagnetic convention.
- Status: implemented and verified at N=20 (sector dimension 184,756). The
  sector solver agrees with an independently assembled full Pauli-space solver
  at small N and is stable under a tighter Lanczos tolerance.

### REVIEW-MAJ — exhaustive majorization check

- Inputs: generated XY covariance eigenvalues for a declared critical model
  and L range.
- Outputs: every worst partial-sum margin and the responsible index.
- Checks: spectrum normalization, non-negativity, dimension padding, and direct
  small-L density-matrix parity.
- Status: implemented and verified. All 18 declared adjacent-block tests pass;
  the minimum numerical margin is -1.11e-15, within the 1e-10 tolerance.
