# Paper Map

## Identity

- Paper ID: `1711.09418`
- Title: *Symmetry-Resolved Entanglement in Many-Body Systems*
- Authors: Moshe Goldstein and Eran Sela
- Publication: *Physical Review Letters* **120**, 200602 (2018)
- DOI: `10.1103/PhysRevLett.120.200602`
- Source: arXiv PDF and TeX source frozen under `raw/`
- Source SHA-256: PDF `2cff4934d825edc96f07deb9156a04f36b0c5151efeae5ffedcc083982d732b0`; archive `807d0e2d5406bee918a271233344f17adbe19970cdf38f97f454be1b89e89d65`

## Reproduction Goal

Follow the full U(1) derivation, independently implement the free-fermion lattice calculation, and reproduce every numerical result in Main Figs. 2 and 3. Main Fig. 1 is a conceptual schematic and is excluded from numerical reproduction. No author implementation or numerical array is used.

## Paper Structure

| Section | Role | Reproduction consequence |
| --- | --- | --- |
| Symmetry-resolved Rényi entropy | Defines charged moments and sector projection | EQ002 |
| U(1) Luttinger liquid | Derives charged-moment scaling | EQ003 and EQ005 |
| Free-fermion lattice check | Supplies the independent correlation kernel | EQ001, T001, T002 |
| Entanglement spectrum | Derives sector largest eigenvalues and integrated density | EQ004-EQ005, T002 |
| SU(2) extension | Generalization discussed without a numerical figure | Context only |
| Discrete symmetry / critical Ising chain | Prints a parity-sector formula and says it was numerically verified, but discloses no numerical setup or artifact | Formula-level sanity only; paper-exact author verification unavailable |
| Supplemental Material S.A | Derives the composite twist-field scaling dimension | Derivation support; no numeric item |
| Supplemental Material S.B | Derives the integrated eigenvalue density used by Eq. (11) | EQ005 support; no separate figure/table |

## Equation And Method Inventory

| ID | Source | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Free-fermion paragraph before Fig. 2 | Correlation matrix | verified |
| EQ002 | Eqs. (2)-(4) | Charge projection | verified |
| EQ003 | Eqs. (6)-(8), Fig. 2 discussion | Analytic Fig. 2 curves | verified |
| EQ004 | Product-density-matrix paragraph, Fig. 3 caption | Numerical spectrum | verified |
| EQ005 | Eq. (11) | Analytic Fig. 3 curves | verified |
| NUM001 | Toeplitz partial eigensolver plus charge recurrence | T001 | verified |
| NUM002 | 24-mode many-body enumeration plus quadrature | T002 | verified |

## Figure Inventory

| Item | Content | Class | Decision |
| --- | --- | --- | --- |
| Main Fig. 1 | Flux-insertion/symmetry-resolution concept | schematic_context | excluded |
| Main Fig. 2 | Charge distribution and entropy contribution | numeric_reproduction | T001 |
| Main Fig. 3 | Integrated entanglement spectrum by charge | numeric_reproduction | T002 |

The source archive contains exactly three figure files (`fig1plus.pdf`,
`fig2.pdf`, `fig3.pdf`) and no table or supplementary figure file. Main Fig. 2
and Main Fig. 3 have no labeled subpanels; every series within each is covered
by its target.

## Digital Claim Inventory

| Claim | Source | Classification | Boundary |
| --- | --- | --- | --- |
| Critical-Ising parity-sector formula was “verified numerically” | Main text after the `s_n(Q_A)` equation | unplotted numerical claim | Author size, BCs, algorithm, tolerance and data are absent. Formula identities are executable; paper-exact author verification is not reconstructible. |

## Assumptions

- Infinite half-filled tight-binding chain; subsystem length `L=10000`.
- Luttinger parameter `K=1` for the noninteracting numerical check.
- The 96 central correlation eigenvalues contain all nonsaturated modes; edge saturation is checked explicitly.
- Fig. 3 uses exactly the 24 closest-to-zero single-particle entanglement energies, as stated in the caption.
