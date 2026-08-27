# Paper Map

## Identity

- Paper ID: `1706.07435`
- Title: *Topological Band Theory for Non-Hermitian Hamiltonians*
- Authors: Huitao Shen, Bo Zhen, Liang Fu
- Source: arXiv:1706.07435; Phys. Rev. Lett. 120, 146402 (2018)
- Local PDF: `../raw/paper.pdf`
- Local source: `../paper-source/nonHermitian.tex`

## Reproduction Goal

Reconstruct the paper's non-Hermitian band theory from its left/right
eigenvectors, complex spectra, and defectiveness conditions; then independently
evaluate the equations and diagonalize the stated continuum/lattice models.
The goal is to test Chern-number consistency, energy vorticity, bulk-edge
correspondence, and the hybrid-point–exceptional-pair transition. There is no
physical experiment in this paper. All plotted values are generated from the
paper equations; original vector figures remain reference-side evidence only.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main: band definitions | Domain vocabulary | Separates isolated, separable, and inseparable complex bands. |
| Main: Chern numbers | Analytic topology | Defines four left/right Berry curvatures and proves their Chern integrals coincide. |
| Main: bulk-edge correspondence | Continuum model | Generalized Dirac bulk spectrum and domain-wall matching. |
| Main: energy vorticity | New invariant | Energy-difference winding and the one-dimensional Z/2 classification. |
| Main: stable degeneracies | Local theory | Codimension-two degeneracies, defective exceptional points, and square-root dispersion. |
| Main: phase transition | Global transition | Hybrid point → exceptional-point pair → hybrid point. |
| Supplement I–III | Proofs | Nonzero biorthogonal overlap, equality and vanishing of Chern numbers. |
| Supplement IV | Numerical bulk-edge evidence | Domain-wall matching surface and square-lattice cylinder spectra. |
| Supplement V–VI | Degeneracy derivations | Codimension count and four merging-EP outcomes. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Main Eqs. (1)–(3); Supp. I–III | Biorthogonal overlap and Chern equality | verified |
| EQC002 | Main Eq. (4), dispersion below it, and EP-position equation | Generalized Dirac bulk spectrum and phase boundaries | verified |
| EQC003 | Main Eqs. (5)–(7); Supp. Eqs. (10)–(12) | Domain-wall eigenvalue and matching conditions | verified |
| EQC004 | Main Eqs. (8)–(12), Fig. 2 model | Energy vorticity and exceptional-point square-root spectrum | verified |
| EQC005 | Supp. Eq. (13) | Square-lattice cylinder Hamiltonian | verified |
| EQC006 | Main hybrid-point equation; Supp. Eq. (20) | Hybrid-point anisotropic dispersion | verified |
| EQC007 | Supp. Eqs. (14)–(17) | Two-real-parameter degeneracy and defectiveness | verified |

## Scientific Claim Scope

Every central/supporting claim must also appear in
`physics_reproduction_project.json#scientific_scope`.

| Claim ID | Importance | Reproduction mode | Source refs | Formula/method refs | Expected evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| CLM001 | central | analytic derivation | Main Chern section; Supp. I–III | EQC001 | Patch-gauge proof plus symmetry limits | verified |
| CLM002 | central | formula numericalization | Main Fig. 1; Supp. IV | EQC002, EQC003, MTH002 | Complex bulk regions and domain-wall edge energies | verified |
| CLM003 | central | formula numericalization | Main vorticity section and Fig. 2 | EQC004, MTH001 | Branch swap and half-integer energy winding | verified |
| CLM004 | supporting | formula numericalization | Main stable-degeneracy section; Supp. V | EQC004, EQC007, MTH001 | Defective rank and square-root exponent | verified |
| CLM005 | central | formula numericalization | Main Fig. 3; Supp. VI | EQC002, EQC006, MTH001 | Phase regions, EP trajectories, and hybrid anisotropy | verified |
| CLM006 | supporting | formula numericalization | Supp. Eq. (13), Fig. 3 | EQC005, MTH003 | Cylinder spectrum and two chiral edge branches | verified |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Main Fig. 1 | Complex bulk-band regions and domain-wall edge curve | theory numerical | Target T001 |
| Main Fig. 2(a–c) | EP branch swap, 3D dispersion, and `kx=0` cut | theory numerical | Three panel items, target T002 |
| Main Fig. 3(a–b) | Dirac-model phase diagram and EP trajectories | theory numerical | Two panel items, target T003 |
| Supp. Fig. 1 | Torus patch construction | schematic context | Excluded from generation |
| Supp. Fig. 2 | `Im E(k=0)` over two transverse non-Hermitian shifts | theory numerical | Target T004 |
| Supp. Fig. 3(a–b), Re/Im | Four cylinder-band plots | theory numerical | Four panel items, target T005 |
| Supp. Fig. 4(a–b), Re/Im/cuts | Hybrid-point surfaces and anisotropic cuts | theory numerical | Four panel items, target T006 |
| Supp. Table I | Degeneracy taxonomy | context table | Analytically checked; no numerical rendering target |

## Assumptions

- Pauli convention follows the paper: `sigma_± = sigma_x ± i sigma_y` (no factor `1/2`).
- Momentum loops are oriented counter-clockwise unless stated; reversing orientation flips vorticity sign, not magnitude.
- Continuum energies are expressed in the mass scale specified by each caption.
- The cylinder is periodic in `y`, open over exactly `n=40` sites in `x`.
- Plotting resolution and 3D camera are presentation choices and cannot change scientific evidence.
