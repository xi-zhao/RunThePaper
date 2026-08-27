# Figure Classification

Every numerical subpanel in the main text and embedded supplement is either an
executable formula-derived target or an explicit blocker. Source panels are never
numerical inputs.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1(a) | schematic_context | no | Qualitative spin-split band sketch. |
| Main Fig. 1(b) | schematic_context | no | Atomic stacking sketch. |
| Main Fig. 1(c) | numeric_reproduction | deferred | DFT calculation lacks exact QE/pseudopotential/structure metadata. |
| Main Fig. 1(d) | numeric_reproduction | T001 | Analytic first-shell potential. |
| Main Fig. 2(a) | numeric_reproduction | T002 | Continuum bands and tight-binding fit. |
| Main Fig. 2(b) | numeric_reproduction | T003 | DOS and dual filling/density axes. |
| Main Fig. 2(c) | numeric_reproduction | T004 | Bloch-derived Wannier function. |
| Main Fig. 2(d) | numeric_reproduction | T005 | Hopping sweep. |
| Main Fig. 3(a) | numeric_reproduction | T006 | Screened interactions and U0/t1. |
| Main Fig. 3(b) | numeric_reproduction | T007 | Exchange couplings and J2/J1. |
| Main Fig. 4(a) | numeric_reproduction | T008 | Energy and Fermi contours. |
| Main Fig. 4(b) | schematic_context | no | Magnetic lattice drawing. |
| Main Fig. 4(c) | schematic_context | no | Magnetic-order drawing. |
| Supplement Fig. 5(a) | numeric_reproduction | T009 | Mismatch-system potential. |
| Supplement Fig. 5(b) | numeric_reproduction | T010 | Mismatch-system bands. |
| Supplement Fig. 5(c) | numeric_reproduction | T011 | Mismatch-system hopping sweep. |
| Supplement Fig. 5(d) | numeric_reproduction | T012 | Mismatch-system interactions. |

## Atomic coverage result

- displayed panels: 17;
- eligible numerical panels: 13;
- covered panels: 12;
- uncovered panels: 1;
- excluded schematics: 4;
- coverage: **12/13 = 92.31%**.

## Uncovered item

| Item | Direct cause | Root cause | Code assessment | Next action |
| --- | --- | --- | --- | --- |
| `main_fig1c_dft_displacement_map` / `D001` | The paper does not provide the exact Quantum ESPRESSO version, relativistic pseudopotentials, relaxed coordinates, cutoffs, k mesh, or convergence tolerances needed to generate the displacement-dependent DFT map. | `publication_underspecified`: the fitted continuum-model parameters cannot reconstruct the upstream first-principles array. | `not_applicable`: without a unique input contract there is no paper-exact implementation to test; passing downstream continuum checks do not close D001. | Obtain and hash-bind a citable DFT benchmark contract, then implement and converge it independently without author numerical code. |

The machine-readable mirror is `figure_coverage.json`.
