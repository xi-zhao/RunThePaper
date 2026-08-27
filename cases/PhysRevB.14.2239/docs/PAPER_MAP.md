# Paper Map

## Identity

- Paper ID: `PhysRevB.14.2239`
- Title: *Energy Levels and Wave Functions of Bloch Electrons in Rational and Irrational Magnetic Fields*
- Author: Douglas R. Hofstadter
- Publication: *Physical Review B* **14**, 2239–2249 (1976)
- DOI: `10.1103/PhysRevB.14.2239`
- Local PDF: `raw/paper.pdf`
- Publisher record: APS full text; no author code, data archive or supplement

## Reproduction Goal

Independently derive and numerically reproduce every scientific display item
and every central quantitative/analytic claim that has no display carrier. All
six figures are theory/numeric: the apparently diagrammatic Fig. 2 is the
computed spectral skeleton, and Figs. 3–4 are computed rectangularizations of
recursively defined subcells.

## Paper Structure

| Section | Role | Reproduction consequence |
| --- | --- | --- |
| I–II | Physical model and Harper difference equation | Defines the clean-room numerical operator. |
| III | Transfer matrix and rational spectrum | Defines q bands, band edges and Fig. 1. |
| IV–V | Recursive cells and band counting | Defines Figs. 2–4 and quantitative recursion claims. |
| VI–VII | Irrational and field-smeared spectra | Defines Fig. 5 and the band-count bound. |
| VIII | Magnetic superlattice and wavefunctions | Defines Fig. 6, its three rational approximants and reordering. |
| IX | Experimental proposal | Textual context only; no additional numeric figure/table. |

## Equation/Method Inventory

| ID | Source location | Role | Gate |
| --- | --- | --- | --- |
| EQ001 | PDF p. 2, Eq. (1) | Harper finite-difference eigenproblem | verified |
| EQ002 | PDF pp. 2–3, Eqs. (2)–(5) | q-step transfer matrix and trace test | verified |
| EQ003 | PDF p. 3, rational-spectrum discussion | q bands and band-edge construction | verified |
| EQ004 | PDF p. 3, four spectrum properties | flux/energy symmetries and global bound | verified |
| EQ005 | PDF pp. 4–5, Statements I–III and Eqs. (6)–(8) | recursive local coordinates and rectangularization | verified |
| EQ006 | PDF p. 7, field-spread construction | union over alpha within delta-alpha | verified |
| EQ007 | PDF pp. 9–10, Eqs. (12)–(17) | magnetic-period wavefunction reordering | verified |

## Atomic Reproduction Inventory

The full-paper inventory has **8 independently adjudicable display items** and
**2 independent text-only theorem families**. One additional collection of
cross-figure checks is retained as supporting evidence and is not counted a
second time.

| Atomic item | Numerical/scientific content | Coverage |
| --- | --- | --- |
| Fig. 1 | Full rational-flux spectrum for denominators below 50 | covered by T001 |
| Fig. 2 | Unit-cell numerical skeleton through pure cases `N<=37` | covered by T002 |
| Fig. 3 | Rectangularized L2 subcell | covered by T003 |
| Fig. 4 | Rectangularized C2 subcell | covered by T004 |
| Fig. 5 | One quadrant smeared by `delta-alpha=1/100` | covered by T005 |
| Fig. 6, `alpha=1/5` series | Reordered top-edge wavefunction and eigenvalue | covered by T006 |
| Fig. 6, `alpha=2/11` series | Reordered top-edge wavefunction and eigenvalue | covered by T006 |
| Fig. 6, `alpha=17/93` series | Reordered top-edge wavefunction and eigenvalue | covered by T006 |
| **Section VI Cantor-spectrum theorem** | Irrational spectrum is uncountable, measure zero, and homeomorphic to a Cantor set | **uncovered, T008** |
| **Section VII continuity theorem family** | Spectrum is set-valued continuous; its measure is continuous at irrationals and discontinuous at rationals | **uncovered, T009** |

There are no tables or supplemental figures. Band count, symmetries, trace
edges, bounds, printed eigenvalues, and period ordering remain T007 supporting
checks of Figs. 1-6; they do not create an eleventh eligible item.

## Coverage Summary

- Eligible reproduction items: **10**.
- Covered items: **8**.
- Explicitly uncovered items: **2**.
- Coverage: **80.00%**.
- Covered-item fidelity: **89.62/100**.
- Reproduction degree: **71.70/100**.

## Uncovered Items

| Item | Direct current gap | Root-cause boundary | Next discriminating action |
| --- | --- | --- | --- |
| Section VI Cantor-spectrum theorem (T008) | No independent proof/check artifact establishes the irrational-limit topology and zero measure. | Earlier scope counted finite rational-spectrum checks but omitted this text-only central theorem; code fault remains unexcluded because no claim-specific implementation exists. | Derive the nested-cell limit independently and implement a rational-approximant/topological check. |
| Section VII continuity theorem family (T009) | No independent artifact tests set-valued spectral convergence separately from spectral-measure convergence. | Earlier scope treated finite rational plots as coverage of a limiting theorem; code fault remains unexcluded until a continuity oracle exists. | Test rational-approximant sequences for set convergence and Lebesgue-measure behavior at rational and irrational flux. |

## Explicit Reconstruction Choices

- The paper fixes `q<50` in Fig. 1, `N<=37` in Fig. 2 and
  `delta-alpha=1/100` in Fig. 5.
- It does not print the rational cutoff or raster resolution for Figs. 3–5.
  We use `q<=79` and a 480x480 Fig. 5 grid as convergence/render choices;
  these never become paper-exact claims.
