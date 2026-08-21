# Derivation

## 1. Mode decomposition

After Jordan-Wigner and Bogoliubov transformations, each momentum mode is

$$
h_k(g)=(g-\cos k)\sigma_z+\sin k\,\sigma_x,
\qquad \epsilon_k(g)=\sqrt{(g-\cos k)^2+\sin^2 k}.
$$

For a sudden quench, the initial ground state is a superposition of the final
ground and excited mode states. With
`phi_k=theta_k(g0)-theta_k(g1)`, the boundary free energy is

$$
f(z)=-\int_0^\pi\frac{dk}{2\pi}
\log[\cos^2\phi_k+\sin^2\phi_k e^{-2z\epsilon_k(g_1)}].
$$

## 2. Fisher zeros and critical times

Setting each factor to zero gives

$$
z_n(k)=\frac{\log\tan^2\phi_k+i\pi(2n+1)}{2\epsilon_k(g_1)}.
$$

A line crosses the imaginary axis when `sin^2(phi_k*)=1/2`. Therefore

$$
\cos k^*=\frac{1+g_0g_1}{g_0+g_1},\qquad
t_n^*=\frac{\pi(n+1/2)}{\epsilon_{k^*}(g_1)}.
$$

The implementation evaluates both the closed crossing formula and the full
momentum integral; they agree at machine precision.

## 3. Work large deviations

The paper's exact cumulant density `c(R,t)` is evaluated on a monotone `R`
grid. For each work density `w`, the grid brackets the saddle condition
`partial_R c=w`; a safeguarded Newton solve refines `R*`, and

$$
r(w,t)=\sup_R[c(R,t)-wR]
$$

is evaluated directly at `R*`. This removes interpolation-induced zero
plateaus. At `w=0` the result independently closes on the Loschmidt rate to
`1.28e-15`.

## 4. Longitudinal order

The even-parity ground state is represented by a two-component Majorana
covariance symbol on the antiperiodic momentum grid. Its exact time evolution
under the final quadratic Hamiltonian gives a real-space covariance matrix.
For separation `r`,

$$
\langle\sigma^z_0\sigma^z_r\rangle=(-1)^r\operatorname{Pf}\Gamma_r.
$$

The pivoted Pfaffian agrees with a separately implemented `N=10` exact spin
chain within `3e-4`. Production uses `N=128,192,256` and proportional
separations; the first oscillation minimum is unchanged on this grid.

## 5. General ramps

For a declared `g(t)`, every mode is propagated by midpoint exponentials of
`h_k(g(t))`. Endpoint occupations are continuous from one at `k=0` to zero at
`k=pi` for the across-critical protocols, so a half-occupied mode occurs. The
paper does not publish a specific ramp, hence linear and smoothstep results are
reconstructed evidence rather than paper-exact curves.

## 6. Supplemental normalization audit

From `L_ab=exp(-N f_ab)`, the rates are `-log|cos|` and `-log|sin|`. A tilted
probability distribution must be divided by its partition function. The same
normalization gives

$$
\int dW\,P_\beta(W)e^{iWt}=G(t+i\beta)/G(i\beta).
$$

Literal and corrected expressions are both preserved in the frozen outputs so
that a fresh reviewer can attempt to falsify the discrepancy.
