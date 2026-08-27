# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1(a) main/inset and Fig. 1(b) | `schematic_context` (3 items) | no | Atomic geometry and qualitative uncoupled-band sketches. |
| Main Fig. 2(a) | `schematic_context` | no | Brillouin-zone construction. |
| Main Fig. 2(b) | `numeric_reproduction` | T001 | Independent pseudospin texture and winding. |
| Main Fig. 3(a), continuum/TB series | `numeric_reproduction` (2 items) | T002 | The continuum bands and analytic overlay can fail independently. |
| Main Fig. 3(b,c) | `numeric_reproduction` (2 items) | T003-T004 | DOS and Berry-curvature observables. |
| Main Fig. 3(d) | `schematic_context` | no | Honeycomb hopping sketch. |
| Main Fig. 4(a) | `numeric_reproduction` | T005 | Two-degree continuum bands. |
| Main Fig. 4(b), epsilon_23/epsilon_12 | `numeric_reproduction` (2 items) | T006 | Two independently adjudicable gap closings. |
| Main Fig. 4(c), continuum/TB boundaries | `numeric_reproduction` (2 items) | T007 | Two independently adjudicable phase boundaries. |
| Supplement Fig. 5(a,b) | `numeric_reproduction` (2 items) | D001-D002, blocked | Exact first-principles input contract is not published. |
| Supplement Fig. 6(a,b) | `numeric_reproduction` (2 items) | T008-T009 | Independent massive-Dirac spectra. |
| Supplement Fig. 7(a,b) | `numeric_reproduction` (2 items) | T010-T011 | Independent spin-mixed spectra. |
| Supplement Fig. 8(a) main/inset and Fig. 8(b) | `schematic_context` (3 items) | no | AB structure, inversion and qualitative band sketches. |
| **Total** | **16 theory + 8 context** | **14/16 covered** | Every item has a source location and explicit decision. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`

The source TeX and original figures may be read to understand the paper and
classify layout, but no author code, author numerical array, digitized curve or
original-image pixel enters scientific generation.
