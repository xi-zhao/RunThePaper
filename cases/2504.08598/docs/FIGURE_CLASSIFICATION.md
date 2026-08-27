# Figure Classification

Only independently generable theory-numerical figures, panels, or visible
series become executable targets. Experimental measurements/images,
schematics, context, and tables are inventoried but never generated.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). Split mixed figures into panels and mixed panels into
`figure_series` items. Only ids frozen in
`physics_reproduction_project.json` under
`reproduction_scope.target_item_ids` may be targeted. Skipping a selected
theory-numerical item because it is "supporting" or "similar" is
not allowed. A selected target is regenerated from a verified formula/method;
source-image pixels are reference-only.

| Paper item | Parent item | Item type | Scientific role | Selected? | Decision | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| FIG001 | — | figure | schematic_context | no | excluded | End-to-end workflow |
| FIG002 | — | figure | schematic_context | no | excluded | Coloring examples |
| FIG003 | — | figure | schematic_context | no | excluded | Pair-potential/geometry schematic |
| FIG004 | — | figure | schematic_context | no | excluded | Level and schedule schematic |
| FIG005 | — | figure | theory_numerical | yes | target T001 | k=3 A-F curves and E/F distributions |
| FIG006 | — | figure | theory_numerical | yes | target T002 | k=4 G-I distributions |
| FIG007 | — | figure | theory_numerical | no | deferred_blocked | Protocol-c Omega conflict between Appendix A.2 and caption |
| FIG008 | — | figure | theory_numerical | yes | target T003 | k=2 appendix; failures retained |
| FIG009 | — | figure | theory_numerical | yes | target T003 | k=3 G-J appendix |
| TABLE001 | — | table | source_parameter | no | excluded | Coordinates are audited inputs consumed by T001/T002/T003A/T003B, not generated evidence |
| TABLE002 | — | table | source_parameter | no | excluded | Spacings are audited inputs consumed by T001/T002/T003A/T003B, not generated evidence |

Allowed classes:

- `theory_numerical`
- `experimental_measurement`
- `experimental_image`
- `schematic_context`
- `context`
- `source_parameter` (numeric table input only; must name consuming targets)
