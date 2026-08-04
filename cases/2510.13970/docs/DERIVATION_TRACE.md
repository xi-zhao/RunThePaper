# Derivation trace

## Symmetry block

Because the propagator commutes with global parity and the initial density matrix is parity invariant, partial-trace invariance gives `P_A rho_A P_A = rho_A`. Thus `rho_A` is parity block diagonal, `w_+-w_-=Tr(rho_A P_A)`, and a discontinuous change of the maximizing parity block forces a top-eigenvalue degeneracy.

## Distinguishing effective generators

For `H(t)=A+B cos(omega t)`, a periodic rotation that removes the drive gives the phase-independent second-order generator

$$
H_{\mathrm{vV}}=A+\frac{[B,[A,B]]}{4\omega^2}+O(\omega^{-3}).
$$

The principal stroboscopic logarithm at the chosen phase `t0=0` instead has

$$
H_F(0)=A+\frac{[B,[A,B]]/4-[A,[A,B]]}{\omega^2}+O(\omega^{-3}).
$$

Dense Pauli projection at `L=6`, `J=1`, `h0=2` gives

$$
[B,[A,B]]=(8,-8,0,0,0),\qquad
[A,[A,B]]=(0,0,-4,-8,-8).
$$

Therefore the stroboscopic vector is `(2,-2,4,8,8)`. The frozen/source vector is its negative, `(-2,2,-4,-8,-8)`.

## Task-6 asymptote

The leading mismatch operator is

$$
K=4ZZ-4YY+8X_{\rm edge}+16X_{\rm bulk}+16ZXZ,
$$

with `||K||_infty = 101.33438627528581`. Hence

$$
\omega^3\|\Delta\|_\infty
=\omega\|K\|_\infty+O(1),
$$

which diverges.
