# Figure Classification

Only executable numerical figures are reproduced. Hardware drawings, workflow diagrams, and optical setup pictures are kept as context.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. 1 workflow | `schematic_context` | no | It explains the experiment workflow; it is not a numerical result. |
| Fig. 2a-f photonic chip and components | `experimental_context` | no | These panels describe fabricated hardware and measurement setup. |
| Fig. 2g-h output probability distributions | `numeric_reproduction` | yes | The theoretical two-photon probability distributions are generated from `U(t)=exp(-iHt)`. Experimental bars are out of scope without raw chip counts. |
| Fig. 3 PT distance, Shannon entropy, SFF | `numeric_reproduction` | yes | Main numerical claim: chaotic dynamics approach PT statistics and entropy maximum near the SFF dip. |
| Fig. 4 OTOC-equivalent observables and PR | `numeric_reproduction` | yes | Main numerical claim: chaotic dynamics delocalize more strongly than integrable dynamics. |
| Fig. S1 conditional probability proof | `numeric_reproduction` | yes | Sanity check that collision-free post-selection still approximates PT statistics for `D=28`. |
| Fig. S2 experimental setup | `experimental_context` | no | Hardware setup figure, not a numerical target. |
| Fig. S3 chip decomposition | `schematic_context` | no | MZI mesh diagram; not a data figure. |
| Fig. S4 scaling results | `numeric_reproduction` | yes | Supporting numerical claim that the probes improve as mode number grows. |
| Fig. S5 ideal OTOCs | `numeric_reproduction` | yes | Supporting OTOC dynamics for all collision-free output configurations. |
| Fig. S6 short-time OTOC / FFT PR | `numeric_reproduction` | yes | Supporting numerical checks for power laws and late-time frequency delocalization. |

## In-Scope Targets

- T001: Fig. 2g-h theoretical output distributions.
- T002: Fig. 3 PT distance, Shannon entropy, and 4-point SFF proxy.
- T003: Fig. 4 OTOC-equivalent probabilities and participation ratio.
- T004: Fig. S1 conditional probability validation.
- T005: Fig. S4 scaling summary.
- T006: Fig. S5 ideal OTOCs for all configurations.
- T007: Fig. S6 short-time power laws and FFT participation ratio.
