# Scientific Derivation

The reproduction starts from the aligned-bilayer displacement fields, maps them to the slowly varying moire displacement `theta z×r`, and expands the resulting continuum Hamiltonians in complete reciprocal shells. `DERIVATION_TRACE.md` records each step and its code mapping. No plotted coordinates enter this derivation.

The core scientific chain is:

```text
local stacking symmetry
  -> layer potentials and tunneling harmonics
  -> two-layer moire Hamiltonian
  -> eigenvalues/eigenvectors across the MBZ
  -> bands, DOS, Berry curvature, Chern numbers and phase boundaries
  -> remote-band four-state robustness checks
```

The moire reciprocal scale follows directly from the small-angle rotation of
the monolayer reciprocal vectors,

$$
a_M = \frac{a_0}{2\sin(\theta/2)}, \qquad
\mathbf b_j = \theta\,\hat{\mathbf z}\times\mathbf G_j.
$$

The local stacking displacement gives the two layer potentials and tunneling
harmonics used as numerical inputs,

$$
\Delta_l(\mathbf r)=2V\sum_{j=1,3,5}
\cos\!\left(\mathbf b_j\cdot\mathbf r+l\psi\right),
\qquad
\Delta_T(\mathbf r)=w\left(1+e^{-i\mathbf b_2\cdot\mathbf r}
+e^{-i\mathbf b_3\cdot\mathbf r}\right).
$$

They enter the continuum Hamiltonian that is diagonalized in a complete
reciprocal-shell basis,

$$
H_\uparrow(\mathbf k,\mathbf r)=
\begin{pmatrix}
-\frac{\hbar^2(\mathbf k-\boldsymbol\kappa_+)^2}{2m^*}+\Delta_{+}(\mathbf r)
& \Delta_T(\mathbf r)\\
\Delta_T^*(\mathbf r)
&-\frac{\hbar^2(\mathbf k-\boldsymbol\kappa_-)^2}{2m^*}+\Delta_{-}(\mathbf r)
\end{pmatrix}.
$$

The topology is evaluated from the independently generated eigenvectors, not
from plotted coordinates,

$$
\Omega_n(\mathbf k)=-2\,\mathrm{Im}\sum_{m\ne n}
\frac{\langle n|v_x|m\rangle\langle m|v_y|n\rangle}
{(E_m-E_n)^2},\qquad
C_n=\frac{1}{2\pi}\int_{\mathrm{MBZ}}\Omega_n(\mathbf k)\,d^2k.
$$

The strongest independent checks are the pseudospin winding `-0.9969`, the first two Chern integrals `-0.9778/+0.9760`, exact Hermiticity, symmetry-related corner degeneracy and reciprocal-shell convergence.
