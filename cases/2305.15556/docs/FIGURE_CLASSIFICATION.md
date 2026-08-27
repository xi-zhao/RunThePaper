# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1(a) | `numeric_reproduction` | yes, T001 | Husimi-Q probability from the printed CSS and OAT Hamiltonian |
| Main Fig. 1(b) | `numeric_reproduction` | yes, T002 | Husimi-Q probability at `chi t=N^(-2/3)` |
| Main Fig. 1(c) | `numeric_reproduction` | yes, T003 | three QFIM eigenvalues plus the printed analytic formula |
| Main Fig. 1(d) | `numeric_reproduction` | yes, T004 | QFIM eigenvector path and QFI color |
| Main Fig. 2(a) | `numeric_reproduction` | yes, T005 | largest eight QFIM eigenvalues and restricted subgroup optimum |
| Main Fig. 2(b) | `numeric_reproduction` | yes, T006 | 15 optimal-generator coefficients; degenerate gauges disclosed |
| Supplement Fig. S1 | `schematic_context` | no | commutative diagram with no evaluated numerical observable |

The paper and supplement contain no numerical tables and no other figure
panels. All six numeric panels are targets; none is deferred.

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
