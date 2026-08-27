# Paper Map

## Identity

- Paper ID: `1903.05124`
- Title: *Quantum Error Correction in Scrambling Dynamics and Measurement-Induced Phase Transition*
- Authors: Soonwon Choi, Yimu Bao, Xiao-Liang Qi, Ehud Altman
- Source: arXiv:1903.05124; Phys. Rev. Lett. 125, 030505 (2020)
- Local PDF: `../raw/paper.pdf`
- Local source: `../paper-source/manuscript_arxiv_03.tex` and `../paper-source/manuscript_supp.tex`

## Reproduction Goal

Reconstruct the paper's measurement-induced entanglement transition as a
quantum-error-correction problem. The analytic lane derives the naive and tight
decoupling bounds and the channel-capacity identity. The numerical lane builds
the stated random brick-layer Clifford circuit, evolves stabilizer states under
projective measurements, calculates subsystem entropies and tripartite mutual
information, and performs the paper's finite-size scaling. Every visible
theory-numerical panel or inset is generated from that model. The paper contains
no laboratory measurements; its circuit, channel, and tensor-network drawings
are explanatory schematics and remain outside numerical figure generation.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main: protection against measurement | Analytic QEC mechanism | Decoupling first gives `gamma < 1-2p`; retaining measurement outcomes tightens it to `gamma < 1-p`. |
| Main: model and phase diagram | Domain model | A chain of `L` blocks, `m` qubits per block, depth-`d` local Clifford scramblers, and measurement fraction `p`. |
| Main: numerical evidence | Dynamic and steady-state evidence | Half-chain entropy, measurement-induced entropy change, steady-state curves, and the `(d/m,p)` phase diagram. |
| Supplement S1 | Design diagnostic and algorithm | Frame potentials and a polynomial Clifford-trace algorithm. |
| Supplement S2 | Entanglement growth | Eight parameter regimes, each with entropy and measurement-reduction panels. |
| Supplement S3 | Finite-size transition | Half-chain scaling, data collapse, tripartite mutual information, and critical exponents. |
| Supplement S4 | Block-size dependence | `p_c`, `nu`, and logarithmic coefficient `alpha` versus `m`. |
| Supplement S5 | Channel capacity | Proves `Q=max <S>` for the degradable measurement channel. |
| Supplement S6 | Improved decoupling | Haar/2-design average and Weingarten contractions produce the tight exponential bound. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Main Eqs. (1)–(2) | Naive decoupling error and `gamma < 1-2p` | verified |
| EQC002 | Main Eq. (3); Supp. Eqs. (S29)–(S37) | Tight decoupling error and `gamma < 1-p` | verified |
| EQC003 | Supp. Eqs. (S1)–(S3) | Frame potential and Haar lower bound `k!` | verified |
| EQC004 | Supp. Eqs. (S4)–(S10) | Clifford trace from the fixed-Pauli kernel | verified |
| EQC005 | Stabilizer formalism cited in main text | Subsystem entropy from the rank of supported stabilizers | verified |
| EQC006 | Main Fig. 2 and Supp. Fig. S3 definitions | Entanglement density and `Delta S_meas` observables | verified |
| EQC007 | Supp. Eqs. (S11)–(S14) | Half-chain finite-size scaling and collapse cost | verified |
| EQC008 | Supp. Eqs. (S15)–(S16) | Tripartite mutual information and scaling ansatz | verified |
| EQC009 | Main Eq. (4); Supp. Eqs. (S17)–(S28) | Quantum channel capacity equals optimized conditional entropy | verified |
| EQC010 | Supp. Eq. (S17 in section numbering context) | Critical entropy `S(p_c,L)=alpha ln L` | verified |
| MTH001 | Main model section and Fig. 2(a) | Random brick-layer Clifford tableau evolution with computational-basis measurements | reconstructed; exploratory gate open |
| MTH002 | Supp. S1 numerical algorithm | Symplectic-kernel frame-potential estimator | reconstructed; exploratory gate open |
| MTH003 | Supp. S3 scaling protocol | Collapse optimization and bootstrap uncertainty | reconstructed; exploratory gate open |

## Scientific Claim Scope

Every central/supporting claim must also appear in
`physics_reproduction_project.json#scientific_scope`.

