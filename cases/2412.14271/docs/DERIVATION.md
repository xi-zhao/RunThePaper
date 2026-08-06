# Equation-to-code derivation

This case reconstructs the paper from its Hamiltonian, Lindblad equation, and
published cumulant equations. Author code, author numerical arrays, and
digitized figure curves are not inputs to the calculation.

## 1. Open two-photon Dicke model

The finite-size model is

$$
H=\omega_c a^\dagger a+\frac{\omega_a}{2}J_z
  +\frac{\lambda}{N}J_x\left(a^{\dagger 2}+a^2\right),
$$

with Lindblad evolution

$$
\dot\rho=-i[H,\rho]+\mathcal D[\sqrt{\kappa_1}a]\rho
 +\mathcal D\left[\sqrt{\kappa_2/N}\,a^2\right]\rho.
$$

The operator construction and collapse channels are implemented in
`code/src/dicke.py`.

## 2. Thermodynamic branches

For one-photon loss, the normal and superradiant fixed points and the critical
coupling are reconstructed analytically. For simultaneous one- and two-photon
loss, the second-order cumulant equations define a real nonlinear vector field
$\dot x=F(x)$. Fixed points are found independently and retained only when
their residual, spin-length constraint, and bosonic covariance are physical.

The Bogoliubov spectrum is obtained from the numerical Jacobian
$B=\partial F/\partial x|_{x_*}$. Zero modes are kept explicit instead of being
silently classified as stable. This distinction is central to the Fig. 3(g)
finding documented in [PAPER_DISCREPANCY.md](PAPER_DISCREPANCY.md).

## 3. Finite-size quantum calculation

The finite-size panels use an independent Monte-Carlo wave-function
unravelling. For $N_T$ trajectories,

$$
\rho_{\mathrm{ph}}=\frac{1}{N_T}\sum_{j=1}^{N_T}
\operatorname{Tr}_{\mathrm{spin}}|\psi_j\rangle\langle\psi_j|.
$$

Fock distributions, photon number, spin polarization, and Wigner functions are
computed from this reduced density matrix. The public configuration uses fewer
trajectories than the paper and is therefore labeled feature-level rather than
paper-exact.

## 4. Parity-resolved supplement

With pure two-photon loss, photon parity
$P=(-1)^{a^\dagger a}$ is conserved. The code checks the two-dimensional
near-zero Liouvillian kernel and the leakage of even and odd initial states into
the opposite parity sector.

## 5. Figure mapping

| Paper target | Numerical object |
| --- | --- |
| Fig. 2 | one-photon analytic branches, cutoff-dependent trajectory data, Fock distributions |
| Fig. 3 | finite-size Fock distributions and thermodynamic branches |
| Fig. 4 | Wigner functions from the generated reduced density matrices |
| Fig. S1 | one-photon Bogoliubov spectra |
| Fig. S2 | both-loss fixed points and stability spectra |
| Fig. S5 | trajectory-count convergence diagnostic |
| parity supplement | Liouvillian near-zero modes and parity-resolved Fock distributions |

Formal supplemental Figs. S3–S4 are not claimed because the parameters needed
to identify those targets are not available in the accessible paper version.
