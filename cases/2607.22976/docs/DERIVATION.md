# Executable Derivation

The executable derivation is the six-card chain `DW001` through `DW006` in
`DERIVATION_TRACE.md` and `EQUATION_CARDS.json`. Its invariants are:

1. the real-space stencil reproduces each Laurent polynomial on a Bloch mode;
2. winding equals root count minus pole order;
3. constrained Ronkin slopes equal winding mismatches;
4. the GBZ is the union of the published Case-I and Case-II conditions;
5. the Ronkin and diagonalization densities use the same Laplacian;
6. opening the ring removes the traveling-wave sector.

Numerical code may implement only formulas covered by these cards. Original
figure files, rendered panels, and digitized coordinates are not inputs.

## Core equations

For domain `i`, the frozen Laurent model is

$$
h_i(\beta)=\sum_{\alpha=-q_i}^{p_i} t_{i,\alpha}\,\beta^\alpha,
\qquad
P_i(\beta;E)=\beta^{q_i}\bigl(h_i(\beta)-E\bigr).
$$

If `n_i(E)` roots of `P_i` lie inside the unit circle, the point-gap winding is

$$
w_i(E)=n_i(E)-q_i.
$$

The root/Jensen form of the single-domain Ronkin function is minimized under
the three-domain length constraint:

$$
R_{\rm DW}(E)=
\min_{\mu_1,\mu_2,\mu_3}
\sum_{i=1}^{3}\frac{N_i}{N}\,R_i(\mu_i;E),
\qquad
\sum_i N_i\mu_i=0.
$$

Flux is inserted directly into the finite ring, and the determinant winding is

$$
W_{\rm DW}(E)=\frac{1}{2\pi i}
\int_0^{2\pi} d\Phi\,\partial_\Phi
\log\det\bigl[H_{\rm DW}(\Phi)-E\bigr].
$$

The spectral-density comparison in Fig. S1 uses the same complex-energy
Laplacian on the Ronkin and finite-eigenvalue potentials:

$$
\rho(E)=\frac{1}{\pi}\,\partial_E\partial_{\bar E}\Phi(E).
$$
