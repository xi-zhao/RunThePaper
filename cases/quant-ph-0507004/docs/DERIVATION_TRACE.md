# Derivation trace

Starting from Eq. (1), use
`J_x^2-J_y^2=(J_+^2+J_-^2)/2`. The only nonzero off-diagonal element is

`<m+2|H|m> = lambda/(2N) sqrt[(j-m)(j+m+1)(j-m-1)(j+m+2)]`.

Thus the two m-parity blocks are real symmetric tridiagonal matrices. This is
an algebraic reduction, not an approximation.

The classical coordinate map gives `{mu,phi}=2/N`, so `hbar_eff=2/N`.
Stationarity yields `mu_0=0` below lambda=1 and
`mu_0^2=1-lambda^-2` above it, together with the printed ground energy.
Differentiating the WKB action gives `Delta E=2pi/T`. The saddle at `K=-1`
has a logarithmically divergent period and produces Eq. (12). At lambda=1 the
quadratic coordinate term vanishes; the quartic oscillator has
`T(E)~E^-1/4`, hence `E_k~k^(4/3)N^-1/3`.

For the super-scar quantization test, Eq. (16) at `K=-1` has the two roots
`mu=-1` and `mu=1+2/[lambda cos(2phi)]`. The second root is physical between
the turning angles `phi_0=acos(-1/lambda)/2` and `pi-phi_0`. Twice the area
between these roots is the total two-lobe action. With `hbar=2/N`, the printed
WKB rule predicts `k+1/2=N S_sep/(4pi)` without fitting the quoted indices.

For the ordering paragraph, `mu` is diagonal in the `J_z` basis and
`cos(2phi)` shifts `m` by two. Anticommutator and sandwich placements of
`1-mu^2` therefore give two explicit real-symmetric tridiagonal operators.
They make the otherwise unspecified ordering choice testable without claiming
that either one was the authors' hidden prescription.

For complex coupling, the tridiagonal determinant obeys a three-term
recurrence. Differentiating that recurrence with respect to energy produces an
independent recurrence for `partial_E det(H-E)`. Their simultaneous zeros are
algebraic double-root candidates. A retained exceptional point must also show
a scale-small direct eigenvalue gap, agreement between the candidate energy
and pair center, and the expected ill-conditioning of the eigenvector basis.

`EQUATION_CARDS.json` pins every numerical formula and its code reference.
