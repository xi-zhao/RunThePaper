# Derivation Trace

## 1. Microscopic Gaussian evolution

The Hamiltonian is quadratic, so the half-filled Neel state remains a Slater
determinant along every monitored trajectory.  Store its occupied orbitals as
an `L x (L/2)` matrix `Q`, with one-body projector `G=Q Q^dagger`.

The hopping matrix is circulant on the ring.  Its exact half-step propagator is
applied in the Fourier basis.  For the measurement part, write
`M_s=n_s-g_s`, where `g_s=G_ss`.  Dropping state-independent scalar terms, the
printed Ito increment has coefficient

`xi_s - gamma(1-2g_s)dt/2`

in front of `n_s`.  Exponentiating a one-body diagonal operator contributes the
Ito correction `+gamma dt/2`; therefore the orbital multiplier is

`exp[xi_s - gamma(1-g_s)dt]`, with `xi_s ~ N(0,gamma dt)`.

QR re-orthonormalization gives the normalized pure state.  Expanding this update
through Ito order recovers Main Eq. (1).  A symmetric
unitary-half/measurement/unitary-half step reduces splitting bias.

## 2. Observables

For a contiguous subsystem `A`, diagonalize `G_A`.  Its eigenvalues `nu_j`
give the exact Gaussian entropy

`S_A=-sum_j [nu_j log nu_j + (1-nu_j)log(1-nu_j)]`.

For distinct sites, Wick's theorem gives

`<n_x n_y>-<n_x><n_y> = -|G_xy|^2`.

The paper plots a positive `C` and writes it equal to `|G_xy|^2`.  The numerical
reproduction therefore outputs both quantities: `C_positive=|G_xy|^2` for the
paper curves and `C_connected=-|G_xy|^2` for the audit.  The sign is never
silently changed.

Nonlinear observables are evaluated per trajectory and only then averaged; an
average density matrix would erase the monitored-state physics.

## 3. Finite-size analysis

The CFT central charge is fitted from

`S(l,L)=(c/3) log[(L/pi)sin(pi l/L)] + s0`

on the printed window `L/4<l<3L/4`.  Half-chain data use the supplement's joint
ansatz

`S(L/2,L)=B L^b+(c/3)log(L/pi)+s0`,

`C(L/2,L)=1/(A L^a+D L)`.

Because several parameters are highly correlated on small size ranges, the
code also reports direct local slopes and synthetic-recovery tests.  A reduced
run cannot promote fit outputs to paper-exact.

## 4. Independent dark-state lane

At second order in microscopic hopping the replica kernel becomes
`|y|^-2p`.  The infrared integral

`K_p(q)=int_1^infinity sin^2(qy/2)y^-2p dy`

scales as `|q|^(2p-1)` for `1<p<3/2`, while for `p>3/2` its ultraviolet part
restores `q^2`.  Thus `p_c=3/2` follows without trajectory simulation.

The Bogoliubov dark-state covariance scales as `|q|^(p-5/2)`.  Fourier
transformation gives

- entropy exponent `b=3/2-p`;
- positive correlation exponent `a=p+1/2`;
- identity `b=2-a`.

These analytic results are generated independently of the stochastic solver
and serve as its strongest qualitative cross-check.

## 5. Paper-audit implications

Three source-level discrepancies are kept separate from reproduction quality:

1. Main Eq. (4b) misses the Wick minus sign for a literal connected density
   covariance.
2. Main text line 163 says the long-range coupling is relevant for `p>3/2`,
   contradicting its own Eqs. (6), (8)-(10), line 161, and the supplement; the
   intended inequality appears to be `p<3/2`.
3. Main Fig. 2 and Supplement Fig. 1 captions call `(gamma=0.3,p=1.25)` CFT and
   `(gamma=0.3,p=5)` algebraic, opposite to the equations, surrounding prose,
   and plotted slopes.

Each remains `inconclusive` until the formal two-method falsification and
fresh-context review gates are satisfied.
