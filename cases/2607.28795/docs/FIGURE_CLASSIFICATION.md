# Figure and Table Classification

Only independently generated numerical objects are executable targets. A
schematic is not recreated merely because it appears in the paper, and printed
plot pixels or table values never become reproduction data.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. 1(a-b) | `schematic_context` | no | Architecture and logical-gadget illustration. |
| Fig. 2(a) | `numeric_reproduction` | deferred | Paper-scale memory curves require up to 100 billion SE rounds plus exact circuits and schedules. |
| Fig. 2(b) | `numeric_reproduction` | deferred | Surgery panel reports 1-15 billion experiments; deliberately skipped as oversized. |
| Fig. 3 | `algorithm_trace` | no | Discovery-pipeline flowchart. |
| Fig. 4(a-b) | `schematic_context` | no | Atom-movement and multilayer-layout illustrations. |
| Fig. 5(a-d) | `schematic_context` | no | Gadget topology illustrations, not plotted numerical observables. |
| Fig. 6 | `schematic_context` | no | Protocol diagram; its closed-form resource counts are reproduced as T002/Table V. |
| Fig. 7 | `algorithm_trace` | no | Symbolic block-matrix layout used in the derivation. |
| Fig. 8 | `numeric_reproduction` | yes, T003 | Reimplement Algorithm 1 and measure a bounded workload; label it reduced-scale/hardware-mismatched. |
| Fig. 9 | `numeric_reproduction` | deferred | Requires an external detector-error model, incompletely specified decoder tuning, and billions of shots. |
| Fig. 10 | `schematic_context` | no | Example group permutation drawn as atom positions. |
| Fig. 11 | `schematic_context` | no | Example semidirect-product permutation drawn as atom positions. |
| Fig. 12 | `numeric_reproduction` | deferred | Exact hook-free schedules and optimized block layouts are available only through the forbidden author release. |
| Fig. 13 | `schematic_context` | no | Tanner-graph thickness proof illustration. |
| Table I, code algebra columns | `numeric_reproduction` | yes, T001 | Recompute `n,k`, rate, check weight, commutation, ranks, and canonical logical weights from Tables VII/XIII and Eqs. (1)-(4). |
| Table I, distance/gadget/hardware columns | `numeric_reproduction` | deferred | Covered by the detailed Tables II-IV, VIII, XI, and XII blockers below. |
| Table II | `numeric_reproduction` | deferred | Exact optimized surgery graphs are not specified in the PDF. |
| Table III | `numeric_reproduction` | deferred | Random logical-product instances, seeds, and saved merged codes are absent. |
| Table IV | `numeric_reproduction` | deferred | Exact optimized extractor graphs are absent. |
| Table V | `numeric_reproduction` | yes, T002 | Every entry follows directly from Eq. (E15) for printed `|G|` and `d_rep`. |
| Table VI, mitten rows | `numeric_reproduction` | yes, T001 | Same independent code constructor and canonical basis as Table I. |
| Table VI, other families | `numeric_reproduction` | deferred | The case is scoped to the eight mitten processors; extending all alternative families is not needed to test the central claim. |
| Table VII | `not_in_scope` | no | Group-definition parameter card used by T001. |
| Table VIII | `numeric_reproduction` | deferred | Exact SE layer orderings are stated to live in the author repository and cannot be inspected. |
| Table IX | `numeric_reproduction` | deferred | Billion-shot decoder benchmark and exact tuning are oversized/incomplete in the PDF. |
| Table X | `numeric_reproduction` | yes, T004 | Recompute every utilization ratio and mean latency from Eq. (I1) and the reported stage inputs. |
| Table XI | `numeric_reproduction` | deferred | Exact schedules and optimized data-qubit permutations are missing from the PDF. |
| Table XII | `numeric_reproduction` | deferred | HAL routed layouts and stochastic optimization seeds are not provided in the PDF. |
| Table XIII | `not_in_scope` | no | Construction parameter source used by T001, not an output claim. |

The user explicitly permits oversized tasks to be skipped. This affects run
selection, not scientific labeling: every skipped numerical item remains in the
machine-readable coverage contract with a concrete blocker and rerun need.
