# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper scope | Atomic units | Class | Reproduce? | Reason |
| --- | ---: | --- | --- | --- |
| Main Fig. 1 upper device drawings | 2 | `schematic_context` | no | Physical illustrations without numerical observables. |
| Main Fig. 1 lower energy diagrams | 2 | `numeric_reproduction` | T001 | Directional energies and resonance detunings follow Eq. (3). |
| Main Fig. 2 | 1 | `numeric_reproduction` | T002 | Three Lindblad g2 curves; inset is the same data. |
| Main Fig. 3(a-c) | 5 | `numeric_reproduction` | T003 | Correlations, two separate criteria, and two directional distributions. |
| Main Fig. 3(d) | 2 | `numeric_reproduction` | T004 | Two independently evaluable directional level diagrams. |
| Main Fig. 4(a-c) | 5 | `numeric_reproduction` | T005 | Correlations, two separate criteria, and two directional distributions. |
| Supplement Figs. S1-S9 | 47 | `numeric_reproduction` | T006-T014 | Every labeled theory subpanel or independently adjudicable series is enumerated. |
| Supplement Table I | 1 | `literature_or_external_context` | no | Synopsis of earlier literature, not a new model output. |
| Supplement Table II | 1 | `numeric_reproduction` | T015 | Eight formula-derived allowed/prohibited resonance cases form one table item. |
| **Total** | **65** | **62 theory + 3 context** | **62/62 targeted** | Complete 36-page source boundary. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`

Mixed-figure rule: excluding the device artwork does not exclude the theoretical
energy-level portion of Main Fig. 1. Supplement Fig. S3 is split into sixteen
directional level series because either direction can fail independently;
Supplement Fig. S6 is similarly split into independent g2 and g3 comparison
families. No original-image pixels, author arrays/code, or schematic artwork
enter the numerical generator.
