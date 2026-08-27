# Paper Map: 2605.25398

## Identity

- Paper ID: `2605.25398`
- Title: "Boson Sampling as a Probe of Chaotic and Integrable Quantum Dynamics"
- Authors: Yuancheng Zhan, Khen Cohen, Norman T. W. Koo, Kian Hwee Lim, Hui Zhang, Lingxiao Wan, Sanghoon Chae, Ai Qun Liu, Victor M. Bastidas, Yaron Oz, Leong-Chuan Kwek
- Source: https://arxiv.org/pdf/2605.25398
- Local PDF: `raw/paper.pdf`
- Local TeX source: `paper-source/extracted/main.tex`
- Local original figures: `internal-paper-reference/`

## Reproduction Goal

This case follows the paper's numerical claim: boson-sampling output statistics can distinguish chaotic random-matrix dynamics from integrable dynamics.

The executable scope is:

- construct the random-matrix Hamiltonian family `H = (H0 + lambda V) / sqrt(1 + lambda^2)`;
- evolve `U(t)=exp(-iHt)`;
- compute two-photon collision-free boson-sampling probabilities;
- reproduce the paper's diagnostic curves: distance to Porter-Thomas statistics, Shannon entropy, OTOC-equivalent probabilities, participation ratio, conditional-probability validation, and scaling behavior.

Out of scope:

- silicon photonic chip design and optical setup;
- measured experimental photon counts;
- exact visual restyling of the paper figures;
- author seed/data-level reproduction, because the paper states data are available on request and no raw experimental dataset is included in the arXiv source.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Introduction | Scientific motivation | Connects boson sampling, quantum chaos, integrated photonics, PT statistics, entropy, and OTOC-like probes. |
| Theory / Boson Sampling | Core numerical model | Gives the permanent formula for output probabilities and the collision-free conditional distribution. |
| Random-Matrix Hamiltonians | Core numerical model | Defines `H_Lambda`, `Lambda=0.01` integrable and `Lambda=1000` chaotic. |
| Experimental Implementation | Context plus partially numeric panels | Hardware schematics are not reproduced; theoretical output distributions are reproduced as a feature target. |
| Results | Main reproducible targets | Defines PT distance, Shannon entropy, OTOC-equivalent observables, and participation ratio. |
| Appendix: Conditional Probabilities | Sanity check target | Justifies using PT statistics after collision-free post-selection. |
| Appendix: Scaling Arguments | Supporting numerical target | Shows diagnostics improve with increasing optical modes. |
| Appendix: OTOC Dynamics | Supporting numerical target | Gives short-time power laws and late-time FFT participation ratio. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| E001 | Main text Eq. for boson-sampling probability | Converts unitary matrix into output probabilities through a permanent. | Implemented in `conditional_two_photon_distribution`. |
| E002 | `H = (H0 + lambda V) / sqrt(1 + lambda^2)` | Generates integrable and chaotic random-matrix dynamics. | Implemented in `sample_hamiltonian`. |
| E003 | `Lambda = lambda^2 d / 2pi` | Converts the paper's dimensionless perturbation strength into `lambda`. | Implemented in `lambda_from_Lambda`. |
| E004 | `f_t(p)` and Wasserstein distance to `D exp(-Dp)` | First chaos probe. | Implemented in `porter_thomas_w1`. |
| E005 | Shannon entropy `S=-sum p log p` and Haar limit `-1+sum 1/i` | Second chaos probe. | Implemented and checked. |
| E006 | OTOC-equivalent probability `|U_ri U_sj + U_rj U_si|^2` | Third chaos probe for two photons. | Implemented through the same probability kernel. |
| E007 | Participation ratio `1/sum p_i^2` | Global delocalization metric. | Implemented and checked. |
| E008 | Short-time OTOC power laws `t^2` and `t^4` | Appendix validation. | Implemented and checked. |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Fig. 1 | Workflow schematic for on-chip boson sampling chaos probes | schematic_context | Not reproduced. |
| Fig. 2a-f | Experimental hardware, chip, source, filters, MZI | experimental_context | Not reproduced. |
| Fig. 2g-h | Output probability distributions for integrable and chaotic dynamics | numeric_reproduction | Reproduced as theoretical conditional distributions. |
| Fig. 3 | PT distance, Shannon entropy, 4-point SFF | numeric_reproduction | Main target; feature checks passed. |
| Fig. 4 | OTOC-equivalent observables and participation ratio | numeric_reproduction | Main target; feature checks passed. |
| Fig. S1 | Conditional probability distribution after post-selection | numeric_reproduction | Reproduced as appendix sanity check. |
| Fig. S2 | Experimental setup schematic | experimental_context | Not reproduced. |
| Fig. S3 | Chip decomposition schematic | schematic_context | Not reproduced. |
| Fig. S4 | Scaling of diagnostics with system size | numeric_reproduction | Reproduced at local feature scale. |
| Fig. S5 | Ideal OTOCs over all collision-free configurations | numeric_reproduction | Reproduced. |
| Fig. S6 | Short-time OTOC scaling and FFT participation ratio | numeric_reproduction | Reproduced; power-law checks passed. |

## Assumptions

- The input two-photon state is taken as occupied modes `(3,4)` in one-based paper notation, matching the text around the OTOC discussion.
- We reproduce the theory/ideal curves and feature-level diagnostics. Experimental red points require measured chip data, which are not included in the arXiv source.
- Random matrix seeds are local. The paper does not publish seed-level ensembles, so exact pointwise curve matching is not claimed.
- Visual differences in styling, panel layout, and color are not treated as scientific mismatches.
