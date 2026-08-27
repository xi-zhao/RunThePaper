# Paper Map — Boundary time crystals

## Identity

- Paper ID: `1708.05014`
- Title: *Boundary time crystals*
- Authors: F. Iemini, A. Russomanno, J. Keeling, M. Schirò, M. Dalmonte, R. Fazio
- Venue: Physical Review Letters 121, 035301 (2018)
- DOI: `10.1103/PhysRevLett.121.035301`
- Local PDF: `raw/paper.pdf`
- Local source: `paper-source/arxiv_v2_main.tex`

## Scientific Claim Graph

1. Collective drive and collective decay define an exactly finite-dimensional Liouvillian in the symmetric spin sector.
2. For `omega_0/kappa < 1`, the leading Liouvillian spectrum is gapped and non-oscillatory.
3. For `omega_0/kappa > 1`, leading real parts close with size while nonzero imaginary bands remain, producing increasingly persistent oscillations.
4. The `N_b -> infinity` equations conserve spin length and support closed orbits; perturbations `omega_x, omega_z` modify but need not destroy them.

## Equation/Method Inventory

| ID | Source | Numerical role | Gate |
| --- | --- | --- | --- |
| EQ001 | collective-spin definitions | symmetric spin matrices | verified |
| EQ002 | main Eq. (2), supplement Eq. (S1) | sparse Liouvillian | verified |
| EQ003 | main Figs. 1 and 4 | propagation and FFT | verified |
| EQ004 | main Figs. 2–4, supplement spectra | eigenvalue observables | verified |
| EQ005 | supplement NESS section | moments and variances | verified |
| EQ006 | supplement Eq. (S7) | semiclassical trajectories | verified |
| EQ007 | supplement conserved quantities | phase coordinates and branch cut | verified |

## Complete Figure Inventory

| Paper item | Scientific content | Decision |
| --- | --- | --- |
| Main Fig. 1(a,b) | bulk-boundary schematic | excluded as non-numeric |
| Main Fig. 1(c) | finite-size and thermodynamic magnetization | target T001 |
| Main Fig. 2 left/right plus both insets | full Liouvillian spectra and leading-mode zooms | targets T002–T005 |
| Main Fig. 3 left/right | real-part scaling and imaginary bands | targets T006–T007 |
| Main Fig. 4 left, inset, right | Fourier peaks, thermodynamic FFT, decay scaling | targets T008–T010 |
| Supplement chain-mapping Fig. S1 | three conceptual schematics | excluded as non-numeric |
| Supplement Fig. S2 left/right | NESS moments and variances | targets T011–T012 |
| Supplement Fig. S3 left/right | strong/weak real-part scaling | targets T013–T014 |
| Supplement Fig. S4 | lowest oscillatory excitation | target T015 |
| Supplement Fig. S5(a–d) | four `omega_z` phase portraits | targets T016–T019 |
| Supplement Fig. S6 | conserved-R field, trajectories, branch cut | target T020 |
| Supplement Fig. S7(a–d) | four `omega_x,omega_z` phase portraits | targets T021–T024 |

The source archive contains TeX and rendered figure assets only. It contains no author program, notebook, numerical table, or curve array. Original figure assets are reference-only and are absent from the isolated numerical input bundle.
