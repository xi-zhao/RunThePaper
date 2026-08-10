# Scientific Derivation

The reproduction starts from the scalar effective-mass Hamiltonian printed in the
paper, expands its C3-symmetric potential in complete reciprocal shells, and solves
the resulting Hermitian plane-wave matrix. Every downstream object is derived from
those eigenpairs: bands and DOS directly, hopping through a triangular-shell fit,
the Wannier orbital through a gauge-aligned Bloch sum, screened interactions through
Wannier-density projection, exchange through the printed strong-coupling expansion,
and the Fermi contour through filling the computed top band.

$$
\Delta(\mathbf r)=2V\sum_{j=1}^{3}\cos(\mathbf b_j\cdot\mathbf r+\psi),
\qquad
H_{\mathbf g'\mathbf g}(\mathbf k)=
-\delta_{\mathbf g'\mathbf g}\frac{\hbar^2|\mathbf k+\mathbf g|^2}{2m^*}
+V(\mathbf g'-\mathbf g).
$$

The projected interaction and spin exchange follow

$$
U_{RR'}=\iint |w_R(\mathbf r)|^2\widetilde U(\mathbf r-\mathbf r')
|w_{R'}(\mathbf r')|^2\,d\mathbf r\,d\mathbf r',
\qquad
J_1=\frac{4t_1^2}{U_0}\left[1-7\left(\frac{t_1}{U_0}\right)^2\right].
$$

The supplement changes only the moire geometry and potential parameters, so it is an
independent parameter-regime test of the same derivation. The DFT displacement map that
originally motivated the fitted potential cannot be uniquely rerun because essential
first-principles metadata are absent; it is kept visible as D001 rather than replaced
with the fitted potential.

Detailed algebra, assumptions and code pointers are recorded in `DERIVATION_TRACE.md`
and `EQUATION_CARDS.json`.
