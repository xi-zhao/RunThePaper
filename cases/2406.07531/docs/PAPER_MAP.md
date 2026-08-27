# Paper Map

## Identity

- Paper ID: 2406.07531
- Title: Interacting-Bath Dynamical Embedding for Capturing Nonlocal Electron Correlation in Solids
- Authors: Jiachen Li and Tianyu Zhu
- Publication: Physical Review Letters 133, 216402 (2024)
- DOI: 10.1103/PhysRevLett.133.216402
- Preprint: arXiv:2406.07531v2
- Local published PDF: paper-source/prl-133-216402.pdf
- Local arXiv PDF/source: paper-source/2406.07531.pdf and paper-source/2406.07531-source.tar

## Reproduction goal

Independently implement the scientific map

mean field -> IAO+PAO basis -> interacting bath -> projected Hamiltonian ->
embedded many-body Green function -> full self-energy -> spectral observables.

The nine targets are execution units for 28 independently judged theoretical
items in Main Figs. 2-4. The two ARPES series in Fig. 4(a) are experimental
references and remain visible in the inventory without entering the numerical
reproduction denominator. The main text also names Supplement Tables S6 and
S7, bringing the known eligible lower-bound inventory to 30 items. Fig. 1 is
explanatory context only.

The full material campaign currently lacks a paper-exact production parameter
contract and has not been executed. Code readiness and independently verified
small-system algebra must not be promoted to material-specific reproduction.
Point-level author arrays are neither required nor permitted as scientific
inputs.

## Paper structure

| Section | Role | Reproduction use |
| --- | --- | --- |
| Introduction | Motivates local and nonlocal correlation | Claim and alternative-explanation audit |
| Method | Defines bath construction, projected Hamiltonian, and self-energy assembly | Primary derivation source |
| Si and 2D BN | Convergence and DOS benchmarks | Targets T001-T003 |
| MgO and SrTiO3 | Insulator spectral functions and gaps | Targets T004-T005 |
| Na | Bandwidth and nonlocal-correlation diagnosis | Targets T006-T009 |
| Conclusion | General claims | Falsification checklist |

## Equation and method inventory

| ID | Source | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Method, B_DM paragraph | Density-matrix Schmidt bath | derivation verified |
| EQC002 | Method, B_GF paragraph | Frequency-dependent Green-function bath | derivation verified |
| EQC003 | Method, B_NO paragraph | dMP2 natural-orbital bath | source traced; thresholds missing |
| EQC004 | Eqs. (1)-(2) | Projected interacting Hamiltonian and HF subtraction | algebra verified |
| EQC005 | Eq. (3) | Rotate and democratically assemble embedded self-energy | algebra verified; partition details incomplete |
| EQC006 | Eq. (4) | GW+ibDET replacement of local or short-range GW self-energy | algebra verified |
| EQC007 | Standard Dyson relation plus figure captions | DOS, band gaps, and spectral heat maps | independently derived |
| EQC008 | Na analysis and Fig. 4(b,c) | Local/full counterfactual and real-space range | independently derived |

## Numerical target and item inventory

| Target | Paper item | Eligible atomic items | Observable | Current boundary |
| --- | --- | ---: | --- | --- |
| T001 | Fig. 2(a), upper | 5 | Si Gamma-X gap convergence and three theoretical references | missing paper-exact inputs; execution not run |
| T002 | Fig. 2(a), lower | 5 | Si X-X gap convergence and three theoretical references | missing paper-exact inputs; execution not run |
| T003 | Fig. 2(b) | 6 | Three 2D BN DOS comparisons | missing paper-exact inputs; execution not run |
| T004 | Fig. 3(a) plus Table S6 | 3 | MgO spectral map, G0W0 bands, and cited table | supplement source blocked; execution not run |
| T005 | Fig. 3(b) plus Table S7 | 3 | SrTiO3 spectral map, G0W0 bands, and cited table | supplement source blocked; execution not run |
| T006 | Fig. 4(a) | 3 | Na GW+ibDET map plus PBE and G0W0 bands | missing paper-exact inputs; execution not run |
| T007 | Fig. 4(b) | 1 | Na local-minus-full DOS | missing paper-exact inputs; execution not run |
| T008 | Fig. 4(c), top | 2 | Na real/imaginary nonlocal self-energy at -3 eV | missing paper-exact inputs; execution not run |
| T009 | Fig. 4(c), bottom | 2 | Na real/imaginary nonlocal self-energy at 0 eV | missing paper-exact inputs; execution not run |

The known eligible total is 30 and the current covered total is 0. The
per-item rows and reasons live in `figure_coverage.json`; target-level
causality is projected into every corresponding uncovered item.

## Printed quantitative anchors

- Si: 4x4x4 k mesh; about 210 embedding orbitals; both reported gap
  errors 0.04 eV; starting-point spread 0.71 -> 0.08 eV.
- 2D BN: 6x6x1 k mesh and 200 embedding orbitals.
- MgO: 6x6x6, 230 embedding orbitals, reported GW+ibDET gap 8.22 eV.
- SrTiO3: 6x6x6, about 210 embedding orbitals, reported R-Gamma and
  Gamma-Gamma gaps 3.24 and 3.74 eV.
- Na: 8x8x8, 225 embedding orbitals; reported full/local bandwidths
  2.84/3.11 eV; real-space correction remains nonzero through the sixth
  neighbour.

These numbers are comparison anchors only. They are never used to synthesize
spectral arrays or tune physical model parameters.

## Assumptions and unavailable information

- The arXiv source contains no public code or point-level arrays.
- APS supplementary material was inaccessible with HTTP 403 locally and on
  the authorised institute network, and the current APS page confirms that it
  is subscription-gated. Tables S6 and S7 are known but unavailable; the
  remainder of the formal supplemental numerical scope is unknown and is not
  guessed.
- Bath-selection thresholds, real-frequency grids, broadenings, democratic
  partition weights, complete geometries, and several basis details are not
  fully printed in the main article.
- It is not yet proven that the publication itself omits these inputs: some may
  be present in the inaccessible supplement. The root cause remains
  `unresolved/open`, and the unexecuted production path means code fault is
  `not_excluded`.
- Source figure pixels may be used only after data freeze for visual
  diagnostics and RenderContract styling.
