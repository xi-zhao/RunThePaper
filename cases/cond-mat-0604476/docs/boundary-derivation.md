# Finite hard walls, the conserved modes, and the historical test

Fixed cond-mat/0604476v2 explicitly uses a periodic lattice for its displayed
theory but hard walls for its numerical tests (Hamiltonian paragraph). These
are not identical finite Hamiltonians. Let h_O be the open hopping matrix and
h_P its periodic or antiperiodic counterpart. Their difference is a rank-two
end-link operator. For a periodic plane-wave projector Q_q=|q><q|,

    [h_O,Q_q] = [h_O-h_P,Q_q],
    ||[h_O,Q_q]||_F^2 = 2(<q|h_O^2|q> - <q|h_O|q>^2).

The second identity follows by expanding the squared Hilbert-Schmidt norm of
the commutator with a rank-one projector; it is an independent check of the
boundary-operator derivation. Thus periodic plane-wave occupations are not
exact conserved charges of the finite hard-wall problem. Its conserved charges
are the standing-wave occupations with U_xm=sqrt(2/(L+1)) sin(pi*x*m/(L+1)).
The corresponding maximum-entropy construction is the same source principle,
using the actual Hamiltonian's charges rather than transplanting its periodic
formula literally. No interaction, observable or new physical model is added.

There is an exact no-quench control already inside the source range: Lin=L.
The initial covariance C0 is the spectral projector onto the N lowest h_O
modes, so [h_O,C0]=0. Their charges are exactly 0 or1, lambda=+/-infinity;
the hard-wall GGE is exactly the initial pure state and every observable agrees
for all times. A distinct trigonometric derivation gives

    C0(x,y) = (1/(L+1)) sum_{m=1}^N
       [cos(k_m(x-y)) - cos(k_m(x+y))].

The second, boundary-dependent Hankel term is not removed by increasing time.
Replacing C0 by W diag(diag(W^dagger C0 W)) W^dagger removes mode coherences
in a different basis and in general gives a nonstationary mixed Gaussian
state for h_O. Local smallness of an end-link correction is not a uniform
bound on the momentum peak, a sum of Jordan-Wigner string correlations.
The new control evaluates the actual L600,N30 endpoint and increases the
periodic Gaussian correlation cutoff from360 to the complete distance599.

## Meaning of the original size-range check

The source says its GGE prediction is successful over Lin=N..L. It does not
promise a uniform five-percent error at t=3000, pointwise convergence of a
finite quasiperiodic system, or equality of two finite boundary prescriptions.
The original declared check asks for representative sizes and disclosure of
finite-time deviations and convergence; it explicitly is non-exhaustive.
The prior six sizes and all three fixed times/window controls remain unchanged.

The source-level judgment is therefore conditional finite-source support for
the appropriate hard-wall conserved-mode GGE, with observed residuals stated,
not a uniform accuracy theorem. The earlier reproducer-imposed <5% t3000 test
is a separate declared variant: it fails at Lin30 with 6.0265%, and remains a
decisive discrepancy, not a pass obtained by averaging or moving the time.
Likewise the literal periodic prescription has a finite hard-wall endpoint
discrepancy. Those two diagnoses are not a blanket failure of the GGE principle.
This is an explicit correction of what our test can imply, not a relaxed five-
percent threshold or a claim to know the author's implementation.
