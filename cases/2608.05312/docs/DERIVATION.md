# Equation-level derivation

This document records the equations used by the independent reproduction of
arXiv:2608.05312v1. The numerical implementation follows these equations in
the single-excitation basis `[cavity, site 1, ..., site N, sink]`.

## EQ001 — Single-excitation Tavis–Cummings–Hubbard Hamiltonian

The coherent model is

$$
H=\omega_a a^\dagger a+\varepsilon\sum_i\sigma_i^\dagger\sigma_i
+\sum_i g(a^\dagger\sigma_i+\mathrm{h.c.})
+\sum_i t_i(\sigma_i^\dagger\sigma_{i+1}+\mathrm{h.c.}),
\qquad t_i=t+\delta t X_i .
$$

In the numerical basis, the cavity–site matrix elements are `g`, while the
nearest-neighbour matrix elements are `t_mean + delta_t * X[i]`. See
`code/src/cavity_transport/model.py::build_hamiltonian`.

## EQ002 — Emission, absorption, and detailed balance

For the non-Condon channel,

$$
\gamma_{\mathrm{em}}=2J(\Delta)(1+n),\qquad
\gamma_{\mathrm{abs}}=2J(\Delta)n,
$$

so that

$$
\frac{\gamma_{\mathrm{abs}}}{\gamma_{\mathrm{em}}}
=e^{-\Delta/(k_B T)}.
$$

The implementation therefore uses
`gamma_abs = gamma_rec * exp(-1 / thermal_ratio)`, with zero absorption at
zero temperature. See `code/src/cavity_transport/model.py::absorption_rate`.

## EQ003 — Lindblad jump operators

The state-changing channels are

$$
L_{\mathrm{rec},i}=\sqrt{\gamma_{\mathrm{rec}}}
|\mathrm{cav}\rangle\langle i|,
\quad
L_{\mathrm{abs},i}=\sqrt{\gamma_{\mathrm{abs}}}
|i\rangle\langle\mathrm{cav}|,
$$

and local pure dephasing is

$$
L_{\mathrm{deph},i}=\sqrt{\gamma_{\mathrm{deph}}}|i\rangle\langle i|.
$$

The drain is represented by a jump from either the cavity or the final site
to the sink. See `code/src/cavity_transport/model.py::build_jumps`.

## EQ004 — Unidirectional rescue sum rule

If `w_k` denotes the photonic weight of eigenstate `k`, the rescue-induced
transition rate is

$$
W^{\mathrm{rec}}_{k\leftarrow l}
=\gamma_{\mathrm{rec}}w_k(1-w_l).
$$

For an ideal dark initial eigenstate, `w_l=0`. Completeness gives
`sum_k w_k=1`, hence

$$
\sum_{k\in B}W^{\mathrm{rec}}_{k\leftarrow l\in D}
=\gamma_{\mathrm{rec}}.
$$

The escape rate from every ideal dark state is therefore independent of
system size. The reverse transition into a perfectly dark destination is
zero. This one-way identity is checked numerically for several system sizes in
`code/src/cavity_transport/checks.py`.

## EQ005 — Pure-rescue dark decay

The sum rule closes the dark-manifold rate equation:

$$
\frac{dp_D}{dt}=-\gamma_{\mathrm{rec}}p_D,
\qquad
p_D(t)=p_D(0)e^{-\gamma_{\mathrm{rec}}t}.
$$

Coupling the rescued bright population to the drain yields the paper's
two-exponential form

$$
\eta(t)=1-Ae^{-\Gamma_B t}-Be^{-\gamma_{\mathrm{rec}}t}.
$$

The public checks fit the generated dark population and recover the unit decay
rate to numerical precision.

## EQ006 — Column-vectorized Lindblad generator

With column-stacked vectorization,

$$
\mathcal L=-i(I\otimes H-H^T\otimes I)
+\sum_j\left[L_j^*\otimes L_j-
\frac12\left(I\otimes L_j^\dagger L_j+
(L_j^\dagger L_j)^T\otimes I\right)\right].
$$

The reproduction constructs this operator sparsely and applies
`scipy.sparse.linalg.expm_multiply` directly to the vectorized initial density
matrix. A small-system dense exponential is an independent numerical oracle;
the maximum observed matrix-element difference is `3.40e-16`. See
`code/src/cavity_transport/liouvillian.py`.

## EQ007 — Bright and dark observables

After diagonalizing the coherent system Hamiltonian, the two states with the
largest cavity weights define the bright manifold:

$$
P_B=\sum_{k\in B}|\psi_k\rangle\langle\psi_k|,
\qquad
P_D=\sum_{k\in D}|\psi_k\rangle\langle\psi_k|.
$$

Populations are computed as `Tr(P_B rho)` and `Tr(P_D rho)`. This partition
exposes the transient dark-to-bright valve shown in the reproduced dynamics.
See `code/src/cavity_transport/observables.py::manifold_projectors`.

## Parameter boundary

The paper does not print the mean hopping, exact source-state notation,
author random seeds, or exact scan grids. The shared reconstruction uses
`t=1 meV`, source `|1><1|`, and declared deterministic seed sequences. These
choices are constrained by multiple independent paper anchors, but they remain
`paper_subset`, not author-data-level parameters.
