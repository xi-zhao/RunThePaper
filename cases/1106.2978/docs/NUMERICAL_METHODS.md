# Numerical methods

The production method builds the printed tridiagonal transfer and vertex
matrices.  Power products are rescaled at every step and carry logarithmic
normalizations; this avoids overflow without changing ratios of observables.
The Delta=1/2 root-of-unity case uses its exact three-state closure.

For whole-paper theorem checks, the same printed auxiliary matrices are also
contracted into the full physical Cholesky operator `S_n`. This permits an
entrywise comparison of `S_n S_n^dagger` with the independent dense stationary
state and direct checks of rank, triangularity, finite auxiliary dimension and
polynomial degree. Complexity is established by an exact band-operation count,
not wall-clock fitting. Exact algebraic discrepancies are kept separate from
numerical convergence claims.

The easy-plane convergence claim is checked in two numerically distinct ways:
from the two leading eigenvalues of the reduced transfer matrix and from a fit
to independently generated finite-size currents.  The `Delta>=1` infinite-rank
claim is not inferred from one finite matrix rank.  Instead, the implementation
constructs a family of shifted triangular minors whose analytic diagonal stays
nonzero at arbitrary requested order, and verifies finite probes against the
printed hopping amplitudes.

The independent method constructs the 2^n-dimensional Hamiltonian, both edge
jump operators, and the 4^n-dimensional Liouvillian.  A trace row replaces one
linear equation and the resulting dense system is solved directly.  This code
does not call the transfer implementation.

No parameter is optimized against the source figure.  The only interpolations
are for rendering smooth formula-generated curves after the data freeze.
