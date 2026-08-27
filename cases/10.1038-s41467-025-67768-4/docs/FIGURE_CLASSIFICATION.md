# Figure Classification

Only independently generated scientific numerics are executable targets.
Experimental points remain visible later only as reference context; they are
never reconstructed from paper pixels or author arrays.

## Atomic coverage summary

- Displayed figure/table items inventoried: **47**.
- Eligible scientific numerical items: **16**.
- Covered by accepted independent evidence: **13**.
- Uncovered: **3**.
- Whole-paper item coverage: **13/16 = 81.25%**.
- Excluded context items: **31** (schematics, experimental measurements, or
  hardware/acquisition records). Exclusions do not enter the coverage
  denominator, but remain visible in the inventory.

## Items preventing 100% coverage

| Item ID | Paper location | Target | Immediate reason | Root cause | Code fault? | What would close it |
| --- | --- | --- | --- | --- | --- | --- |
| `supp_fig2_qldpc_logical_error_distribution` | Supp. Fig. 2 | T008 | No independent qLDPC distribution can be generated from the disclosed inputs. | The publication omits the executable circuit/noise process, decoder configuration, and Monte Carlo trial contract. | `not_applicable`: the calculation is underdetermined before implementation can be judged. | Obtain a citable complete benchmark contract, then independently implement and validate the decoder/sampler. |
| `supp_fig10b_logical_cnot_expectation` | Supp. Fig. 10(b) | T009 | No independent circuit-level logical-CNOT expectation curve can be generated. | The publication omits the exact lattice-surgery schedule, syndrome-round count, decoder, and sampling contract. | `not_applicable`: missing scientific inputs precede any code test. | Obtain and freeze the missing benchmark contract, then independently implement the schedule and decoder. |
| `supp_fig10c_lattice_surgery_bias_overhead` | Supp. Fig. 10(c) | T009 | No independent bias-versus-overhead curve can be generated. | Same publication underspecification as Fig. 10(b). | `not_applicable`: missing scientific inputs precede any code test. | The same T009 implementation must generate and validate both panels from one frozen numerical result. |

These three items contribute zero to the whole-paper reproduction degree.
They are not hidden by target grouping: T009 represents two separately counted
panels. More compute cannot recover an unpublished benchmark definition.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 | `schematic_context` | no | Conceptual curves and icons, with no numerical parameter set. |
| Main Fig. 2(a) | `schematic_context` | no | Circuit diagram. |
| Main Fig. 2(b) | `experimental_context` | no | Hardware measurements only. |
| Main Fig. 2(c) | `numeric_reproduction` | T001, simulation only | Exact Pauli-injection and feedback/post-selection response can be derived from the circuit. |
| Main Fig. 3(a,b) | `schematic_context` | no | Qubit layout and circuit diagram. |
| Main Fig. 3(c) | `numeric_reproduction` | T002, simulation only | Repetition-code failure model for `d=3,5,7`, `M=1`. |
| Main Fig. 3(d) | `experimental_context` | no | Derived exclusively from experimental samples. |
| Main Fig. 3(e) | `numeric_reproduction` | T003, simulation only | Multi-round repetition-code model at `d=7`. |
| Main Fig. 3(f) | `experimental_context` | no | Derived exclusively from experimental samples. |
| Main Fig. 4(a) | `schematic_context` | no | Layout/circuit diagram. |
| Main Fig. 4(b,c) | `numeric_reproduction` | T004, simulation only | Distance-3 surface-code depolarizing model. |
| Main Fig. 4(d) | `experimental_context` | no | Derived exclusively from experimental samples. |
| Main Fig. 5 | `experimental_context` | no | Processor calibration distributions. |
| Supp. Fig. 1 | `schematic_context` | no | Circuit diagram. |
| Supp. Fig. 2 | `numeric_reproduction` | deferred | Exact qLDPC circuit/noise/decoder metadata are not supplied. |
| Supp. Table 1 | `experimental_context` | no | Measured processor statistics; values are parameters only. |
| Supp. Table 2 | `experimental_context` | no | Chosen acquisition counts, not a computed scientific result. |
| Supp. Fig. 3 | `experimental_context` | no | Standard errors require the hardware shots. |
| Supp. Fig. 4 | `numeric_reproduction` | T002, simulation only | Same one-round uncorrected model as T002. |
| Supp. Table 3 | `algorithm_trace` | T007 | Values approximately, but not exactly, preserve cumulative error across `M+1` injection layers. |
| Supp. Fig. 5 | `experimental_context` | no | Bias/overhead require experimental samples. |
| Supp. Fig. 6 | `schematic_context` | no | State-preparation circuit drawing. |
| Supp. Fig. 7(a,c,e) | `numeric_reproduction` | T004, simulation only | Same surface-code model as Main Fig. 4. |
| Supp. Fig. 7(b,d,f) | `experimental_context` | no | Bias/overhead require experimental samples. |
| Supp. Fig. 8 | `numeric_reproduction` | T005 | Fully numerical comparison of partial and complete ZNE. |
| Supp. Fig. 9 | `numeric_reproduction` | T006 | Fully numerical large-scale logical-memory model. |
| Supp. Fig. 10(a) | `schematic_context` | no | Logical CNOT diagram. |
| Supp. Fig. 10(b,c) | `numeric_reproduction` | deferred | Missing exact circuit schedule, decoder, syndrome-round, and shot metadata. |

The machine-readable decisions and blockers live in `figure_coverage.json`;
T008 and T009 carry the corresponding causal records in
`outputs/checks/similarity_scorecard.json`.
