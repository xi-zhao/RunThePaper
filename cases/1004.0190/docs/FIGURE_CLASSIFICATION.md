# Figure Classification

Only display items are classified here. Text-only quantitative claims are
authored separately in `figure_coverage.json` and `PAPER_MAP.md`.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 | `numeric_reproduction` | yes, T003/T004 | The tetrahedron, octahedron, zero-discord lines, Bell vertices, and separable extrema are all generated from the paper's Bloch-tensor formulas. |
| Main Fig. 2 | `schematic_context` | no rendered target; quantitative content targeted by T005/T006 | The circuit drawing itself is schematic, but the displayed DQC1 workflow and captioned trace/discord statements are reproduced as text-carried quantitative claims without tracing the source artwork. |
| Tables | `not_in_scope` | no | The paper contains no tables. |
| Supplementary material | `not_in_scope` | no | No supplementary numeric item is attached to this publication. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
