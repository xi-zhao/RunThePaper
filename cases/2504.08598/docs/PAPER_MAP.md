# Paper Map

## Identity

- Paper ID: `2504.08598`
- Publication: *Quantum Science and Technology* 11 (2), 025012 (2026)
- DOI: `10.1088/2058-9565/ae3b6d`
- Local paper: `raw/paper.pdf`
- Author data: `raw/supplementary/Dataset.zip`

## Reproduction Goal

Independently reconstruct the complete graph-coloring-to-Rydberg-qudit chain,
execute Eq. (3) at the paper parameters, compare only after generation against
the author CSVs, and produce an explicit H005 hardware handoff.

## Paper Structure

| Section | Role |
| --- | --- |
| 1-3 | MVGCP and Potts-like mapping |
| 4 | Qudit Hamiltonian and annealing schedule |
| 5 | Main k=3 equidistant graphs A-F |
| 6 | Main k=4 K4 embeddings G-I |
| 7 | Experimental feasibility |
| Appendix A | Parameters, coordinates, robustness |
| Appendix B | k=chi-1 and non-equidistant failure modes |

## Equation/Method Inventory

| ID | Source | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Eq. (2) | Potts-like coloring objective | verified |
| EQ002 | Eq. (3) | multilevel Hamiltonian | verified |
| EQ003 | Eq. (4) | encoding inequalities | verified with counterexamples |
| EQ004 | Eqs. (5)-(6) | 8.4 us controls | verified |
| MTH001 | Sec. 4.3 | 300-sample sparse evolution | executed |
| MTH002 | Tables 1-2 | coordinates and spacings | verified with sqrt(2) note |
| MTH003 | Dataset DOI | post-generation comparison | executed |

## Scientific Claim Scope

| Claim | Importance | Mode | Status |
| --- | --- | --- | --- |
| CLM001 native graph-to-qudit mapping | central | derivation | verified |
| CLM002 k=3 A-F behavior | central | simulation | feature reproduced |
| CLM003 k=4 G-I behavior | central | simulation | feature reproduced |
| CLM004 k=chi-1 limitations | supporting | simulation | partial with named mismatches |
| CLM005 H005 hardware requirements | supporting | hardware boundary | verified as future capability |
| CLM007 Figure 7 drive-protocol robustness | supporting | simulation | blocked by conflicting protocol-c source parameters |

## Figure/Table Inventory

| Item | Class | Decision |
| --- | --- | --- |
| Figures 1-4 | schematic/context | excluded |
| Figure 5 | theory/numerical | T001 |
| Figure 6 | theory/numerical | T002 |
| Figure 7 | theory/numerical | blocked by protocol-c source conflict |
| Figures 8-9 | theory/numerical | T003 with named failures |
| Tables 1-2 | parameter tables | audited source inputs |

## Assumptions and Boundaries

- Closed, noiseless, additive pair-interaction model as printed.
- Local basis is `|g>,|r1>,...,|rk>`; CSV state-index convention is undisclosed,
  so raw-index and sorted-distribution TVD are both retained.
- Table-2 tetrahedron value is physical edge length.
- Source data is validation-only.
- Pasqal's qubit backend is not equivalent to this multilevel Hamiltonian.
