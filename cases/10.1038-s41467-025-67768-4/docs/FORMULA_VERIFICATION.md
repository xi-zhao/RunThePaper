# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Evidence |
| --- | --- | --- | --- |
| ZNE001 | Uniform-noise polynomial | open | Source expansion plus order-count identity |
| ZNE002 | Distance-aware weights | open | Source matrix plus moment-cancellation checks |
| ZNE003 | Bias and overhead | open | Source definitions plus independent variance derivation |
| FB001 | Feedback response | open, reconstructed | Closed form agrees with independent 64-pattern enumeration |
| REP001 | Repetition logical failure | open, reconstructed | Binomial normalization, low-noise order, multi-round identity |
| SURF001 | Distance-3 logical Pauli channel | open, reconstructed | Stabilizer commutation, distance, and probability normalization |
| MEM001 | Large-scale logical-memory fit | open | Primary-reference coefficients reproduce the paper's `d=11` anchor |

`reconstructed` means the paper supplies the circuit/model but not the final
closed form used here. It does not mean a curve was inferred from pixels.
