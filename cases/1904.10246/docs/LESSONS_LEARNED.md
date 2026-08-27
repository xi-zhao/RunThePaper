# Lessons Learned

## Case Summary

- Paper: *Amplitude Estimation without Phase Estimation*
- PaperID: `1904.10246`
- Result: four paper-exact numerical targets reproduced
- Scientific score: `93.75`
- Pixel contracts: `4 / 4 passed`
- Main blockers: none

## What Worked

- Treating each paper item as a target-local state machine kept outputs and
  evidence isolated.
- Formula and method gates caught ambiguities before simulation.
- Exact schedule identities and analytic table formulas provided cheap,
  high-value checks independent of Monte Carlo noise.
- A global likelihood grid followed by bounded parabolic refinement reproduced
  the paper scaling in seconds on a laptop.
- Keeping source crops out of generated-data paths made the provenance boundary
  mechanically visible.

## New Failure Modes

- A visually plausible plot can fail a declared pixel contract because its
  typography shifts ink overlap even when axes and data are correct.
- Enlarging typography to match a source crop can clip the generated x-axis
  label; margin checks must remain active during pixel tuning.
- Resource tables can match every number while still missing a grouped header,
  so table layout requires a separate visual review.

## Reusable Checks Or Tools

- Closed-form versus direct-sum checks for schedule and circuit resources.
- An analytic `m=0` MLE identity for the classical estimator.
- Target-scoped runners that require both target ID and reproduction stage.
- Pixel crop evidence with axis IoU, density ratio, ink overlap, and margin
  contracts.
- Source/generated/difference boards created only after independent data exist.

## Generalized Experience

| Lesson | Why it generalizes | Recommendation |
| --- | --- | --- |
| Separate science from pixels | Visual agreement cannot establish numerical independence. | Maintain distinct scientific and pixel contracts. |
| Use formula identities as preconditions | Cheap invariants catch model errors before expensive runs. | Gate every target on executable identities. |
| Tables need semantic and visual validation | Exact cells do not ensure faithful hierarchy. | Check both cell values and grouped headers. |
| Record bounded repairs | Pixel iteration can otherwise become untraceable. | Store before/after metrics and whether science changed. |

## Backlog Boundary

This Trial does not edit the frozen Harness or `HARNESS_BACKLOG.md`. The lessons
remain case-local evidence for `1904.10246`.
