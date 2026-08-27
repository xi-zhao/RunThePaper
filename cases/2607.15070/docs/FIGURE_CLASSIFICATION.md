# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| FIG001 / paper Fig. 1 | `schematic_context` | No numerical target | Plate geometry drawn as an illustration; it contains no computed values, curve, or table. The source image remains contextual evidence only. |
| FIG002 / paper Fig. 2(a,b) | `numeric_reproduction` | Yes, T001 | Two independently computed proper-time integrals for four masses. Both panels and every visible series are included. |
| FIG003 / paper Fig. 3 | `numeric_reproduction` | Yes, T002 | Ratio constructed from independently evaluated Landau-like and additional contributions for all four masses. |
| Tables | not applicable | No | The paper contains no tables. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`

Figure 1 is excluded because it is genuinely non-numerical, not because it is
low priority. All numerical figures are targeted.
