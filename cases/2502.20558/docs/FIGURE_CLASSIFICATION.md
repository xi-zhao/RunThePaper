# Figure Classification

Every one of the paper's 27 figures and its numerical table is classified
before implementation. Final labels distinguish reproduced scope from targets
that a bounded formula/method-driven clean-room campaign attempted but did not
reproduce; no numeric group is left pending merely because author artifacts are
absent.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. 1 | `schematic_context` | no | Conceptual circuit and space-time drawing. |
| Fig. 2(a) | `algorithm_trace` | no | Lifecycle illustration. |
| Fig. 2(b) | `numeric_reproduction` | proxy; attempted not reproduced | Mechanism is tested independently at d=5 and p_loss=1%; the bounded clean-room implementation does not reproduce the absolute surface-code curve. |
| Fig. 3(a-c) | `schematic_context` | no | Three SE circuit constructions. |
| Fig. 3(d) | `numeric_reproduction` | attempted not reproduced | Logical error vs SE rounds, d=7, p=1%; current clean-room system-capability limit. |
| Fig. 3(e) | `numeric_reproduction` | attempted not reproduced | Threshold vs loss fraction; current clean-room system-capability limit. |
| Fig. 3(f) | `numeric_reproduction` | attempted not reproduced | Effective distance vs loss fraction; current clean-room system-capability limit. |
| Fig. 3(g) | `numeric_reproduction` | attempted not reproduced | Space-time overhead; current clean-room system-capability limit. |
| Fig. 4(a) | `numeric_reproduction` | attempted not reproduced | Pauli- and loss-axis threshold fits were attempted but not reproduced. |
| Fig. 4(b) | `numeric_reproduction` | yes, partial | Recompute the printed `7/lifecycle^(1/3)` relation; finite-size points were attempted but not reproduced. |
| Fig. 5(a) | `schematic_context` | no | Random logical circuit construction. |
| Fig. 5(b,c) | `numeric_reproduction` | attempted not reproduced | 24-layer multi-logical-qubit circuit-level simulations reached the current clean-room capability limit. |
| Fig. 6(a) | `schematic_context` | no | Teleported logical gate. |
| Fig. 6(b) | `numeric_reproduction` | yes | Values and rules are printed in Appendix G. |
| Fig. 7(a) | `schematic_context` | no | Small-angle-synthesis-like circuit. |
| Fig. 7(b) | `numeric_reproduction` | attempted not reproduced | 11-layer d=7 circuit-level simulation reached the current clean-room capability limit. |
| Fig. 8 | `algorithm_trace` | no | Detector activation example. |
| Fig. 9 | `algorithm_trace` | no | Approximate MLE construction. |
| Fig. 10 | `numeric_reproduction` | attempted not reproduced | Omega sweep reached the current clean-room circuit/decoder capability limit. |
| Fig. 11 | `numeric_reproduction` | attempted not reproduced | 2D erasure-bias threshold sweep reached the current clean-room capability limit. |
| Fig. 12 | `numeric_reproduction` | attempted not reproduced | 2D loss-bias threshold sweep reached the current clean-room capability limit. |
| Fig. 13 | `schematic_context` | no | SWAP circuit cancellation identity. |
| Fig. 14(a,b) | `schematic_context` | no | SWAP lifecycle cartoons. |
| Fig. 14(c) | `numeric_reproduction` | yes | Average all-qubit lifecycle follows circuit counting. |
| Fig. 15(a,b) | `numeric_reproduction` | attempted not reproduced | The movement-error formula is verified; the Monte Carlo sweep reached the current clean-room capability limit. |
| Fig. 16(a) | `numeric_reproduction` | yes, partial | Recompute conventional data/measure/all counts and the all-qubit SWAP invariant. |
| Fig. 16(b) | `numeric_reproduction` | attempted not reproduced | Logical-error circuit simulation was attempted but not reproduced. |
| Fig. 17 | `schematic_context` | no | RHG/XZZX cluster construction. |
| Fig. 18 | `schematic_context` | no | Steane-to-Knill circuit identity. |
| Fig. 19 | `schematic_context` | no | Steane/MBQC interpolation. |
| Fig. 20 | `schematic_context` | no | Error-model sphere. |
| Fig. 21 | `schematic_context` | no | Algorithm circuits used for lifecycle counting. |
| Fig. 22 | `numeric_reproduction` | attempted not reproduced | Logical error vs rounds for three loss fractions reached the current clean-room capability limit. |
| Fig. 23 | `numeric_reproduction` | attempted not reproduced | Loss-only threshold sweeps reached the current clean-room capability limit. |
| Fig. 24 | `numeric_reproduction` | attempted not reproduced | Loss-only effective-distance sweeps reached the current clean-room capability limit. |
| Fig. 25 | `numeric_reproduction` | attempted not reproduced | Correlated Z-loss threshold sweeps reached the current clean-room capability limit. |
| Fig. 26 | `numeric_reproduction` | attempted not reproduced | Correlated Z-loss effective-distance sweeps reached the current clean-room capability limit. |
| Fig. 27 | `schematic_context` | no | Scheduling illustration. |
| Table I, analytic rows | `numeric_reproduction` | yes | Lifecycle and space-time rows follow printed circuit counts. |
| Table I, simulation rows | `numeric_reproduction` | attempted not reproduced | Threshold/effective-distance values reached the current clean-room capability limit. |

Separately, the Error Model B channel definition is `externally_blocked`: Table
I and Appendix F publish incompatible four-branch definitions, and the supplied
publication materials do not identify an authoritative one.
