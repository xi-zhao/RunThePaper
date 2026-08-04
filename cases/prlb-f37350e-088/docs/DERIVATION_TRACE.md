# Derivation trace

## Sextic covariance

The prompt defines

$$
\operatorname{Cov}(z^2/r^2,R_6)=A_{z,2}A_{z,6}\operatorname{Cov}(z^2,z^6)/r^8.
$$

Therefore the variance cross term is

$$
2A_{z,2}\operatorname{Cov}(z^2/r^2,R_6)
=180A_{z,2}^2A_{z,6}s^4.
$$

## Magic-angle boundary layer

At `cos(2 theta_m)=-3/5`, the needed values are

$$
g=2/5,\ g'=12/5,\ A'_{z,2}=-6,\ A_{z,4}=3/4,
\ P=A_{x,2}^2+A_{y,2}^2=288/25,\ P'=-5328/25.
$$

Writing `theta=theta_m+c s` and solving the leading stationarity condition gives

$$
c=\frac{4P(g'/g)-2P'-24A'_{z,2}A_{z,4}}{4(A'_{z,2})^2}
=\frac{563}{100}.
$$

The sixth-order `lambda` term enters one order later, so it cannot destroy this limit for any fixed finite `lambda`.

## Ring norm

With `M=N/2` cells, the Bloch off-diagonal element of `H-H'` is

$$
\frac{J_0-J_1}{2}(1-e^{-iq}),\qquad q=2\pi n/M.
$$

Maximizing its magnitude gives `f_N=1` if `M` is even and `f_N=cos(pi/N)` if `M` is odd. This discrete-momentum obstruction invalidates the claimed N independence.
