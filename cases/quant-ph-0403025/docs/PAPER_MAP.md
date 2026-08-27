# Paper Map

## Identity

- Paper ID: `quant-ph-0403025`
- Title: *Universal quantum computation with ideal Clifford gates and noisy ancillas*
- Authors: Sergey Bravyi and Alexei Kitaev
- Source: arXiv `quant-ph/0403025v2`; Phys. Rev. A 71, 022316 (2005)
- DOI: `10.1103/PhysRevA.71.022316`
- Local PDF/source: `raw/paper.pdf`, `paper-source.tar.gz`

## Reproduction Goal

Independently reproduce every numerical plot from the published formulas and
audit every printed quantitative conclusion that supports them. The scientific
runner evaluates the five-qubit and fifteen-qubit distillation maps without
reading the PDF, EPS files, author code, or author arrays. There is no author
code or array in the source archive.

## Paper Structure

| Section | Role | Reproduction action |
| --- | --- | --- |
| I-II | Model, Clifford boundary, magic-state thresholds | Analytic threshold and fidelity checks |
| III-IV | Universal-gate construction and resource accounting | Algebraic/scaling checks |
| V | Five-qubit T-type distillation | Fig. 2(a,b), direct stabilizer-projector cross-check |
| VI | Fifteen-qubit H-type distillation | Fig. 3, Reed-Muller weight-enumerator cross-check |
| VII | Conclusions and n=11/17 code-search claim | Reproducibility audit; exact codes/results are unreported |
| Appendix | Five-qubit projector normalization | Direct matrix verification |

## Equation/Method Inventory

| ID | Source | Role | Gate |
| --- | --- | --- | --- |
| EQ001 | Sec. I, Theorems 2-3 | Fidelity/error/polarization conversion | verified |
| EQ002 | Eqs. (8)-(9) | T-basis dephasing and five-copy input | verified |
| EQ003 | Eqs. (10)-(20), Appendix | Five-qubit stabilizer projector and logical sectors | verified |
| EQ004 | Eqs. (21)-(22) | T-type success probability | verified |
| EQ005 | Eq. (23) | T-type output-error map | verified |
| EQ006 | Eqs. (29)-(34) | Fifteen-qubit Reed-Muller code spaces and enumerators | verified |
| EQ007 | Eqs. (35)-(36) | H-type success/output maps | verified |
| EQ008 | Eqs. (6), (24), (38)-(39) | Recursive yield and error scaling | verified |
| EQ009 | Sec. IV | Circuit-level resource scaling | verified |

## Figure/Table Inventory

| Paper item | Scientific class | Decision |
| --- | --- | --- |
| Fig. 1 | Bloch-sphere/octahedron schematic | excluded |
| Fig. 2 upper | T-type final error versus input error | T001 |
| Fig. 2 lower | T-type trivial-syndrome probability | T002 |
| Fig. 3 | H-type final error versus input error | T003 |
| Tables/supplement | None | no target |
| Sec. VII n=11/17 simulation sentence | Unpublished numerical claim | deferred: exact codes and results absent |

## Declared Numerical Choices

- The physical maps and thresholds are paper exact closed forms.
- The plotting grid (`2001` points on `0 <= epsilon <= 1/2`) is a declared
  rendering discretization; it does not change the scientific object.
- Roots are solved independently by bracketed bisection and checked against
  the polynomial fixed-point residual.
