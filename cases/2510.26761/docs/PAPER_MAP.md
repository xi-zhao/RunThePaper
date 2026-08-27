# Paper Map

## Identity

- Paper ID: `2510.26761`
- Title: *Sufficient Wigner Negativity Implies Genuine Multipartite Entanglement*
- Authors: Lin Htoo Zaw, Jiajie Guo, Qiongyi He, Matteo Fadel, and Shuheng Liu
- Publication: *Physical Review Letters* **137**, 040202 (2026)
- DOI: `10.1103/bftw-qnbf`
- Source: arXiv `2510.26761`
- Local PDF: `../raw/paper.pdf`
- Local source: `../paper-source/WignerNegativityImpliesGME.tex`

## Reproduction Goal

Reproduce the numerical content of both main-text figures from the formulas and
state definitions printed in the paper:

1. the numerical Wigner-function surfaces behind the conceptual overview in
   Fig. 1, together with the two witness values quoted in the End Matter;
2. the two panels of Fig. 2 for the tripartite W state, including the finite-disk
   threshold and the finite characteristic-function witness.

The arrows, prose, and page composition in Fig. 1 are explanatory graphics and
are not redrawn. The scientific objects under those graphics are in scope.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Background and Definitions | Fixes the multimode Wigner and GME conventions | Numerical normalization depends on the paper's \(2/\pi\) convention |
| Primary Theoretical Results | States the two slice/smoothing theorems | Supplies the witness inequalities used for Fig. 1 |
| Construction of GME criteria | Gives finite-region and finite-point criteria | Supplies both panels of Fig. 2 |
| End Matter: Fig. 1 state | Defines the collective-mode Fock state | Contains an internally inconsistent printed threshold numerator |
| End Matter: Fig. 2 state | Gives closed forms for \(W_3\), \(\chi_3\), and the 19 points | Enables an independent exact reproduction |
| Supplemental S1--S5 | Proves the bounds and characteristic matrix criterion | Used to verify normalization and sign conventions |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Background definitions | Wigner and characteristic conventions | verified |
| EQC002 | Theorem 1 and Supplemental S1 | Canonical two-dimensional slice identity | verified |
| EQC003 | Theorem 1 | Slice negativity and GME threshold | verified |
| EQC004 | Theorem 2 | Smoothed center-of-mass witness | verified |
| EQC005 | Eq. `filter-function-Gaussian` | Gaussian kernel for \(M=3\) | verified |
| EQC006 | Corollary `GME-Wigner-witness` | Finite-region absolute-volume criterion | verified |
| EQC007--EQC009 | End Matter: Fig. 2 | W-state Wigner function, volume, and threshold | verified |
| EQC010--EQC011 | Characteristic witness and End Matter | W-state finite-point matrix | verified |
| EQC012--EQC014 | End Matter: Fig. 1 | Illustrative state, slice witness, and smoothing value | verified with one source correction |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Main Fig. 1 | Overview of slice negativity and smoothed center-of-mass negativity | mixed schematic/numeric | Numeric Wigner surfaces and quoted witness values are target `T001`; arrows and text are excluded |
| Main Fig. 2(a) | W-state Wigner function on the equal-coordinate slice | numeric reproduction | Target `T002`, panel `wigner_slice` |
| Main Fig. 2(b) | W-state characteristic function and 19 difference points | numeric reproduction | Target `T002`, panel `characteristic_slice` |
| Supplemental material | Analytic proofs only | non-numeric | Represented by validation targets rather than figures |

## Assumptions

- The paper's Wigner convention is used exactly; no conversion to the
  \(1/\pi\) convention is made.
- The canonical displayed slice is \(\vec y=\vec 1,\vec z=0\).
- The third collective (relative) mode of the Fig. 1 example is in vacuum.
- The Fig. 1 isosurface levels and camera are not disclosed, so its numerical
  reconstruction is evaluated by sign topology, analytic invariants, and
  cross-sections rather than pixel identity.
- For the Fig. 1 state, the printed Fock coefficients are treated as primary
  evidence. They imply a numerator of 52 in the state-dependent GME bound,
  whereas the End Matter prints 56; both values are recorded explicitly.
