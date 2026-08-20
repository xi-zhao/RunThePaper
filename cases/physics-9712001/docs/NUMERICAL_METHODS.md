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

## NUM005 — Hermitian comparator and asymptotic probes

The separate Hermitian Hamiltonian `p^2+|x|^N` is diagonalized on a real grid.
Its finite boundary is selected by a fixed potential-height rule, paired grids
measure discretization error, and `N=2..512` tests the square-well limit without
using the paper's plotted points. Eq. (11) is also solved at a declared
logarithmic epsilon grid; the fitted observable is the slope of `log(E)` versus
`log(-log(epsilon))`, not a hand-picked visual trend.

## NUM006 — whole-paper falsification probes

Claims that are not plotted are still executed as first-class numerical
targets. The runner records: spectra of the three opening cubic examples;
exact shifted-oscillator sequences; wedge centers and openings; spectra under
three admissible contour deformations; turning-point residuals and the actual
positive-imaginary branch-cut intersection; an independently bracketed and
resolution-converged first exceptional point; same-parameter Riccati/finite-
difference cross-checks; large-N WKB growth; Airy-Wronskian values; classical
periods; an integrated Riemann-sheet spiral with turning-point passage events;
quantum-merger/event-count correspondence; and exact massive anchors at
N=0,1,2. Every check carries both `target_ids` and `claim_ids`, so no broad
figure target can silently stand in for a missing scientific claim.

## NUM007 — near-N=2 perturbative cross-check

The non-Hermitian first-order perturbation is projected into adjacent
harmonic-oscillator pairs. Gauss-Hermite quadrature at two orders evaluates
the complex-symmetric matrix elements, and a bracketing solve locates the
discriminant zero. Only scalar matrix elements and merger thresholds are
stored; no author matrix, code, or numerical array is used.

## NUM008 — exceptional-point and classical-event repair channel

The first broken/unbroken threshold is found from the sign change of
`Re[(E2-E1)^2]`, not by inserting the paper's 1.42207 value. Four independent
finite-difference resolutions locate and converge the root. The solver
cross-check uses identical N values in Riccati shooting and a sparse matrix
eigenproblem, so paper-table error is never mixed into a solver-agreement
metric.

For the subcritical classical claim, the state is parameterized as
`i*x=exp(q+i*theta)` and theta is left unwrapped. This follows the orbit across
Riemann sheets, records each printed turning-point angle that the trajectory
passes, checks energy conservation, and maps every computed quantum merger
epsilon to the number of classical turning points passed before the escape
ray. This is bounded numerical support for the stated correspondence, not a
pixel or formula-only self-test.
