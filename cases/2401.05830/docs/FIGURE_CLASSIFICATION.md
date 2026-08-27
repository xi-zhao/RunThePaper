# Figure Classification

Only numerical figures/tables become executable reproduction targets.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). The default is reproduce; skipping a numeric item because it
is "supporting" or "similar to another figure" is not allowed.

| Paper item | Atomic classification | Decision / target | Reason |
| --- | --- | --- | --- |
| Main Figure 1 | 3 `schematic_context` regions | excluded | Cartoon, energy-level diagram, and pulse sequence; no evaluated numerical observable. |
| Main Figure 2 left | 3 theory series + 3 measured series | theory: T001; experiment: excluded | Three fitted loci are formula-generated; measured markers/error bars remain visible inventory rows but are not reconstructed. |
| Main Figure 2 right | 1 theory series | T002 | Slow-mode coefficient from the paper-normalized expression, independently checked by mode annihilation. |
| Main Figure 3 top/bottom | 2 experimental panels | excluded | Raw and smoothed hardware tomography are measurements, not formula-runner outputs. |
| Main Figure 4 | 2 theory + 2 experimental series | theory: T003; experiment: excluded | Both continuous-model predictions are reproduced; raw/smoothed measurements are not reconstructed. |
| Main Figure 5 main/inset | 2 experimental items | excluded | Direct-preparation tomography and its measured difference contain no plotted theory layer. |
| Supplemental Figure 1 | 4 theory series | T004 | Zero, x, fast and slow Liouvillian eigenvalue branches. |
| Supplemental Figure 2 | 7 theory series | T005 | Five printed `alpha` loci and two discriminant-zero branches. |
| Supplemental Figure 3 | 2 theory series | T006 | The `alpha=1` locus and the displayed fast-mode chord family. |
| Supplemental Figure 4 left | 3 theory series | T007 | Three printed full relaxation trajectories. |
| Supplemental Figure 4 right | 3 theory series | T008 | Three late-time zoom trajectories. |
| Supplemental Figure 5 left/right | 2 theory series | T009/T010 | Crossing-time and maximum-advantage sweeps. |

Display inventory totals: 39 items = 27 theory numerical + 9 experimental measurement +
3 schematic. All 27 theory items are covered. Two additional no-display quantitative claims are
eligible and currently uncovered:

| Claim | Location | Decision | State |
| --- | --- | --- | --- |
| `claim_dissipator_rate_factor_two` | Main Eqs. (1)-(2) vs Supplement Eqs. (1)-(4) | T011 | uncovered; source conflict needs fresh adjudication |
| `claim_hamiltonian_prose_factor_two` | Main experimental paragraph vs all executable equations | T012 | uncovered; source conflict needs fresh adjudication |

The experimental exclusions do not authorize digitization. A continuous-model
counterpart may be generated as a diagnostic, but it must not be labeled as the
raw or smoothed experimental panel.

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
