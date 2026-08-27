# Paper Map

## Identity

- Paper ID: `2401.08523`.
- Title: *Information and Majorization Theory for Fermionic Phase-Space Distributions*.
- Authors: Nicolas J. Cerf and Tobias Haas.
- Publication: *Physical Review Letters* **135**, 110201 (2025), DOI `10.1103/3qg7-r4mq`.
- Frozen source: arXiv `2401.08523v2`, submitted 2025-09-25.
- Local PDF: `raw/arxiv-2401.08523v2.pdf`.
- Local source: `paper-source/main.tex` and `paper-source/sm.tex`.

## Reproduction Goal

Follow the complete single-mode argument, verify its formula chain, and
independently regenerate every numerical figure and subpanel. The paper has two
main figures and four numerical panels in total; the supplement has no figures.
The source vectors are used only after generation for layout and pixel evidence.

## Core Scientific Model

The parity superselection rule reduces a physical single fermionic mode to one
state variable, the occupation `n` in `[0,1]`. From this one variable the paper
derives three Grassmann supernumbers `P`, `W`, and `Q`. Their common soul fixes
normalization, while their three ordinary bodies fix majorization, covariance
determinants, Rényi entropies, and channel dynamics. This single deep model is
the architecture of the case; plotting is only a downstream view.

## Paper Structure

| Section | Role | Reproduction treatment |
| --- | --- | --- |
| Introduction | motivation and bosonic comparison | read and mapped; no numeric target |
| Single fermionic mode | operator/state domain | EQ001 |
| Physical states and Gaussianity | superselection and thermal form | EQ001, Fig. 1 |
| Coherent states / phase-space distributions | construct `P/W/Q` | EQ002 and Supplement (b-d) |
| Majorization relations | central order theorem | EQ003 and Supplement (e) |
| Second moments | covariance uncertainty | EQ004, Fig. 2(a) |
| Entropies | Rényi/Shannon uncertainty | EQ005-EQ006, Fig. 2(b-c) |
| Appendix A | cloning/broadcasting application | analytic audit; no figure |
| Appendix B | thermal loss channel | EQ007 numeric validation |
| Supplement (a-g) | detailed derivations | fully audited; no additional figures |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | main Eq. (2), Fig. 1 | physical thermal state and Fermi-Dirac curve | verified |
| EQ002 | main Eq. (6), SM (b-d) | `P/W/Q` bodies and common soul | verified |
| EQ003 | main Eqs. (7-11), SM (e) | majorization identity and chains | verified |
| EQ004 | second-moment section | covariance determinants | verified |
| EQ005 | entropy section, SM (g) | Rényi and Shannon entropies | verified |
| EQ006 | entropy bounds and Fig. 2 caption | uncertainty bounds and crossings | verified |
| EQ007 | Appendix B | thermal loss channel | verified |
| MTH001 | all numeric targets | deterministic formula-grid evaluation | verified |

## Figure/Table Inventory

| Item | Caption summary | Class | Decision |
| --- | --- | --- | --- |
| Main Fig. 1 | Fermi-Dirac occupation, positive/negative `T` | numeric reproduction | T001, complete |
| Main Fig. 2(a) | `det gamma(P/W/Q)` | numeric reproduction | T002, complete |
| Main Fig. 2(b) | Shannon `S(P/W/Q)` | numeric reproduction | T002, complete |
| Main Fig. 2(c) | `S_r(W)` for five orders | numeric reproduction | T002, complete |
| Tables | none | not applicable | none |
| Supplement figures | none | not applicable | none |

## Assumptions And Conventions

- Natural units `hbar=k_B=1` follow the paper.
- Berezin integration uses the innermost-first convention
  `int d alpha* d alpha alpha alpha*=+1`.
- Exact singularities at zero supernumber body are retained as `+inf` in the
  CSV and merely clipped by the visible plot boundary.
- The source's visible grids set sampling density and canvas geometry, not the
  scientific values.
- No source pixels, vector paths, or digitized curve points enter generation.
