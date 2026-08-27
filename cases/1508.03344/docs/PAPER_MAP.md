# Paper map

## Identity and scientific core

- Paper ID: `1508.03344`.
- Published as: PRL 116, 250401 (2016).
- Source: `raw/paper.pdf` and `paper-source.tar.gz`.
- Scientific core: exact diagonalization of two disordered binary-driven Ising
  chains, with Floquet eigenphase statistics and eigenstate-order diagnostics.

## Complete numerical inventory

| Item | Numerical content | Target |
| --- | --- | --- |
| Fig. 1 main | disorder-averaged adjacent-gap ratio versus mean log-coupling, `L=8,10,12` | T001 |
| Fig. 1 inset | disorder/eigenstate-averaged spin-glass susceptibility versus mean log-coupling | T002 |
| Fig. 2(a) | analytic free-uniform binary-drive phase diagram | T003 |
| Fig. 2(b) | interacting pi-phase level statistics versus `J_z`, `L=8,10,12` | T004 |
| Fig. 2(c) | pi-SG and zero-SG spin-raising spectral functions for seven interaction values | T005 |
| Fig. 2(d) | time-dependent `C_xx` and `C_yy` in a single pi-SG eigenstate | T006 |
| text/captions | Poisson/COE anchors, localization threshold, spectral-peak positions and two micromotion crossings | supporting checks covered by T001–T006; not a separate denominator item |

There is no supplemental file and no table. Both published figures are fully
numerical; there are no experimental panels. The six displayed numerical items
are the complete denominator, while the results-text claims are retained as
supporting checks of those same objects.

## Equation and method inventory

| ID | Source | Role |
| --- | --- | --- |
| EQ001 | Floquet formalism, Eqs. (1)-(2) | one-period unitary and quasienergies |
| EQ002 | driven Ising model, Eqs. (3)-(4) | Fig. 1 disorder campaign |
| EQ003 | text below Eq. (4) | adjacent-gap ratio |
| EQ004 | Eqs. (5)-(6) | spin-glass correlator and susceptibility |
| EQ005 | Eq. (7) | operator spectral function |
| EQ006 | Eqs. (8)-(9) | pi-phase binary drive |
| EQ007 | Fig. 2(a) and free-fermion limit | four analytic phase sectors |

## Publication ambiguities frozen for review

- Eq. (8) defines `T=T1+T2`, while the numerical paragraph prints `T=1` and
  `T2=pi/2`; Fig. 2(d) separately prints `T1=1`. These cannot all hold.
- Eq. (7) prints a matrix element without an absolute square, although the
  plotted spectral function is real and non-negative.
- The displayed `H_x` leaves the site index in its `J_z sigma_z sigma_z` term
  outside an explicit summation; the preceding Hamiltonian and `H_z` establish
  the intended nearest-neighbor sum.

These are review findings, not self-declared paper errors. Each admissible
interpretation remains explicit in code or in the falsification ledger.
