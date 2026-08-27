# Figure Classification

Only numerical figures become executable reproduction targets. Circuit drawings and algorithm diagrams are kept as context.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. `simulation-steps` | `schematic_context` | no | Explains the simulation idea; no numerical data. |
| Fig. `code422` | `schematic_context` | no | Code layout drawing. |
| Fig. `422_example` | `schematic_context` | no | Circuit diagram. |
| Fig. `422_propagation` | `schematic_context` | no | Circuit identity illustration. |
| Fig. `non-ft-can-meas` | `schematic_context` | no | Measurement gadget drawing. |
| Fig. `FT-canonical-meas-circ` | `schematic_context` | no | Measurement gadget drawing. |
| Fig. `propagation_rules_visual` | `algorithm_trace` | no | Error propagation rules, not a numerical curve. |
| Fig. `CH-meas-circ` | `schematic_context` | no | Steane-code circuit drawing. |
| Fig. `stim-vs-cirq-numerical-results1` panel a | `numeric_reproduction` | yes | Infidelity vs physical error rate `p`; benchmark compares Stim-style propagated simulation with Cirq state-vector simulation. |
| Fig. `stim-vs-cirq-numerical-results1` panel b | `numeric_reproduction` | yes | Acceptance rate vs `p`; benchmark compares the same two simulation routes. |
| Fig. `stim-vs-cirq-numerical-results2` | `numeric_reproduction` | yes | Average time per shot vs `p`; benchmark demonstrates faster propagated-error simulation. |
| Fig. `error_prop_sim` | `schematic_context` | no | Labels error locations and colors; useful for a full simulator but not itself numerical. |
| Fig. `propagation_alg_visual` | `algorithm_trace` | no | Algorithm diagram. |

## Reproduction Scope

This case reproduces the three numerical benchmark features:

1. infidelity increases with the physical error rate;
2. acceptance decreases with the physical error rate;
3. propagated Clifford simulation is much cheaper per shot at low `p`.

The exact paper curves are not digitized or pointwise matched because no underlying benchmark arrays are included in the arXiv source.
