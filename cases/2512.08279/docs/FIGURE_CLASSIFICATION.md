# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 (`FIG001`) | `schematic_context` | No | Conceptual wiring diagram; contains no independently generated numerical quantity. |
| Main Fig. 2 (`FIG002`) | `numeric_reproduction` | Yes, `T001` | Plots a closed-form time-dependent observable and finite quasisampling estimates. |
| Main Fig. 3 (`FIG003`) | `numeric_reproduction` | Yes, `T002` | Plots two 41-point SDP cost curves from paper-linked parameters. |
| Supplemental SWAP–dephasing protocol (`FIGS001`) | `schematic_context` | No | Circuit/process diagram supporting the Fig. 2 derivation. |
| Supplemental amplitude-damping circuit (`FIGS002`) | `schematic_context` | No | Quantikz circuit; no numerical data. |
| Supplemental six-operation HPTP protocol (`FIGS003`) | `schematic_context` | No | Circuit/process diagram supporting Proposition 4; no numerical data. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`

No experimental or literature-derived figures occur in this paper. There are
no tables. Both numerical main-text figures are targeted; none is deferred.
