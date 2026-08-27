# Figure Classification

Numerical figures/tables and independent analytic claims become reproduction
targets. A claim already represented by a display item is not counted twice.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. 1 left/right | `schematic_context` (2 items) | no | Conceptual before/after feature-space illustration. |
| Fig. 2 | `schematic_context` | no | Feature-map/kernel/RKHS relationship diagram. |
| Fig. 3 implicit/explicit | `schematic_context` (2 items) | no | Workflow schematics; equations feed numerical targets. |
| Fig. 4, c=1.0/1.5/2.0 | `numeric_reproduction` (3 items) | T001 | Three independently adjudicable kernel surfaces. |
| Fig. 5, six panels | `numeric_reproduction` (6 items) | T002 | Six independently identifiable SVC decision maps. |
| Fig. 6, epochs 1/500/5000 | `numeric_reproduction` (3 items) | T003 | Three finite-dataset perceptron states. |
| Fig. 7(a-c) | `schematic_context` (3 items) | no | Architecture/circuit/gate-block drawings; equations feed T004. |
| Fig. 8 probability map and loss series | `numeric_reproduction` (2 items) | T004 | Two scientific outputs; inset is a view of the same loss series. |
| Appendices B-D universal separability theorem | `numeric_reproduction` / analytic claim | T005, qualified pass | Dedicated rank, Gram, label and counterexample tests are independent from Fig. 6. |
| **Total** | **22 display items + 1 analytic claim** | **15/15 eligible items covered** | Eight schematics are excluded from the denominator. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`

Source figures are reference material for understanding and post-freeze render
comparison only. No source pixel, author array or author implementation enters
scientific generation.
