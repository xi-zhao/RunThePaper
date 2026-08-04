# Independent Derivation

## Zero mode

With `Y0=1/sqrt(V)`, the constant-field action is

$$
S_0 = \frac{\lambda}{4V}\phi_0^4.
$$

For `a=lambda/(4V)`, the even moments of `exp(-a phi0^4)` are

$$
\langle\phi_0^n\rangle =
a^{-n/4}\frac{\Gamma((n+1)/4)}{\Gamma(1/4)}.
$$

This gives the frozen Task 1 result and `<phi0^4>=V/lambda`.

## Nonzero-mode Hessian

The background field is `phibar=phi0/sqrt(V)`. The physical quadratic
coefficient follows directly from the local potential:

$$
V''(\bar\phi)=3\lambda\bar\phi^2=
\frac{3\lambda}{V}\phi_0^2.
$$

Therefore

$$
A=\langle M^2\rangle =6\sqrt{\frac{\lambda}{V}}
\frac{\Gamma(3/4)}{\Gamma(1/4)},\qquad
B=\langle M^4\rangle=\frac{9\lambda}{V}.
$$

The exact zero-mode-averaged propagator is evaluated by adaptive quadrature.
The truncated geometric series requires `M^2/K^2 << 1`; it cannot be a
`K -> 0` deep-infrared expansion.

## Large-N saddle

Write `lambda=t^2`, `mbar^2=mu t^2`, and
`rho0=sqrt(dD)/t+r0`. Expanding `8 rho0^2 W'(rho0)=1` through first order in
`t` gives

$$
r_0=-\frac{3D}{d}-\frac{\mu}{2}.
$$

Substitution into `D/rho0` and the singlet frequency yields the two source
eigenvalue series with distinct labels `lambda_v` and `lambda_s`.

## NLO Fokker-Planck equation

Source Eq. (8.14) directly fixes the three coefficients. Their dimensions are
`[a]=mass^-2`, `[b]=mass`, and `[c]=mass^-3` in the source convention, matching
the derivative terms of Eq. (8.13).
