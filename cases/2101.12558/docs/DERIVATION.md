# Scientific Derivation

## From the paper to a numerical object

The common object behind all 18 axes is the layer-resolved interacting Green
function. A public plane-wave calculation is projected into a Ni 3d/O 2p
Wannier basis,

$$
H^{KS}_{mm'}(\mathbf{k})=\langle w_{m\mathbf{k}}|\hat H_{KS}|w_{m'\mathbf{k}}\rangle.
$$

Each inequivalent Ni layer carries an independent local self-energy. Dyson's
equation gives

$$
G(\mathbf{k},z)=\left[(z+\mu)I-H^{KS}(\mathbf{k})-
P^\dagger(\Sigma(z)-V_{DC})P\right]^{-1},
$$

and its local projection defines the next impurity Weiss field,

$$
G_i(z)=\frac{1}{N_k}\sum_{\mathbf{k}}P_iG(\mathbf{k},z)P_i^\dagger,
\qquad \mathcal{G}_{0,i}^{-1}=G_i^{-1}+\Sigma_i.
$$

The five Ni d orbitals use the density-density Slater-Kanamori interaction
with the printed values $U=10$ eV and $J=1$ eV. The fully localized-limit
double counting is updated from the calculated occupancy,

$$
V_{DC}=U(N_d-1/2)-J(N_d/2-1/2).
$$

The charge density, Wannier Hamiltonian, impurity solutions, and double
counting must reach one joint fixed point. The source spectra then follow
from

$$
A(\mathbf{k},\omega)=-\frac{1}{\pi}\operatorname{Im}\operatorname{Tr}
G(\mathbf{k},\omega+i0^+),\qquad
A_{i\alpha}(\omega)=-\frac{1}{\pi}\operatorname{Im}G_{i\alpha,i\alpha}.
$$

The two spin-correlation figures are direct imaginary-time observables,

$$
\chi_i(\tau)=\langle m_{z,i}(\tau)m_{z,i}(0)\rangle,
\qquad \chi_i(\tau)=\chi_i(\beta-\tau),
$$

while a symmetric slab surface energy is

$$
\gamma=\frac{E_{slab}-N E_{bulk}}{2A}.
$$

The independent feature run verifies these algebraic and physical invariants.
It does not substitute the toy Hamiltonian for the paper's NiO calculation.
In the production path, each reconstructed $e_g$ moment operator is sampled
directly with the CT-HYB insertion estimator. A product or square of the
single-particle Green function is not accepted as this two-particle
observable.
