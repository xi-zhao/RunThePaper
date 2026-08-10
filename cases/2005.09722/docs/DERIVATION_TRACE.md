# Derivation Trace

## From the stochastic equation to an orbital update

Quadratic hopping and number measurements map Gaussian states to Gaussian
states. Writing the Slater determinant through occupied orbitals `U`, the
single-particle hopping acts from the left. The periodic hopping matrix is
circulant, so its Fourier eigenvalue is `2 cos(k)` and its exponential is
applied exactly by FFT. The paper's first-order diagonal measurement factor is
then multiplied row-wise and QR returns an orthonormal occupied basis. QSD uses
the state-dependent drift (`sigma=1`); QSDc omits it (`sigma=0`).

## Entropy and CFT coefficients

For interval A, `D_A=U_A U_A†`. Each eigenvalue is a fermionic occupation
probability, giving the binary-entropy sum in EQ004. EQ005 is linear in the
chord coordinate, so ordinary least squares yields `c=3*slope` and `s0` without
nonlinear optimization.

## Quantum jumps without author code

The total event rate is constant at `gamma*N`. Between jumps the exact FFT
propagator is used. At a selected occupied site, rotate the occupied orbitals
so one column aligns with that site's row, replace that column by the site
basis vector, and retain the orthogonal columns. Direct algebra yields the
paper's rank-one covariance update; the test suite checks the full matrix.

## Density correlation identity

For a number-conserving Gaussian state, Wick's theorem gives
`<n_i n_j>=<n_i><n_j>-|D_ji|²` for distinct sites. Therefore independently
averaging the first two terms and subtracting must reproduce the direct Fock
signal within stochastic error. This is a scientific cross-check, not a visual
fit.

## Scaling limits

The BKT transforms use the paper's printed `gamma_c=0.31`, `alpha=3.99`, and
`g(L)`. They are applied to generated data without refitting those constants.
At `L≤96` they demonstrate the transformation only; they cannot prove the
thermodynamic jump claimed from `L≤800`.
