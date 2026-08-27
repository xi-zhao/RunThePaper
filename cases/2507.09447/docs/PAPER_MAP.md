# Paper Map: 2507.09447

## Identity

- Paper ID: `2507.09447`
- Title: “Lyapunov formulation of band theory for disordered non-Hermitian systems”
- Authors: Konghao Sun and Haiping Hu
- Version: arXiv v1, submitted 13 July 2025
- Source: https://arxiv.org/abs/2507.09447
- Formal publication: “Universal Thouless relations for disordered non–Hermitian systems in one dimension”, *Science Bulletin* (2026), online first
- Publication DOI: `10.1016/j.scib.2026.05.055`
- Publisher item identifier: PII `S2095927326005839`
- Local PDF: `raw/paper.pdf`
- Local TeX: `paper-source/extracted/manuscript_arxiv.tex`
- Original figure assets: `paper-source/extracted/Fig1.pdf` through `Fig5.pdf`

## Scientific Problem

Clean non-Hermitian band theory relies on translation symmetry. The paper asks
for a real-space object that still determines spectra, localization, mobility
edges, and topology when disorder removes momentum as a good quantum number.

The core object is the ordered Lyapunov spectrum of the real-space transfer
matrix. Disorder changes the two central exponents; their position relative to
zero determines whether an OBC eigenstate is a skin mode, an Anderson-localized
mode (ALM), or a unidirectional critical state (UCS).

## Executable Model

The main numerical example is a single-band chain with hopping range `M=2`:

```text
t_2 = 0.5, t_1 = 1.5, t_-1 = 1, t_-2 = 1,
t_0(i) ~ Uniform[-W, W].
```

For a complex energy `E`, a four-dimensional site transfer matrix gives four
ordered exponents `gamma_1 <= ... <= gamma_4`. The two central exponents
`gamma_2` and `gamma_3` are the domain state used by all three main targets.

## Paper Structure

| Section | Role | Reproduction consequence |
| --- | --- | --- |
| Real-space formulation | Defines the finite-range Hamiltonian and transfer matrix | Implement the `M=2` chain and stable QR Lyapunov estimator. |
| Non-Hermitian Thouless relations | Relates OBC/PBC electrostatic potentials to Lyapunov exponents | Compare transfer-matrix potentials with independently diagonalized spectra. |
| Essential Lyapunov exponent | Defines the mobility edge and state classes | Generate the union of the continuous `gamma_2=0` and `gamma_3=0` contours and apply sign-based classifications. |
| Illustrative examples | Supplies the paper model and Fig. 3–4 parameters | Reproduce locally at reduced system/sample scale, preserving the exact Hamiltonian parameters. |
| Topological criterion | Proves `nu=M-n_P` | Check Lyapunov-count winding against direct twisted-boundary determinants. |
| Skin–Anderson transition | Tracks contour shrinkage and `alpha(W)` | Recover the transition trend and compare the estimated threshold with `W_c≈2.1`. |
| Published supplement S1–S6 | Gives derivations, extra disorder models, and numerical convergence checks | Reproduce all numerical panels S1–S4; use the remaining sections as formula evidence. |

## Equation Inventory

| Card | Paper source | Role |
| --- | --- | --- |
| EQC001 | Eq. `model` | Finite-range disordered Hamiltonian. |
| EQC002 | Supplemental site-transfer equation | Numerically propagates an eigenvector by one site. |
| EQC003 | Eq. `t_matrix` and clean-limit Appendix S3 | Defines the ordered Lyapunov spectrum and clean-root limit. |
| EQC004 | Eqs. `pot_obc`, `den_obc` | OBC potential and density. |
| EQC005 | Eqs. `pot_pbc`, `den_pbc` | PBC potential and density. |
| EQC006 | Eqs. `ess`, `mobility` | Essential exponent and mobility edge. |
| EQC007 | Eqs. `winding`, `winding2` | Topological criterion `nu=M-n_P`. |
| EQC008 | Eq. `ratio` | ALM fraction and transition threshold. |

## Figure Inventory

| Item | Class | Scope decision |
| --- | --- | --- |
| Fig. 1 | `schematic_context` | Excluded; supercell/transfer-matrix diagram. |
| Fig. 2 | `schematic_context` | Excluded; conceptual LE/eigenstate profiles. |
| Fig. 3 | `numeric_reproduction` | In scope: OBC spectrum, Lyapunov prediction, mobility edge, potential convergence. |
| Fig. 4 | `numeric_reproduction` | In scope: PBC spectrum, Lyapunov prediction, winding labels. |
| Fig. 5 | `numeric_reproduction` | In scope: mobility-edge shrinkage and ALM fraction. |
| Fig. S1 | `numeric_reproduction` | In scope: off-diagonal disorder model, reduced-scale execution with explicit publication metadata boundary. |
| Fig. S2 | `numeric_reproduction` | In scope: quasiperiodic onsite model, reduced-scale execution with explicit publication metadata boundary. |
| Main-text one-way limit | `numeric_reproduction` | In scope: analytic triangular identity plus finite eigenspectrum check. |
| Published Fig. S3 | `numeric_reproduction` | In scope: code-complete multi-precision benchmark with a measured reduced pilot and explicit paper-scale compute boundary. |
| Published Fig. S4 | `numeric_reproduction` | In scope: full reported size/energy grid, alternative fit comparison, and an 18-protocol seed/ensemble/QR sensitivity sweep; current feature result is not reproduced pending fresh review. |
| Table I | `analytic_summary` | No numerical reproduction; checked through equation cards. |

## Reproduction Scope

The first run is a local numerical-feature reproduction, not a complete
paper-scale reproduction. It keeps the published Hamiltonian, hopping values,
disorder strengths, boundary conditions, energy ranges, and marker energies,
but reduces exact-diagonalization size/sample count and uses an explicitly
documented finite transfer length/grid.

Paper-scale Fig. 3(a) requires `L=1000` averaged over 3200 disorder
realizations. The TeX source does not report random seeds or the transfer-grid
resolution. These gaps prevent a `paper_exact` claim in the first run.

## Acceptance Signals

- clean-limit Lyapunov exponents agree with `log|beta_s|` roots;
- the transfer recurrence matches the Hamiltonian eigen-equation convention;
- OBC/PBC spectral potentials approach the corresponding Lyapunov potentials;
- direct twisted-boundary winding equals `M-n_P` away from contours;
- mobility-edge area shrinks as `W` grows;
- the inferred all-ALM threshold is close to the paper value `W_c≈2.1`;
- every plotted point is backed by CSV data and every claim by JSON checks.

## Known Missing Metadata

- author plotting data and code are not linked from arXiv;
- random seeds are not reported;
- Lyapunov transfer length, energy-grid resolution, smoothing rule, and the
  ensemble details behind Fig. 5(b) are not reported in the TeX source.
