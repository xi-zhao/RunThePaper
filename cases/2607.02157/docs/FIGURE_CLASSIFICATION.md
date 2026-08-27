# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Atomic items | Class | Reproduce? | W1 result |
| --- | ---: | --- | --- | --- |
| Fig. 1(a-c) | 3 panels | `schematic_context` | No | All three are explicitly excluded because they contain no numerical observable. |
| Fig. 2(a1,b1,c1) | 9 series | `numeric_reproduction` | Yes | 9/9 TFIM series mapped to T001. |
| Fig. 2(a2,b2,c2) | 9 series | `numeric_reproduction` | Yes | 9/9 cluster-model series mapped to T001. |
| Fig. S1(a) | 5 series | `numeric_reproduction` | Yes | G(omega), MG power, signal, ensemble mean, and variance are all mapped to T002. Input characterization remains eligible because it is independently generated numerical content shown by the paper. |
| Fig. S1(b) | 1 spectrum family | `numeric_reproduction` | Yes | The 64 jointly interpreted TFIM energy branches are mapped to T002 as one family. |
| Fig. S1(c) | 1 spectrum family | `numeric_reproduction` | Yes | The 64 jointly interpreted cluster-model branches are mapped to T002 as one family. |
| Fig. S2(a1-c1) | 9 series | `numeric_reproduction` | Yes | 9/9 TFIM delay/horizon series mapped to T003. |
| Fig. S2(a2-c2) | 9 series | `numeric_reproduction` | Yes | 9/9 cluster-model delay/horizon series mapped to T003. |

W1 total: **43/43 eligible numerical items covered; 0 uncovered; 3
non-numerical panels excluded**.  This is a scope statement, not a claim that
the stronger execution, physics, pixel, and independent-review gates pass.

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
