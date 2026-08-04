# Executable Derivation

The executable derivation consists of cards `QS001-QS005`. It computes the
encoded density matrix, published optimal observables, polar-normalized
interferometer fringe, amplitude-damping channel, and variance derivatives.

The implementation has two explicit non-Hermitian variance modes:

- `literal`: follows the printed `A^dagger A` order in Eq. (3);
- `paper_intended`: follows the curve and Fisher bound by using `A A^dagger`.

Keeping both is a scientific audit requirement. Original figure pixels and
experimental data points are never numerical inputs.

## Core equations

The encoded qubit state is evaluated directly as

$$
\rho(\theta)=\frac12
\begin{pmatrix}
1 & (2p-1)e^{i\theta}\\
(2p-1)e^{-i\theta} & 1
\end{pmatrix}.
$$

After polar normalization `A=aA'` and `R=aR'`, the reproduced interference
curve is

$$
\frac{I(\phi)}{n_0}=\frac14\left[
1+\langle R'^2\rangle+2|\langle A'\rangle|
\cos\left(\xi-\phi+\frac{\pi}{2}\right)
\right].
$$

The printed variance lane is

$$
V_{\rm literal}=
\frac{\langle A^\dagger A\rangle-|\langle A\rangle|^2}
{|\partial_\theta\langle A\rangle|^2}
=\frac{1}{F_{\rm nH}}+4,
$$

whereas the lane consistent with the paper's plotted bound is

$$
V_{\rm intended}=
\frac{\langle A A^\dagger\rangle-|\langle A\rangle|^2}
{|\partial_\theta\langle A\rangle|^2}
=\frac{1}{F_{\rm nH}}.
$$

Amplitude damping is applied after encoding:

$$
\rho_\gamma=E_0\rho E_0^\dagger+E_1\rho E_1^\dagger,
\quad
E_0=\begin{pmatrix}1&0\\0&\sqrt{1-\gamma}\end{pmatrix},
\quad
E_1=\begin{pmatrix}0&\sqrt{\gamma}\\0&0\end{pmatrix}.
$$
