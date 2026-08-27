# Paper Map

## Identity

- Paper ID: `1807.10084`
- Title: *Nonreciprocal Photon Blockade*
- Authors: Ran Huang, Adam Miranowicz, Jie-Qiao Liao, Franco Nori, Hui Jing
- Publication: *Physical Review Letters* **121**, 153601 (2018)
- DOI: `10.1103/PhysRevLett.121.153601`
- Source: arXiv:1807.10084v2, submitted 26 July 2018, revised 16 October 2018
- Local PDF: `raw/paper.pdf` (Letter and Supplementary Material, 36 pages)
- Local source: `paper-source/extracted/arXiv_V2.tex`
- Original figure assets: 4 main and 9 supplementary PDF figures, reference-only

## Reproduction Goal

Independently derive and solve the driven dissipative Kerr-resonator model and
reproduce every numerical or formula-derived theoretical panel in the Letter
and Supplementary Material. The numerical generator may use only explicit
configuration and independently written code. It may not read the PDF, TeX,
original figures, digitized curves, author code, or author-generated arrays.

Illustrative device artwork and literature-summary content are context rather
than numerical targets. In mixed figures, only the formula-derived energy
levels, correlations, probabilities, and parameter relations are reproduced.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main: Model | Defines Fizeau shift, driven Kerr Hamiltonian and level energies | Core direction/sign convention |
| Main: Analytical results | Weak-drive amplitudes and equal-time correlations | Independent limiting reference |
| Main: Numerical results | Lindblad steady state and paper parameters | Core numerical generator |
| Main: nonreciprocal 2PB / 1PB-2PB | Higher-order correlations and distributions | Main Figs. 3-4 |
| SM S1: Kerr interaction and Fizeau drag | Derives rotating-frame model | Includes Supplement Fig. S1 |
| SM S2: Photon blockade effects | PB/PIT criteria, energy diagrams and distributions | Supplement Figs. S2-S5 and Tables S1-S2 |
| SM S3: Analytic correlations | Derives approximate g2 and g3 | Supplement Fig. S6 |
| SM S4: Rotation-induced nonreciprocity | Directional shifts and complete case map | Supplement Figs. S7-S9 |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Main Eq. (1); SM Eqs. (S2-S3) | Fizeau frequency shift | verified |
| EQ002 | Main Eqs. (2-3); SM Eqs. (S4-S7) | Kerr Hamiltonian and Fock energies | verified |
| EQ003 | Main text after Eq. (2) | Physical U, gamma and drive mappings | verified |
| EQ004 | Main Eq. (8) | Lindblad master equation | verified |
| EQ005 | Main text and SM definitions | P(n), mean n and factorial correlations | verified |
| EQ006 | Main Eqs. (6-7, 10); SM analytic section | Weak-drive g2/g3 references | verified |
| EQ007 | Main Eq. (9); SM PB/PIT criteria | PB/PIT and Poisson-deviation diagnostics | verified |
| EQ008 | Derived from Eq. (8) | Column-vectorized steady-state solve | verified |

## Atomic Figure/Table Inventory

The 36-page source was read through the end of the embedded Supplement. The
machine contract now records 65 independently identifiable display items: 62
theoretical numerical items and three contextual exclusions. A zoom that uses
the same frozen array is not counted again unless the paper labels it as a
separate subpanel with an independently testable scientific criterion.

| Paper location | Atomic display items | Eligible theory items | Excluded context | Target |
| --- | ---: | ---: | ---: | --- |
| Main Fig. 1(a,b) | 4 | 2 directional energy diagrams | 2 device schematics | T001 |
| Main Fig. 2 | 1 | 1 correlation panel | 0 | T002 |
| Main Fig. 3(a-d) | 7 | 7 panels/axes/directional diagrams | 0 | T003-T004 |
| Main Fig. 4(a-c) | 5 | 5 panels/axes/distributions | 0 | T005 |
| Supplement Fig. S1 | 1 | 1 Fizeau-shift panel | 0 | T006 |
| Supplement Fig. S2(a,b) | 2 | 2 energy diagrams | 0 | T007 |
| Supplement Fig. S3(a-h) | 16 | 16 directional level diagrams | 0 | T008 |
| Supplement Fig. S4(a-c) | 8 | 8 labeled diagnostic subpanels | 0 | T009 |
| Supplement Fig. S5(a-c) | 8 | 8 labeled diagnostic subpanels | 0 | T010 |
| Supplement Fig. S6 | 2 | g2 and g3 analytic/numerical families | 0 | T011 |
| Supplement Fig. S7(a,b) | 2 | 2 directional rotation sweeps | 0 | T012 |
| Supplement Fig. S8 | 1 | 1 directional correlation panel | 0 | T013 |
| Supplement Fig. S9(a-d) | 6 | 2 correlation panels and 4 distribution cases | 0 | T014 |
| Supplement Table I | 1 | 0 | 1 literature synopsis | — |
| Supplement Table II | 1 | 1 eight-row resonance table | 0 | T015 |
| **Total** | **65** | **62** | **3** | **T001-T015** |

No additional quantitative claim enters the denominator: the paper's printed
correlation values, resonance conditions, and allowed/prohibited cases are all
already represented by these display items. They remain available as
supporting scientific checks without being double-counted.

## Assumptions

- Frequencies are represented consistently as angular-frequency numbers; the
  paper labels the numerical values in kHz/MHz without an extra 2pi conversion.
- The small refractive-index dispersion term in the Fizeau shift is omitted,
  matching the paper's plotted relation and its statement that the correction
  is at most about one percent.
- The exact Lindblad steady state is converged in a truncated Fock basis; the
  cutoff is increased until omitted population and observable changes pass
  explicit checks.
- The paper does not publish author numerical arrays or random seeds. This is a
  deterministic single-mode model, so independent equation-level comparison
  is the scientific reference.
