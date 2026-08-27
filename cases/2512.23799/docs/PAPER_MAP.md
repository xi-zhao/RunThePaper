# Paper Map

## Identity

- Paper: *Efficient simulation of logical magic state preparation protocols*
- PaperID: `2512.23799`
- Source: `https://arxiv.org/pdf/2512.23799`
- Authors: Samyak Surti, Lucas Daguerre, Isaac H. Kim
- Case type: fault-tolerant quantum computing / magic-state-preparation simulation

## Source Files

- PDF: `raw/paper.pdf`
- TeX source: `paper-source/extracted/main_v2.tex`
- Source benchmark images:
  - `paper-source/extracted/stim_and_cirq_fidelities_3.png`
  - `paper-source/extracted/stim_and_cirq_acceptance_rates_3.png`
  - `paper-source/extracted/stim_and_cirq_average_time_per_shot_4.png`
- Author CSV/code: not included in the arXiv source. The paper states that datasets and code can be made available upon request.

## Section Map

| Section | Role | Notes |
| --- | --- | --- |
| Introduction | Main claim | MSP simulation can be polynomial in qubit count and target-state nonstabilizerness. |
| Preliminaries | Core definitions | Pauli group, Clifford hierarchy, magic states, PSC, stabilizer rank, Pauli rank. |
| Toy example | Mechanism | Shows how Pauli errors propagate to end-of-circuit Clifford errors in a `[[4,2,2]]` example. |
| Controlled-Clifford / PSC | Formula gate | PSCs are Cliffords that square to Paulis; controlled PSCs sit in the third Clifford hierarchy. |
| Fidelity method | Numerical object | Fidelity is computed through Pauli-rank expectation values. |
| Appendix: error model | Simulation input | Uniform circuit-level Pauli noise with physical error rate `p`. |
| Appendix: H-state preparation | Benchmark target | Steane-code `|Hbar>` protocol compared with Stim and Cirq. |
| Appendix: error propagation algorithm | Runtime target | Propagated Clifford errors are updated with lookup-table rules. |

## Equation / Method Inventory

| ID | Paper location | Object | Needed for target | Status |
| --- | --- | --- | --- | --- |
| E001 | Eq. `magic_states` | `|T>` and `|H>` magic states | Formula gate | checked |
| E002 | Eq. `eigen_PSC` | Magic state as PSC eigenstate projection | Formula gate | traced |
| E003 | Eq. `stab_rak` | Stabilizer-rank decomposition | Runtime/method target | traced |
| E004 | Eq. `rep_rho_Paulis` | Pauli-rank density expansion | Fidelity target | checked |
| E005 | Definition PSC | Clifford `U` with `U^2` a Pauli | Formula gate | checked numerically |
| E006 | Eq. `nonclifford_identity_6` | Controlled-H propagation identity | Formula gate | checked numerically |
| E007 | Appendix error model | Initialization/gate/measurement/idling Pauli noise | Benchmark targets | implemented as feature model |
| E008 | Algorithm 1 | Error propagation algorithm | Runtime target | represented by propagated-error proxy |

## Figure / Table Inventory

| Paper item | Caption summary | Numeric? | Reproduction target? |
| --- | --- | --- | --- |
| Fig. `simulation-steps` | Schematic simulation technique | no | context only |
| Fig. `code422` | `[[4,2,2]]` code sketch | no | context only |
| Fig. `422_example` | Toy magic-state protocol circuit | no | context only |
| Fig. `422_propagation` | Error propagation circuit | no | context only |
| Fig. `non-ft-can-meas` | Non-FT measurement gadget | no | context only |
| Fig. `FT-canonical-meas-circ` | Shor-style measurement gadget | no | context only |
| Fig. `propagation_rules_visual` | Propagation rules | no | algorithm context |
| Fig. `CH-meas-circ` | Steane `Hbar` prep circuit | no | context only |
| Fig. `stim-vs-cirq-numerical-results1` | Infidelity and acceptance rate vs `p` | yes | T001, T002 |
| Fig. `stim-vs-cirq-numerical-results2` | Average time per shot vs `p` | yes | T003 |
| Fig. `error_prop_sim` | Error-location map | no | context only |
| Fig. `propagation_alg_visual` | Error propagation algorithm | no | algorithm context |

## Assumptions And Open Questions

- The arXiv source provides benchmark PNGs but not the numerical arrays behind them.
- The case therefore checks the scientific features of the benchmark curves rather than pointwise agreement.
- A full paper-grade reproduction requires a faithful clean-room implementation
  of the Steane flag gadget plus Stim/Cirq comparison runs. Author numerical
  code is outside the implementation boundary; published values may be used
  only after independent arrays are frozen.
