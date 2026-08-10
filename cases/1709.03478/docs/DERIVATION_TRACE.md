# Derivation Trace

## Core model

### EQC001–EQC002: continuum Hamiltonian and dimensionless grid

The paper's Eq. (1) is

\[
H=-\frac{\hbar^2}{2m}\partial_x^2+\frac{V_p}{2}\cos(2k_px)
 +\frac{V_d}{2}\cos(2k_dx+\phi).
\]

Set the primary-site spacing to \(a=\pi/k_p=\lambda_p/2\), define
\(s=x/a\), \(\alpha=k_d/k_p=\lambda_p/\lambda_d=532.2/738.2\), and divide
by \(E_r^p=\hbar^2k_p^2/(2m)\). Since
\(\partial_x=(k_p/\pi)\partial_s\),

\[
\frac{H}{E_r^p}=-\frac{1}{\pi^2}\partial_s^2
+\frac{v_p}{2}\cos(2\pi s)
+\frac{v_d}{2}\cos(2\pi\alpha s+\phi).
\]

On a uniform mesh \(s_j=(j+1/2)/q-L/2\) with \(h=1/q\),

\[
(H\psi)_j=\frac{2}{\pi^2h^2}\psi_j
-\frac{1}{\pi^2h^2}(\psi_{j-1}+\psi_{j+1})+V(s_j)\psi_j.
\]

This is a real symmetric tridiagonal matrix. Its lowest \(L\) eigenvectors
represent the lowest primary band. The independent free-particle check is that
the discrete kinetic eigenvalue approaches \(k^2/\pi^2\) with \(O(h^2)\)
error; the code also checks eigenvector orthonormality and grid refinement.

### EQC003: tunnelling-time conversion

The paper uses \(\tau=\hbar/J\). The primary-lattice lowest-band dispersion
\(\epsilon_0(q)\) gives the nearest-neighbour hopping coefficient

\[
J=-\int_{-1/2}^{1/2}\epsilon_0(q)\cos(2\pi q)\,dq,
\]

where energies are in \(E_r^p\). Thus a plotted time \(t_\tau=t/\tau\)
corresponds to the dimensionless Schrödinger phase
\(\exp[-i(E/E_r^p)t_\tau/(J/E_r^p)]\). A common band offset cancels from
all density observables and is subtracted for numerical stability.

### EQC004: CDW imbalance

Let \(P_0\) project onto Wannier-like cell ground states on one parity of
primary sites. The evolved one-body density matrix is
\(\rho(t)=U(t)P_0U^\dagger(t)\). With \(W_{\rm eo}\) equal to +1 on even
cells and -1 on odd cells,

\[
\mathcal I(t)=\frac{\mathrm{Tr}[W_{\rm eo}\rho(t)]}
{\mathrm{Tr}[\rho(t)]}.
\]

It is exactly 1 at \(t=0\). For \(V_d=0\), phase averaging and long-time
dephasing drive it toward zero; in a strongly localized limit it remains
positive. These are executable sanity checks.

### EQC005: center-third edge density

Let \(P_c\) be the projector onto the lowest-band eigenstates of the isolated
central third. After releasing it into the full system,

\[
\mathcal D(t)=1-\frac{N_c(t)}{N_c(0)},\qquad
N_c(t)=\mathrm{Tr}[W_cU(t)P_cU^\dagger(t)],
\]

where \(W_c\) selects the originally populated central third. Dividing by the
same lowest-band representation's \(N_c(0)\) removes basis-projection leakage
without changing the physical definition. Therefore \(\mathcal D(0)=0\),
\(0\le\mathcal D\le1\) up to roundoff, and a uniform final density approaches
\(2/3\). These bounds are checked.

### EQC006: spectral propagation

For the real symmetric final grid Hamiltonian \(H=Q\Lambda Q^T\),

\[
U(t)=Q\,\mathrm{diag}(e^{-i\lambda_at})Q^T.
\]

For a diagonal observable \(W\) and initial density matrix \(\rho_0\), define
\(W'=Q^TWQ\), \(R'=Q^T\rho_0Q\). Then

\[
\langle W\rangle_t=\sum_{ab}W'_{ab}R'_{ba}
e^{i(\lambda_a-\lambda_b)t}.
\]

This reduces each scalar observable from orbital-by-orbital propagation to an
\(O(L^2)\) contraction after diagonalization, without changing the model.
For the stationary curves in Main Figs. 3–4, the long-time average removes
off-diagonal energy coherences,

\[
\overline{\langle W\rangle}=\sum_a W'_{aa}R'_{aa}.
\]

This diagonal-ensemble object is kept distinct from the explicit
\(3000\tau\) finite-time calculation used for Supplementary Fig. S2.

### EQC007: supplementary cloud observables

The supplement defines a Gaussian envelope with FWHM about 123 sites,
cell-resolved FWHM, edge density, and an RMS radius. For normalized site
density \(n_i\), the implemented RMS is the dimensionally consistent standard
form

\[
r_{\rm rms}=\sqrt{\frac{\sum_i(i-i_c)^2n_i}{\sum_i n_i}}.
\]

The prose/TeX in the supplement omits the outer square root on its right-hand
side; this is explicitly treated as a reconstructed correction rather than
silently copied.

### EQC008: tube averaging proxy

The supplement gives Gaussian lattice-beam waist \(w=150\,\mu\mathrm m\) and
cloud widths \(w_y=42\,\mu\mathrm m\), \(w_z=12\,\mu\mathrm m\), but not the
per-tube atom histogram or the convention attached to the fitted cloud widths.
The declared proxy treats all quoted widths as \(1/e^2\) radii and writes

\[
n(y,z)\propto e^{-2(y^2/w_y^2+z^2/w_z^2)},\qquad
f(y,z)=e^{-2(y^2+z^2)/w^2}.
\]

With \(u=\sqrt{2}y/w_y\) and \(v=\sqrt{2}z/w_z\), the normalized atom
distribution is \(e^{-u^2-v^2}/\pi\).  Product Gauss–Hermite quadrature
therefore evaluates the nonlinear tube observable directly:

\[
\langle O\rangle_{\rm tube}\approx
\sum_{ij}\frac{4w_iw_j}{\pi}O(f_{ij}V_p,f_{ij}V_d),\qquad
f_{ij}=\exp\!\left[-\frac{w_y^2u_i^2+w_z^2v_j^2}{w^2}\right].
\]

Even quadrature orders permit the four sign-related points to be merged.  The
production order-(8,4) rule yields eight explicit positive-coordinate depth
nodes; the order-(10,6) reference yields fifteen and refines both transverse
axes.  This is derivable and executable without author arrays, but remains a
`paper_scale_method_proxy`, not author-equivalent tube averaging.

### EQC009: phase-boundary rule

The Fig. 3 caption defines numerical boundaries as the first detuning depths
where \(\mathcal I\) rises through 0.015 and \(\mathcal D\) falls through
0.015. The runner uses linear interpolation only between independently
generated neighboring grid points. No source curve or source pixel is read.

## Numerical gate decision

EQC001–EQC006 and EQC009 are source-traced and independently checked at reduced
scale. EQC007 and EQC008 are explicitly reconstructed.  Paper-scale execution,
four-axis convergence and fresh protocol-v2 review remain outstanding; no
artifact may be called final or a paper-error candidate before those gates pass.
