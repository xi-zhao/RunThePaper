# Figure Classification

The paper is reviewed as a scientific whole. Numerical figures, equations,
quantitative statements, limits, and method-dependent claims must all be
enumerated. Figure classification below decides which visual objects require a
rendered comparison; it does not exclude non-figure scientific claims from
executable targets or claim-level review.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 band axes | `numeric_reproduction` | yes, T001 | Independent diagonalization of Eq. (6) at printed `t2/t=.03`. |
| Main Fig. 1 lattice inset | `schematic_context` | no | Geometry illustration; only the theoretical band axes are reproduced. |
| Main Fig. 2(a) | `algorithm_trace` | yes, T008 | The drawing is schematic, but the displayed two-terminal conductance label `2e^2/h` is an eligible subfigure-level quantitative item reproduced without tracing the cartoon. |
| Main Fig. 2(b) | `algorithm_trace` | yes, T009 | The drawing is schematic, but the displayed four-terminal spin-current label `eV/4pi` is an eligible subfigure-level quantitative item reproduced without tracing the cartoon. |
| Main Fig. 3 | `schematic_context` | no | Feynman diagram, no numerical dataset. |
| Tables | `not_in_scope` | no | The paper contains no tables. |
| Supplemental material | `not_in_scope` | no | The official archive contains no supplement. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
