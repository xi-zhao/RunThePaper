# Paper Map

## Identity

- Paper ID: `physics-0206018`
- Title: *Boundary element method for resonances in dielectric microcavities*
- Author: Jan Wiersig
- Publication: *Journal of Optics A: Pure and Applied Optics* **5**, 53-60 (2003)
- DOI: `10.1088/1464-4258/5/1/308`
- Preprint: <https://arxiv.org/abs/physics/0206018> (v2, 10 December 2002)
- PDF: `raw/paper.pdf` (SHA-256 `d08bf2750f924b8a18b760318e8d1a240adeba106e921900fe6521e41101820f`)
- TeX: `paper-source/obem.tex`; no author numerical code is present or used.

## Reproduction Goal

Implement the Green-function boundary element method from the printed
equations, validate it against an independently known circular-cavity
resonance, then recompute every numerical result for the coupled hexagons:
cross section (Fig. 5), resonant near field (Fig. 6), and far-field emission
(Fig. 7). Geometry and method illustrations (Figs. 1-4) are classified but not
redrawn as reproduction targets.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| I | 2D dielectric Helmholtz and outgoing resonances | Defines physical observable and lifetime. |
| II | Green-function boundary integral equations | Derives bounded, scattering, resonant, TE, and symmetry forms. |
| III | Constant-element BEM, corners, and resonance search | Gives matrix elements, singular diagonals, Newton/SVD reconstruction. |
| IV | Two coupled hexagonal cavities | Fixes all available physical parameters for Figs. 5-7. |

## Equation/Method Inventory

| ID | Source | Role | Status |
| --- | --- | --- | --- |
| BEM001 | Eqs. (1), (4)-(8) | Helmholtz equation and outgoing Hankel Green function | verified |
| BEM002 | Eqs. (6), (12)-(14) | Boundary integral and homogeneous transmission system | reconstructed orientation convention |
| BEM003 | Eqs. (31)-(34) | Constant-element collocation and singular diagonal entries | verified |
| BEM004 | Eqs. (15)-(20) | Plane-wave scattering amplitude and optical theorem | verified |
| BEM005 | Eqs. (35)-(38) | Resonance refinement, null vector, field reconstruction | verified |

## Figure Inventory

| Item | Description | Class | Decision |
| --- | --- | --- | --- |
| Fig. 1 | General multi-domain geometry | schematic_context | excluded |
| Fig. 2 | Symmetry-reduction geometry | schematic_context | excluded |
| Fig. 3 | Rounded-corner discretization sketch | algorithm_trace | excluded |
| Fig. 4 | Coupled-hexagon geometry and incident wave | schematic_context | excluded; parameters feed T001-T003 |
| Fig. 5 | Total scattering cross section `sigma/R` vs `kR` | numeric_reproduction | T001 |
| Fig. 6 | Near-field intensity at the reported complex resonance | numeric_reproduction | T002 |
| Fig. 7 | Far-field emission intensity of the same resonance | numeric_reproduction | T003 |

## Paper Parameter Contract

- two regular hexagons of side length `R`; the prose gives displacement
  `(1.8R,+0.5R)`, while Fig. 4's explicit axes place the right cavity at
  `(1.8R,-0.5R)` relative to the left cavity;
- TM polarization; `n_in=1.466`, `n_out=1`;
- incident plane wave at 15 degrees to horizontal side faces;
- scan `20 <= kR <= 25`;
- paper resolution `2N=3200` matrix unknowns (N=1600 boundary elements);
- rounded corners satisfy `rho/lambda≈0.11`, `rho/Delta s≈11.2`, but the paper
  explicitly omits the rounding/discretization formula;
- reported resonance `k_res R≈22.94444-0.09696 i`.

The omitted rounding and mesh are not an automatic fidelity failure: the paper
explicitly declares those implementations equivalent inside its printed
resolution bounds. The `N=1600` runner therefore verifies that equivalence
class. The displacement-sign conflict is different: it is an internal source
discrepancy, so the numerical-figure run follows Fig. 4 and may be called the
figure-defined publication variant, never unqualified `paper_exact` until an
independent review resolves the contradiction.
