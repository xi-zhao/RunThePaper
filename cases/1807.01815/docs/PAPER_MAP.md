# Paper Map

## Identity

- Paper ID: arXiv:1807.01815v2.
- Preprint title: *Periodic orbits, entanglement and quantum many-body scars in constrained models: matrix product state approach*.
- Authors: Wen Wei Ho, Soonwon Choi, Hannes Pichler, and Mikhail D. Lukin.
- Formal publication: *Physical Review Letters* **122**, 040603 (2019), DOI `10.1103/PhysRevLett.122.040603`.
- Canonical source: `https://arxiv.org/abs/1807.01815`.
- Local full paper: `raw/paper.pdf` (21 pages: main text and complete supplemental material).
- Local source: `paper-source/`; the archive contains TeX, bibliography output, and six rendered figure assets, but no author code or numerical arrays.
- Frozen source record: `SOURCE_FREEZE.json`.

## Reproduction Goal

Independently regenerate every numerical figure from the stated Hamiltonians,
TDVP equations, MPS definition, and exact constrained-space quantum mechanics.
The generator must not read the PDF, TeX, source figures, extracted curves, or
reference pixels. Main Fig. 3 is explanatory artwork and is inventoried but not
numerically reproduced.

The central scientific question is whether a two-parameter, bond-dimension-two
TDVP manifold contains an isolated orbit passing through the two Neel product
states and whether its period and small leakage explain long-lived exact
many-body revivals. Exact dynamics are evaluated in a two-site-translation
sector; level statistics use the momentum-zero, inversion-even sector.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main: Introduction | Product-state-dependent thermalization and scar analogy | Establishes the physical claim. |
| Main: constrained spin models | Defines the projected spin-s Hamiltonian and exact numerical observables | Source for Figs. 1b, 2, and 4b/d. |
| Main: TDVP equations | Defines projected coherent-state MPS, flow, and leakage | Source for Figs. 1a and 4a/c. |
| Main: Discussion | Interprets integrated leakage as a many-body analogue of weak orbit instability | Quotes orbit periods and integrated errors. |
| Supplement I | Derives the normalized bond-dimension-two MPS | Supplies transfer-matrix and normalization identities. |
| Supplement II | Derives TDVP Gram matrix, flow, and residual norm | Supplies the executable analytic/method contract. |
| Supplement III | Resolution of identity | Analytic context; no numerical target. |
| Supplement IV | Infinite-temperature values in the constrained space | Supplies sanity checks for local magnetization and entropy. |
| Supplement V | Deformed Hamiltonian and TDVP flow | Source for Figs. S1 and S2. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ-H | Main Eq. (1) | Projected spin-s Hamiltonian | verified from local spin matrix elements and constraint rules |
| EQ-MPS | Main Eqs. (2)-(3); Supplement I | Normalized constrained MPS | verified by finite-ring direct normalization |
| EQ-FLOW | Main Eq. (4); Supplement II | Two-site TDVP flow for arbitrary spin | verified by symmetry and product-state limits |
| EQ-GAMMA | Main Eq. (5); Supplement II | Intensive TDVP residual | verified by direct finite-MPS residual norm, not source pixels |
| EQ-R | Main Fig. 2 caption | Adjacent-gap ratio | verified against Poisson and GOE reference limits |
| EQ-ENT | Main Fig. 2; Supplement IV | Reduced-density-matrix entropy | verified by trace, positivity, and product-state limits |
| EQ-THERM | Supplement IV | Constrained infinite-temperature local magnetization | verified by transfer/counting formula |
| EQ-DEF-FLOW | Supplement V | Deformed-model two-site TDVP flow | source traced and checked to reduce to EQ-FLOW at s=1/2, h=0 |
| MTH-T2 | Independent symmetry reduction | Exact dynamics in translation-by-two orbit basis | verified against full-basis small systems |
| MTH-DIH | Independent symmetry reduction | k=0, inversion-even full-spectrum diagonalization | verified against full-basis small systems |
| MTH-BLOCK-TDMRG | Independent exact pair blocking plus finite-MPS product formula | Paper-scale L=30 Fig. 2(b,c) entropy route | blocked/unblocked Hamiltonians and small exact evolution agree; checkpoint/resume and six-shard merge tested |

## Complete Figure/Table Inventory

| Item | Panels | Numerical content | Class and decision |
| --- | --- | --- | --- |
| Main Fig. 1 | (a) s=1/2 TDVP flow, leakage map, orbit; (b) local Sz for L=30,32 from zero and Z2 states, t Omega=0..300 | all panels numerical | targets T_FIG1A, T_FIG1B |
| Main Fig. 2 | (a) r-statistic for s=1/2,1,2; (b) six-site entropy at L=30, t Omega=0..100; (c) one-site entropy at L=30, t Omega=0..120 | all panels numerical | T_FIG2A remains reduced because the plotted size list is not disclosed; T_FIG2B/C have an executable, unrun L=30 finite-MPS contract plus the executed reduced exact evidence |
| Main Fig. 3 | (a) tangent-space cartoon; (b) projected-state/MPS cartoon | no generated numerical quantity | excluded schematic |
| Main Fig. 4 | (a,b) s=1 flow/leakage and local Sz for L=20,22; (c,d) s=2 flow/leakage and local Sz for L=14,16; t Omega=0..300 | all panels numerical | targets T_FIG4A-D |
| Supplement Fig. S1 | four flow panels at h/Omega=-0.2, 0, 0.2, 0.4 | numerical vector fields | targets T_FIGS1_HM020/H000/H020/H040 |
| Supplement Fig. S2 | (a) integrated leakage; (b) integrated squared leakage for h/Omega=0..0.08 | numerical orbit integrals | targets T_FIGS2A/B; finite-ring convergence passes but the printed minimum is not reproduced |
| Tables | none | none | no table target |

## Parameter Sources and Assumptions

- Set `Omega=1`; all reported times are therefore `t Omega`.
- Periodic boundary conditions follow the main Hamiltonian definition and Supplement IV.
- The plotted local observable is the sublattice that is in `|0>` at t=0; this is fixed by every dynamics panel starting at `-s`.
- The paper does not state time sampling, ODE tolerance, heat-map resolution,
  the exact system-size list behind Fig. 2(a), or numerical evolution controls
  such as time step, bond dimension and truncation cutoff for Fig. 2(b,c).
  These are never recovered from source geometry. The Fig. 2(b,c) contract
  declares independent controls and explicit dt/bond refinements.
- Source images are used only to inventory panels and, after the freeze, to compose labelled side-by-side comparisons. No curve is digitized.
- Executed exact dynamics and entropy are exploratory reduced-scale evidence;
  the unexecuted Fig. 2(b,c) L=30 path is code-ready but not evidence. The
  analytic TDVP periods and leakages retain the printed spin and time
  definitions. Fig. S2 is a declared failed scientific target: the independent
  deformed Hamiltonian projects to the printed flow and the residual converges,
  yet the generated minimum differs. Because the closed deformed residual
  construction and numerical integration procedure are omitted, protocol-v2
  assigns `parameter_ambiguity`. It is not eligible for
  `paper_error_candidate` without a paper-exact procedure and fresh independent
  review.
