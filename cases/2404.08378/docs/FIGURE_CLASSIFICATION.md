# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1(a,b) | `schematic_context` | no | Chip layout and cross-section illustration. |
| Main Fig. 1(c) | `numeric_reproduction` | yes, T001 | Independently solve a declared scalar Helmholtz approximation at both wavelengths. |
| Main Fig. 1(d) | `experimental_context` | deferred | SHG wavelength-power arrays are not deposited. |
| Main Fig. 2 model | `numeric_reproduction` | yes, T002 | Compute the four transfer probabilities from the MZI unitary. |
| Main Fig. 2 measurements | `experimental_context` | deferred | Point-level powers and uncertainties are unavailable. |
| Main Fig. 3(a) | `schematic_context` | no | Experimental apparatus. |
| Main Fig. 3(b–g) model | `numeric_reproduction` | yes, T003–T008 | Lift the MZI unitary to the two-photon Fock basis. |
| Main Fig. 3(b–g) measurements | `experimental_context` | deferred | Coincidence-rate arrays are unavailable. |
| Main Fig. 4(a) | `schematic_context` | no | Experimental apparatus. |
| Main Fig. 4(b) model | `numeric_reproduction` | yes, T009 | Reproduce a visibility- and width-constrained HOM dip. |
| Main Fig. 4(b) measurements | `experimental_context` | deferred | Delay-scan coincidence points are unavailable. |
| Supplement Figs. S1–S2 | `numeric_reproduction` | yes, T010–T013 | Exact imbalance and coherence scans from the published density matrices. |
| Supplement Fig. S3 | `experimental_context` | no | Two-photon microscope image. |
| Supplement Fig. S4 | `experimental_context` | deferred | Coincidence histograms are not deposited. |
| Supplement Fig. S5(a,c,d) | `experimental_context` | deferred | Required spectral response arrays are not deposited. |
| Supplement Fig. S5(b) | `numeric_reproduction` | yes, T014 | Evaluate the published HOM visibility functional; exact spectral weighting awaits arrays. |
| Supplement Fig. S6 ideal line | `numeric_reproduction` | yes, T015 | Compute 3 dB per ideal splitter and printed excess-loss trend. |
| Supplement Fig. S6 points | `experimental_context` | deferred | Measured output powers are unavailable. |
| Supplement Fig. S7 | `numeric_reproduction` | yes, T016 | Independent evanescent-overlap loss reconstruction. |
| Brightness and bandwidth claims | `numeric_reproduction` | yes, T017–T018 | Recalculate loss correction and transform-convention arithmetic. |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
