# Paper Map

## Identity

- Paper ID: `quant-ph-0211074`
- Title: *Entanglement in Quantum Critical Phenomena*
- Authors: G. Vidal, J. I. Latorre, E. Rico, and A. Kitaev
- Preprint: arXiv:quant-ph/0211074
- Formal publication: Phys. Rev. Lett. 90, 227902 (2003), DOI
  `10.1103/PhysRevLett.90.227902`
- Local PDF: `raw/paper.pdf`, SHA-256
  `04dcac91f5afce31cfba1013525a9b2127661233d438c409f06d101e130036f0`
- Local source: `paper-source.tar`, SHA-256
  `6e44408225affbeeb6069a3bdfd3ebbf836574cca46c98735f6d851de6dfbf15`

The source archive contains one TeX file and two EPS figures. It contains no
author computational code, notebook, or numerical data table.

## Reproduction Goal

Independently regenerate both numerical figures and every quantitatively
testable formula/text claim from the printed Hamiltonians, Majorana correlation
matrix, entropy spectrum, scaling laws, and clean-room finite-chain
calculations. The authored scope contains 41 atomic numerical items: 40 map to
runnable targets and one higher-dimensional area-law statement is explicitly
deferred because this paper gives no model or numerical observable for it.
Author figure paths are comparison-only evidence.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Eqs. (1)--(4) | models and entropy observable | Defines XY/XXZ chains and block entropy. |
| Eqs. (5)--(13) | exact XY-chain reduction | Majorana correlation matrix and entropy eigenvalues. |
| Eqs. (14)--(18) | scaling claims | XX/Ising logarithms, saturation, and central charge. |
| Figs. 1--2 | numerical evidence | Both figures are fully numerical and in scope. |
| Eqs. (19)--(21) | spectrum and review claims | Complete product spectrum, effective rank, and majorization. |
| Remaining quantitative prose | whole-paper audit | Reliability, scaling collapse, central charge, anisotropy, RG monotonicity, and DMRG-rank claims. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | TeX lines 73--87 | XY and XXZ Hamiltonians | verified |
| EQ002 | TeX lines 116--139 | thermodynamic-limit Majorana correlations | verified |
| EQ003 | TeX lines 141--174 | block entropy from covariance eigenvalues | verified |
| EQ004 | TeX lines 176--220 | critical and noncritical scaling | verified |
| EQ005 | TeX lines 192--203, 237--255 | N=20 XXX finite-chain entropy | verified with degeneracy check required |
| EQ006 | TeX lines 311--330 | density-spectrum majorization | verified definition; numerical falsification required |
| EQ007 | Eq. (20) | complete reduced-density spectrum | verified by normalization and entropy identity |
| EQ008 | Fig. 1 caption/scaling paragraph | noncritical scaling coordinate | reconstructed; paper gives no finite grid or tolerance |
| EQ009 | c-theorem paragraph | RG-flow entropy monotonicity | source-only; no lattice RG map is published |
| EQ010 | DMRG paragraph | operational effective Schmidt rank | reconstructed; threshold and finite range are unpublished |
| EQ011 | Eqs. (5), (6), (10), (11) | labelled fermion occupation convention | verified algebra; printed Eq. (11) sign retained as a source discrepancy |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Main Fig. 1 | noncritical Ising entropy surface versus L and a | numeric_reproduction | all surface samples in scope |
| Main Fig. 2 | critical Ising, XX, and N=20 XXX entropies plus CFT guides | numeric_reproduction | all three series and both guide lines in scope |
| 39 quantitative claims | Eqs. (1)--(21), captions, and quantitative prose | numeric_reproduction | 38 target-mapped atomic items; one missing-source deferral |

The machine-readable item-to-target mapping is authoritative in
`figure_coverage.json`: 41 numeric items, 40 targeted, one deferred. The
17 executable targets are `T001`--`T017`; none is represented only by pixels.

## Assumptions

- The thermodynamic-limit XY calculation uses the paper's Toeplitz correlation
  matrix directly; no finite-N correction is introduced.
- Figure grids not printed numerically are reconstructed from the displayed
  integer L values and labeled axes, never fitted to source pixels.
- A finite probe grid selected for an asymptotic or universal claim is labeled
  `paper_subset`; it is evidence for or against the claim, not a claim that the
  undisclosed author campaign has been reproduced exactly.
- The printed ferromagnetic-sign XXX Hamiltonian has a degenerate ground-state
  multiplet. The runner must record the selected magnetization/symmetry sector
  and compare it with an independently diagonalized small chain.
