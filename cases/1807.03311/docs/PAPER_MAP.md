# Paper Map

## Identity

- Paper ID: `1807.03311`
- Title: *Topological insulators in twisted transition metal dichalcogenide homobilayers*
- Authors: Fengcheng Wu, Timothy Lovorn, Emanuel Tutuc, Ivar Martin, A. H. MacDonald
- Publication: *Physical Review Letters* 122, 086402 (2019)
- DOI: `10.1103/PhysRevLett.122.086402`
- Source: `https://arxiv.org/abs/1807.03311`, arXiv v2
- Local PDF: `raw/paper.pdf` (`sha256:537cdc8b2271cd2ded0b6760916801c983c504d896984efdb7eece9715c8daae`)
- Local TeX: `raw/arxiv-source.tar` (`sha256:1435212518862b3724388f91dd4d769074aa46bb029d953f0917c216f484ac20`)

## Reproduction Goal

Independently derive and calculate every formula-generated numerical panel in the main text and supplement. Original figure assets are inventory and post-freeze rendering references only. Main/supplement schematics are excluded. The two first-principles DFT panels remain explicitly deferred because they require a separate fully relativistic Quantum Espresso/Wannier workflow and exact pseudopotential metadata.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main: aligned bilayers | derives local layer potentials and interlayer tunneling | Eqs. (1)-(3), fitted MoTe2 parameters |
| Main: moire Hamiltonian | promotes local displacement to a periodic continuum model | Eq. (4), plane-wave diagonalization |
| Main: topological bands | pseudospin skyrmion, Chern bands, DOS, Kane-Mele mapping | Eqs. (5)-(7), Figs. 2-3 |
| Main: phase diagram | angle- and layer-bias-driven transitions | Fig. 4 |
| Supplement: DFT | establishes aligned-bilayer parameters | external QE/Wannier calculation, deferred |
| Supplement: remote conduction | four-band massive-Dirac robustness check | independently executed |
| Supplement: remote spin bands | layer x spin robustness check | independently executed |
| Supplement: interactions/AB stacking | analytic discussion and schematics | no additional numerical figure |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | geometry preceding main Eq. (4) | moire direct/reciprocal vectors and kappa shifts | verified |
| EQ002 | main Eq. (2) | layer-resolved lowest-harmonic potential | verified |
| EQ003 | main Eq. (3) | interlayer tunneling harmonics | verified |
| EQ004 | main Eq. (4) | two-band plane-wave continuum Hamiltonian | verified |
| EQ005 | main Eqs. (5)-(6) | pseudospin field and winding | verified |
| EQ006 | main Fig. 3 text | DOS, Kubo curvature, Chern number, global gaps | verified |
| EQ007 | main Eq. (7) | Kane-Mele/Haldane tight-binding comparison | verified |
| EQ008 | supplement remote-conduction section | conduction/valence massive-Dirac model | verified |
| EQ009 | supplement remote-valence section | layer x spin model and spin-mixing tunneling | verified |

## Atomic Figure Inventory

The complete ten-page source contains 24 independently identifiable display
items. Sixteen are theoretical numerical items; fourteen are bound to existing
independent data and two first-principles panels are explicitly uncovered.

| Paper location | Atomic items | Eligible theory | Excluded | Mapping |
| --- | ---: | ---: | ---: | --- |
| Main Fig. 1(a,b) | 3 | 0 | 3 schematics | — |
| Main Fig. 2(a,b) | 2 | 1 | 1 schematic | T001 |
| Main Fig. 3(a-d) | 5 | 4 | 1 schematic | T002-T004 |
| Main Fig. 4(a-c) | 5 | 5 | 0 | T005-T007 |
| Supplement Fig. 5(a,b) | 2 | 2 uncovered DFT panels | 0 | D001-D002 |
| Supplement Fig. 6(a,b) | 2 | 2 | 0 | T008-T009 |
| Supplement Fig. 7(a,b) | 2 | 2 | 0 | T010-T011 |
| Supplement Fig. 8(a,b) | 3 | 0 | 3 schematics | — |
| **Total** | **24** | **16** | **8** | **14 covered, 2 uncovered** |

Main Fig. 3(a) is split into continuum and tight-binding series; Fig. 4(b)
into the two independently closable gaps; and Fig. 4(c) into continuum and
tight-binding boundaries. These series can receive different scientific
verdicts and therefore cannot remain hidden inside whole-figure groups.

## Assumptions And Boundaries

- Small-angle relation `a_M=a0/theta` is used exactly as printed.
- The common plane-wave energy zero is arbitrary; the TB overlay receives one recorded constant energy-zero shift only.
- Main panels use complete reciprocal shells through cutoff 4; the angle/bias sweep uses cutoff 4 and finite 9x9/7x7 momentum meshes.
- Source TeX is used to understand equations and parameters. No author numerical code, arrays, vector coordinates, or pixel samples feed the runner.
- The two DFT panels are blocked by missing scientific inputs, not by available
  compute. More CPU/GPU cannot infer unpublished pseudopotentials, relaxed
  coordinates, convergence settings or Wannier windows.
- The final lifecycle remains partial while D001-D002, parameter provenance,
  paper-scale evidence where needed, and independent fresh-context review are open.
