# Figure Classification

Only results that require executing the reconstructed algorithm are treated as
numeric reproduction targets. Explanatory circuit diagrams are useful source
material but are not themselves reproduced as numerical results.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. 1 Toffoli circuit | schematic_context | No | Background quantum-circuit example. |
| Fig. 2 IBM Q20 Tokyo information | hardware_context | Partly | Coupling graph is extracted and used as the hardware model. |
| Fig. 3 SWAP/problem example | algorithm_trace | Yes | Used as the first small executable correctness target. |
| Table I notation | source_context | No | Defines notation used by algorithm cards. |
| Fig. 4 DAG/front layer | algorithm_trace | Yes | Implemented as DAG/front-layer construction checks. |
| Algorithm 1 SABRE search | algorithm_definition | Yes | Core reproduction target. |
| Fig. 5 reverse traversal | algorithm_trace | Yes | Implemented as forward-backward-forward traversal. |
| Fig. 6 SWAP search | algorithm_trace | Yes | Implemented as candidate-SWAP and heuristic checks. |
| Fig. 7 trade-off example | algorithm_trace | Yes | Implemented through decay behavior checks. |
| Table II benchmark results | numeric_reproduction | Partial first pass | Exact published values need exact original benchmark corpus and baseline. |
| Fig. 8 trade-off plot | numeric_reproduction | Yes first pass | Reproduced on locally generated circuits using the paper's decay sweep idea. |

## Scope Guard

The existing GitHub implementation or any third-party SABRE implementation is
not used as a source. Qiskit may be used only to generate/decompose circuits
for benchmark inputs, not to route them.
