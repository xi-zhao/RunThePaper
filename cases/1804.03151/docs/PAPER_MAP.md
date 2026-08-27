# Paper Map

## Identity

- Paper ID: `1804.03151`
- Title: *Hubbard model physics in transition metal dichalcogenide moire bands*
- Authors: Fengcheng Wu, Timothy Lovorn, Emanuel Tutuc and A. H. MacDonald
- Publication: *Physical Review Letters* **121**, 026402 (2018)
- DOI: `10.1103/PhysRevLett.121.026402`
- Local PDF: `raw/paper.pdf`
- Local source: `paper-source/Moire_Hubbard_arXiv.tex`

## Reproduction Goal

Follow the complete continuum-to-Hubbard derivation and independently reproduce every
numerical panel in the article and its embedded supplement. Main Fig. 1(c) is retained
as an explicit DFT blocker because the source does not identify the exact first-principles
environment. Pure schematics are outside numerical scope.

## Paper Structure

| Section | Role | Numerical consequence |
| --- | --- | --- |
| Moire potential | Reduces the heterobilayer to a scalar effective-mass Hamiltonian | T001-T003, T008-T010 |
| Hubbard model | Builds Wannier orbitals, hoppings and screened interactions | T004-T006, T011-T012 |
| Half filling | Maps the Hubbard model to a frustrated spin model | T007 |
| Three-quarter filling | Identifies the nested Fermi contour | T008 |
| Supplement: WSe2/MoS2 | Adds lattice mismatch to the same model | T009-T012 |
| Supplement: potential discussion | Qualifies the DFT approximation | D001 blocker rationale |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Main Eq. (1) and following text | Geometry and first-shell potential | verified |
| EQ002 | Main Eq. (2) | Plane-wave Hamiltonian | verified |
| EQ003 | Main Eq. (3) | Triangular tight-binding reduction | verified |
| EQ004 | Fig. 2(c) discussion | Bloch-to-Wannier transform | verified |
| EQ005 | Image-charge paragraph and Eq. (4) | Screened interaction projection | verified |
| EQ006 | Fig. 2(b) discussion | DOS and filling-density conversion | verified |
| EQ007 | Text after Eq. (5) | Strong-coupling exchanges | verified |
| EQ008 | Three-quarter-filling section | Fermi contour and nesting | verified |
| EQ009 | Supplement Eq. (6) | Mismatch-system geometry | verified |

## Figure/Table Inventory

| Paper item | Classification | Decision |
| --- | --- | --- |
| Main Fig. 1(a) | schematic context | excluded |
| Main Fig. 1(b) | schematic context | excluded |
| Main Fig. 1(c) | numerical DFT | D001, uncovered: missing benchmark metadata |
| Main Fig. 1(d) | numerical potential | T001 |
| Main Fig. 2(a-d) | bands, DOS, Wannier, hopping | T002-T005 |
| Main Fig. 3(a,b) | interactions and exchanges | T006-T007 |
| Main Fig. 4(a) | energy/Fermi contours | T008 |
| Main Fig. 4(b) | magnetic-lattice schematic | excluded |
| Main Fig. 4(c) | magnetic-order schematic | excluded |
| Supplement Fig. 5(a-d) | mismatch potential, bands, hopping, interactions | T009-T012 |

The seven-page PDF, including the embedded supplement through Supplement Fig. 5,
has a complete panel-level inventory: 17 displayed panels, 13 eligible numerical
panels, 12 covered panels and one explicitly uncovered panel. Four quantitative
text claims support those panel items and are not double-counted in the denominator.

### D001 boundary

Main Fig. 1(c) is not hidden under a generic deferred label. Its direct blocker is
the absent executable first-principles contract: exact Quantum ESPRESSO version,
fully relativistic pseudopotentials, relaxed atomic coordinates, basis and density
cutoffs, k-point mesh and convergence tolerances. The root cause is publication
underspecification, not a demonstrated code error or a compute shortage. More GPU
capacity cannot infer the missing inputs. Closing D001 requires a citable, hash-bound
benchmark contract followed by an independent converged implementation that does
not consult author numerical code.

## Assumptions

- The printed effective mass and first Fourier shell define the continuum model.
- Twist angles use radians in `a_M=a_0/theta`; degrees are converted at the boundary.
- Unspecified reciprocal and real-space discretizations are declared in config and tested for the main spectral observable.
- The top isolated band admits a smooth phase gauge centered on a potential maximum.
- The image-charge formula is evaluated with the paper's `D=3 nm`; plotted `epsilon U` is kept independent of the chosen dielectric, while exchange uses `epsilon=10` as in the caption.
