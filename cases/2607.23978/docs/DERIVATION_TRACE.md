# Derivation Trace

## QS001: encoded mixed qubit

From `|Psi0,1>=(|0> +/- |1>)/sqrt(2)`,

`rho0 = [[1/2, (2p-1)/2], [(2p-1)/2, 1/2]]`.

Applying `M_theta=diag(exp(i theta/2),exp(-i theta/2))` multiplies the upper
off-diagonal element by `exp(i theta)` and the lower by its conjugate. This
closed form is used for every trace and derivative.

## QS002: the observable-order inconsistency

For a fixed locally optimal observable, Eq. (3) means

`V_A = (Tr[rho A^dagger A]-|Tr[rho A]|^2) / |d_theta Tr[rho A]|^2`.

Substitution gives, exactly,

- `V_AH = 1/(2p-1)^2 = 1/F_H`;
- `V_AnH_literal = 4 + 4p(1-p)/(2p-1)^2 = 4 + 1/F_nH`.

The second result contradicts the stated saturation and the red line in
Fig. 3(a). If the numerator is instead `Tr[rho A A^dagger]-|<A>|^2`, or the
printed observable is replaced by its adjoint, then

`V_AnH_intended = 4p(1-p)/(2p-1)^2 = 1/F_nH`.

The code exposes `ordering="literal"` and `ordering="paper_intended"`; the
figure reproduction uses the latter and the science check requires the exact
`+4` discrepancy in the former.

## QS003: normalized fringe

Take the polar decomposition `A=UR`, let `a` be the largest eigenvalue of
`R`, and define `A'=A/a`, `R'=R/a`. Dividing Eq. (8) by `n0` gives

`I(phi)/n0 = [1 + <R'^2> + 2 |<A'>| cos(xi-phi+pi/2)]/4`.

All quantities are recomputed from matrices. For an optimal observable built
at the same local parameter as the state, `<A'>=0`; Fig. 2(c,d) therefore
contains flat theory baselines whose values depend on `<R'^2>`.

## QS004-QS005: noisy curves

After encoding, apply

`rho_gamma = E0 rho E0^dagger + E1 rho E1^dagger`.

The observable remains fixed at the working point `p=0.01`,
`theta=0.3*pi` while the encoded state is varied for the `theta` derivative.
The main theory curve uses the paper-intended non-Hermitian order identified
above. The `gamma` derivative is evaluated from the smooth generated variance
curve with a convergence check over two steps.

## Missing derivation lane

The main text does not define `A1`, `A2`, the explicit physical POVM elements,
or the reported finite `Delta gamma`. Because the cited Supplement is absent
from the arXiv submission, those numerical lanes remain blocked rather than
being reconstructed from the plotted pixels.
