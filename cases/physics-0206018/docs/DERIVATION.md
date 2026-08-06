# Equation-to-code derivation

This case independently implements the boundary-element formulation in Jan
Wiersig's paper. The calculation uses the printed equations and reported
parameters, not author code, author arrays, digitized curves, or figure pixels.

## 1. Boundary representation

For each homogeneous region, the outgoing two-dimensional Helmholtz Green
function is

$$
G(\mathbf r,\mathbf r')=-\frac{i}{4}
H_0^{(1)}\!\left(nk|\mathbf r-\mathbf r'|\right).
$$

Green's identity reduces the field to its boundary value $\psi$ and normal
derivative $\partial_\nu\psi$. Interior and exterior equations are coupled with
the TM boundary conditions into a non-Hermitian matrix equation
$M(k)u=b$ for scattering and $M(k)u=0$ for resonances.

## 2. Constant boundary elements

Each boundary segment carries constant field variables. Off-diagonal matrix
entries use Gaussian quadrature. Diagonal logarithmic singularities use the
analytic limits printed in the paper, including the local-curvature correction.
The implementation is in `code/src/bem.py`.

## 3. Scattering cross section

A plane wave supplies the incident boundary data. Solving the coupled system
gives the far-field amplitude and total cross section through the two-dimensional
optical theorem. Scanning $20\le kR\le25$ produces the independent Fig. 5
resonance sequence.

## 4. Resonance state and fields

At the reported complex resonance, the smallest right singular vector of
$M(k)$ supplies the shared boundary state. The near field follows from the
boundary integral representation, and the far field follows from the Hankel
asymptotic form. The same generated state is used for Figs. 6 and 7, preventing
independent curve fitting of the two panels.

## 5. Resolution criterion

The paper's boundary-resolution measure is

$$
b=\frac{2\pi}{n\,\operatorname{Re}(k)\,\Delta s}\ge4.
$$

The public feature calculation uses 432 boundary elements, rather than the
paper's 1600, because the exact corner-rounding curve and nonuniform element map
are not specified. It is therefore a reduced-scale numerical reproduction, not
a paper-exact mesh reconstruction.

## Figure mapping

| Paper target | Independently generated object |
| --- | --- |
| Fig. 5 | plane-wave cross-section scan |
| Fig. 6 | resonant near-field intensity from the BEM null state |
| Fig. 7 | far-field radiation pattern from the same null state |

Figs. 1–4 are geometry or method schematics and are intentionally not redrawn.
