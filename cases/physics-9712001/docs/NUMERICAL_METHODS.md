# Numerical Methods

## NUM001 — contour finite differences

Use second-order centered differences for the chain-rule Hamiltonian on the
smooth contour in `DERIVATION_TRACE.md`. Dirichlet endpoints are placed deep in
the decaying wedges. Sparse shift-invert eigenvalue solves return the low-energy
complex spectrum. Paper-scale output includes paired resolutions so convergence
is measured rather than assumed.

For `1<N<4` and for every massive Fig. 3 target, the real axis already lies in
the admissible asymptotic region and is used directly. For the massless
`N>=4` tail, the smooth anti-Stokes contour is required.

## NUM002 — Riccati shooting

The massless ground state near `N=1` is ill-conditioned in ordinary double-
precision matrix diagonalization. Integrating the logarithmic derivative with
an adaptive high-order ODE solver avoids amplitude overflow and imposes the
paper's origin patch condition directly. Domain and tolerance convergence are
recorded for every Table II row.

## NUM003 — analytic comparators

- Eq. (5) generates all WKB entries in Table I.
- Eq. (11) generates all asymptotic entries in Table II via scalar root finding.
- `E_n=(2n+1)sqrt(m^2)+1/(4m^2)` checks each Fig. 3 family at `N=1`.
- `E_n=2n+1` checks the massless solver at `N=2`.

## NUM004 — figure sampling

The authors do not publish their N grids. The reproduction declares dense
physical grids plus all printed critical/table points. Sampling is never fitted
to the EPS markers and is therefore `reconstructed_sampling`, while Hamiltonian
parameters remain paper-exact.
