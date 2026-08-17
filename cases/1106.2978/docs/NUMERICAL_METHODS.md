# Numerical methods

The production method builds the printed tridiagonal transfer and vertex
matrices.  Power products are rescaled at every step and carry logarithmic
normalizations; this avoids overflow without changing ratios of observables.
The Delta=1/2 root-of-unity case uses its exact three-state closure.

The independent method constructs the 2^n-dimensional Hamiltonian, both edge
jump operators, and the 4^n-dimensional Liouvillian.  A trace row replaces one
linear equation and the resulting dense system is solved directly.  This code
does not call the transfer implementation.

No parameter is optimized against the source figure.  The only interpolations
are for rendering smooth formula-generated curves after the data freeze.
