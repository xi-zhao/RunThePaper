# Paper Map

## Identity

- Paper ID: `2305.15556`
- Title: *Optimal Generators for Quantum Sensing*
- Authors: Jarrod T. Reilly, John Drew Wilson, Simon B. Jäger, Christopher
  Wilson, and Murray J. Holland
- Source: arXiv:2305.15556v2; Phys. Rev. Lett. 131, 150802 (2023),
  DOI `10.1103/PhysRevLett.131.150802`
- Local PDF: `raw/paper.pdf`
- Local source: `raw/arxiv-source.tar`, with text-only TeX members under
  `raw/tex/`

## Reproduction Goal

Independently reconstruct the fixed-N symmetric SU(2) and SU(4) quantum
dynamics, evaluate the full pure-state QFIM, and reproduce every numerical
panel in Main Figs. 1 and 2. The Supplemental commutative diagram is schematic
and excluded. Author figures are reference-only after numerical freeze.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main formalism | QFIM and optimal-generator theorem | Rayleigh-Ritz problem for a normalized operator basis |
| Main SU(2) example | one-axis twisting | exact N=20 symmetric-spin dynamics and Husimi-Q surfaces |
| Main SU(4) example | three-axis twisting | N=20 four-mode symmetric-boson dynamics, 1771 states |
| Main multiparameter section | commuting optimal generators | quantitative anchors at `chi t=pi/4` |
| Supplement Sec. I | normalized SU(n) operator basis | fixes Cartan directions and trace norm |
| Supplement Sec. II | unitary connection | analytic context; no numerical figure |
| Supplement Sec. III | physical SU(4) realization | fixes basis labels, Hamiltonian, and initial state |
| Supplement Sec. IV | geometric derivation | derives covariance QFIM and Killing-form normalization |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Main Eqs. (1)-(5), Supp. Eqs. (S34),(S43) | pure-state QFIM | verified |
| EQ002 | Main Eq. (3), Supp. final geometric argument | optimal-generator eigenproblem | verified |
| EQ003 | Main Eq. (9), Supp. Sec. I and Eq. (S44) | SU(n) operator normalization | verified |
| EQ004 | Main Eqs. (6)-(7) | OAT state evolution | verified |
| EQ005 | Main Eq. (8) and following paragraph | analytic OAT QFI and generator angle | verified |
| EQ006 | Main Eq. (10), Supp. Eqs. (S12)-(S18) | SU(4) dynamics and initial state | verified |
| EQ007 | Main multiparameter paragraph | commuting-generator anchors | source-only quantitative cross-check |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Main Fig. 1(a) | initial SU(2) Husimi-Q sphere | numeric | T001 |
| Main Fig. 1(b) | optimally squeezed SU(2) Husimi-Q sphere | numeric | T002 |
| Main Fig. 1(c) | three QFIM eigenvalues and analytic OAT curve | numeric | T003 |
| Main Fig. 1(d) | optimal-generator path on the Bloch sphere | numeric | T004 |
| Main Fig. 2(a) | eight largest SU(4) QFIM eigenvalues and subgroup bound | numeric | T005 |
| Main Fig. 2(b) | coefficients of a deterministic optimal-generator representative | numeric | T006; gauge-sensitive at degeneracy |
| Supplement Fig. S1 | maps among group, Hilbert, and state manifolds | schematic | excluded |

## Assumptions

- Fixed total particle number and fully symmetric bosonic subspace.
- Dimensionless time `tau=chi t`; the plotted horizontal coordinate is
  `2 tau/pi`.
- QFIM basis vectors have equal trace norm in the N-particle symmetric
  representation.
- At a degenerate leading eigenvalue, the optimal vector is not unique; only
  its eigenspace is gauge invariant.
- The explicit initial ket in the main text is authoritative for numerics. The
  adjacent prose calls it a simultaneous `J_x` and `K_y` eigenstate, while
  direct operator evaluation indicates `J_x` and `K_z`; this is a formal
  consistency item to falsify rather than silently correct.
