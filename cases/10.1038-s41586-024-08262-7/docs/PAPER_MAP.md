# Paper Map

## Identity

- Paper ID: `10.1038-s41586-024-08262-7`
- Title: Particle exchange statistics beyond fermions and bosons
- Authors: Zhiyuan Wang, Kaden R. A. Hazzard
- Source: Nature **637**, 314–318 (2025), DOI 10.1038/s41586-024-08262-7 · preprint arXiv:2308.05203
- Local PDF: (not fetched; Nature is paywalled)
- Local source: `raw/Parastatistics_2nd_quantization-minimal.tex` (full arXiv TeX + figures)

## Reproduction Goal

Reproduce the paper's **only numerical/plottable main-text figure, Fig. 2**:

- **left** — the generalized exclusion statistics (level degeneracy `{d_n}`) for
  ordinary fermions, bosons, and the paraparticle R-matrices Ex.2/Ex.3/Ex.4;
- **right** — the free-particle thermodynamics, thermal occupation `<n>_beta`
  vs `beta*eps`, for the same species.

As an independent validation of the physics behind Fig. 2, exact-diagonalize the
paper's 1D exactly-solvable spin model (Ex.3, Eq. Hamil1Dspin) and confirm that
its many-body spectrum is that of **free paraparticles** with the Ex.3 exclusion
statistics — the paper's central claim ("free paraparticles emerge as
quasiparticle excitations") and the origin of `z_R(x)=1+m x`.

Out of scope (schematic / proof-only, not numerical figures): the conceptual
exchange-statistics illustration, the 2D solvable-model lattice diagram, the
paraparticle-braiding illustration, and all the SI tensor-network / commutation
diagrams. These carry no reproducible numerical data.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Intro + R-matrix / YBE | theory | Defines paraparticle CRs (Eq. fundamental_Rcommu), R-matrix, Table 1 examples |
| Generalized exclusion statistics | theory + Fig. 2 left | `d_n` = dim of n-particle single-mode space |
| Free-particle thermodynamics | theory + Fig. 2 right | `z_R`, `<n>_beta = x z'/z` (Eqs. single_mode_Z, n_k_expectation) |
| Exchange statistics | theory | R-matrix as physical two-particle rotation |
| Exact solution of free paraparticles | theory | H=sum h_ij e_ij -> sum eps_k n_k |
| Emergent paraparticles (1D/2D models) | theory | Eq. Hamil1Dspin solvable spin chain; 2D model in Methods |
| Methods + SI | proofs / details | gl_N algebra, gJWT, 2D KDH lattice, exclusion-statistics calc |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| `single_mode_partition_z_R` | Eq. single_mode_Z, Table 1, SI exclusion calc | definition + Fig.2 left | verified |
| `thermal_occupation_n_beta` | Eq. n_k_expectation | Fig.2 right observable | verified |
| `solvable_1d_spin_model_free_paraparticles` | Eq. Hamil1Dspin, SI 1D model | physical realization / validation | verified |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Fig. 1 | Types of exchange statistics (concept) | schematic | not numerical |
| **Fig. 2** | Exclusion statistics `{d_n}` + thermodynamics `<n>_beta` | **numeric** | THE reproduction target |
| Fig. 3 | 2D solvable spin model on 7×7 lattice | schematic | lattice diagram |
| Fig. 4 | Paraparticle exchange (braiding) illustration | schematic | conceptual |
| Table 1 | R-matrices and their `z_R(x)` | numeric (analytic) | inputs to Fig. 2 |
| SI figures | tensor-network / CR diagrams | schematic | proofs |

## Assumptions

- Fig. 2 is reproduced at the **published figure legend** parameters
  (Ex.2 m=2, Ex.3 m=2, Ex.4 m=3), not the main-text prose value m=5 — see
  FIGURE_CLASSIFICATION.md for the flagged text/figure inconsistency.
- Fermion/boson reference curves are the ordinary single-flavor (m=1) statistics.
- The 1D-model ED uses illustrative small chains (N=4,5); the paper fixes no
  figure-level N, so chain length is not a claim-relevant parameter.