| Claim ID | Importance | Reproduction mode | Source refs | Formula/method refs | Expected evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| CLM001 | central | analytic derivation | Main protection section; Supp. improved bound | EQC001, EQC002 | Algebraic exponent and limiting-condition checks | verified derivation |
| CLM002 | central | analytic derivation | Main Eq. (4); Supp. channel-capacity section | EQC009 | Degradable-channel and block-entropy derivation | verified derivation |
| CLM003 | supporting | independent numerics | Supp. Fig. S2 | EQC003, EQC004, MTH002; T002 | `F1,F2,F3` approach `1!,2!,3!`; `F4` remains above `4!` | active |
| CLM004 | central | independent numerics | Main Fig. 2(b,c); Supp. Fig. S3 | EQC002, EQC005, EQC006, MTH001; T001,T003 | Early-time protection and threshold-aligned entropy reduction | active |
| CLM005 | central | independent numerics | Main Fig. 2(d,e); Supp. Figs. S4,S5 | EQC005–EQC008, MTH001,MTH003; T001,T004,T005 | Volume/area phases, `p_c(d)`, and finite-size collapses | active |
| CLM006 | central | independent numerics | Supp. Figs. S5–S6 and Table SI | EQC008, MTH001,MTH003; T005,T006 | `nu` near 1.25 with weak `d,m` dependence | verified at feature scale; T005 depth-span warning retained |
| CLM007 | supporting | derivation plus independent numerics | Supp. Fig. S6 and improved bound | EQC002, EQC008, EQC010, MTH001,MTH003; T006 | Increasing `p_c(m)` toward one and stable `nu,alpha` | verified at feature scale |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Main Fig. 1 | Bell-pair scrambling and measured/unmeasured partition | schematic context | Excluded from generation; analytic claim CLM001 is still derived. |
| Main Fig. 2(a) | Qubit-block circuit layout | schematic context | Excluded from generation; defines MTH001. |
| Main Fig. 2(b–e) | Dynamics, measurement change, steady state, and phase diagram | theory numerical | Four items, target T001. |
| Supp. Fig. S1(a,b) | Clifford circuit and binary matrix `T` | schematic context | Two excluded panels; defines MTH002. |
| Supp. Fig. S2(a–d) | First through fourth frame potentials | theory numerical | Four items, target T002. |
| Supp. Fig. S3(a–h), upper/lower | Entropy growth and measurement reduction | theory numerical | Sixteen items, target T003. |
| Supp. Fig. S4(a–g), three insets | Half-chain scaling and exponent | theory numerical | Ten items, target T004. |
| Supp. Fig. S5(a–g) | `I3` curves, collapses, and exponent | theory numerical | Seven items, target T005. |
| Supp. Table SI | Fitted `nu` and `p_c` versus `d` | numerical context table | Values are scientific checks for T005; table rendering is excluded by case policy. |
| Supp. Fig. S6(a–c) | `p_c`, `nu`, and `alpha` versus block size | theory numerical | Three items, target T006. |
| Supp. Fig. S7(a,b) | Measurement channel and dilation | schematic context | Excluded from generation; used in EQC009. |
| Supp. Fig. S8(a–c) | Toy model and swap tensor networks | schematic context | Excluded from generation; used in EQC002. |
| Supp. Fig. S9 | Weingarten contraction network | schematic context | Excluded from generation; used in EQC002. |

## Assumptions

- A circuit layer uses the alternating nearest-neighbour brick pattern shown in Fig. S1; independent two-qubit Clifford gates are sampled uniformly.
- At the block-chain level, neighbouring block pairs alternate between even and odd bonds each time step, with periodic boundaries for the `I3` calculation as stated in the supplement.
- If `pm` is noninteger, each block measures either `floor(pm)` or `ceil(pm)` qubits with probabilities chosen so the expectation is `pm`.
- Paper-realization counts, system sizes, and stated grids are final targets; fixed seeds are reproduction controls because the authors do not publish their random seeds.
- Exact equilibration windows and some plotted sampling grids are not stated. They must be chosen by a convergence rule, recorded in generated metadata, and never inferred from source pixels.
- Source figures may be cropped and registered only after independent values exist; they never enter a simulator, fit, or renderer as generated data.
