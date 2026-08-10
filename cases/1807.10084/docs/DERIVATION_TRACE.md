# Derivation Trace

## 1. Physical mechanism

For a counterclockwise spinning resonator, counterpropagating optical modes see
opposite Fizeau shifts. Neglecting the explicitly small dispersion correction,

\[
\Delta_F=\pm\eta\Omega,\qquad
\eta=\frac{n_0r\omega_0}{c}\left(1-\frac{1}{n_0^2}\right).
\]

The sign is fixed by propagation direction, not fitted from the figure. With
the paper values, `eta=83.38974048`; `Omega=29 kHz` therefore gives
`Delta_F/U=0.507577`, explaining the paper's `|Delta_F|=U/2`
condition to its plotted precision.

## 2. Rotating-frame Hamiltonian and levels

Transforming the coherent drive at frequency `omega_L` into its rotating frame
gives

\[
H/\hbar=(\Delta_L+\Delta_F)a^\dagger a
       +U a^{\dagger2}a^2+\xi(a^\dagger+a),
\quad \Delta_L=\omega_0-\omega_L.
\]

Using `a†a|n>=n|n>` and `a†2a2|n>=n(n-1)|n>` produces the
undriven Fock energies

\[
E_n/\hbar=n(\Delta_L+\Delta_F)+Un(n-1).
\]

These energies determine every theoretical level diagram. No coordinates or
pixels are copied from the paper.

## 3. Physical-to-numerical parameter map

The printed SI quantities determine all rates:

\[
\omega_0=2\pi c/\lambda,\quad
\gamma=\omega_0/Q,\quad
U=\frac{\hbar\omega_0^2cn_2}{n_0^2V_{eff}},\quad
\xi=\sqrt{\frac{\gamma P_{in}}{\hbar\omega_L}}.
\]

For `lambda=1550 nm`, `Q=5e9`, `n0=1.4`, `n2=3e-14 m2/W`, and
`Veff=150 um3`, the independent calculation gives

| Quantity | Value |
| --- | ---: |
| `omega0` | `1.215259075683131e15 rad/s` |
| `gamma` | `2.430518151366262e5 rad/s` |
| `U` | `4.764403491927026e6 rad/s` |
| `U/gamma` | `19.6024188885` |

The implementation divides the full generator by `gamma`; steady states are
unchanged and numerical conditioning improves.

## 4. Exact steady state

The paper's one-photon loss equation is

\[
\dot\rho=-i[H/\hbar,\rho]
+\gamma\left(a\rho a^\dagger-\tfrac12\{a^\dagger a,\rho\}\right).
\]

Column stacking and `vec(A rho B)=(B^T tensor A)vec(rho)` give EQ008.
One redundant Liouvillian row is replaced by the trace constraint
`vec(I)^T vec(rho)=1`. The solution is symmetrized only for roundoff-level
diagnostics; observables use the direct converged solution.

The Fock cutoff is not assumed. It is increased until the final-level
population and the changes in `mean_n`, `g2`, `g3`, and `g4` satisfy the
declared convergence tolerances.

## 5. Observables

Because `a†m a^m` is diagonal in the Fock basis,

\[
g^{(m)}(0)=\frac{\sum_n n(n-1)\cdots(n-m+1)P(n)}{\bar n^m},
\quad P(n)=\rho_{nn},\quad \bar n=\sum_n nP(n).
\]

The Poisson reference is generated from the same independently calculated
`mean_n`; it is not extracted from the source figure.

## 6. Weak-drive cross-check

Truncating the no-jump wavefunction and retaining leading drive orders gives

\[
C_1=-\frac{\xi}{\Delta-i\gamma/2},\qquad
C_2=-\frac{\sqrt2\xi C_1}{2(\Delta+U)-i\gamma},
\quad \Delta=\Delta_L+\Delta_F.
\]

Substitution into the factorial moments yields EQ006. Repeating the recurrence
for `C3` yields the displayed `g3`. Both reduce to one for `U=0`, providing a
simple analytic check. These approximations are comparison references; final
data come from the Lindblad equation.

## 7. Blockade classifications

The paper's two-photon blockade criterion is evaluated without visual
judgment:

\[
g^{(3)}<e^{-\bar n},\qquad
g^{(2)}\ge e^{-\bar n}+\bar n g^{(3)}.
\]

PIT requires the displayed higher-order correlations to exceed one. Relative
photon-number bars use

\[
\delta P_n=(P_n-\mathcal P_n)/\mathcal P_n,
\qquad \mathcal P_n=e^{-\bar n}\bar n^n/n!.
\]

This closes the causal chain from the paper's physics to every plotted numeric
quantity.
