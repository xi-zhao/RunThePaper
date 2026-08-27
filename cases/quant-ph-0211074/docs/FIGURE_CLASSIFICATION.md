# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 | `numeric_reproduction` | yes, T001 | Every surface value follows from Eqs. (8)--(13) for the noncritical Ising chain. |
| Main Fig. 2 | `numeric_reproduction` | yes, T002 | All Ising, XX, and N=20 XXX entropy series and both CFT guide lines are numerical. |

There are no schematic or experimental figures, tables, or supplements. The
machine-readable contract also inventories nine non-figure quantitative
claims. Eight are assigned to T001--T003; the generic higher-dimensional area
law is deferred because the publication does not define a paper-exact numerical
problem. The complete claim ledger is in `QUANTITATIVE_CLAIM_AUDIT.md`.

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
