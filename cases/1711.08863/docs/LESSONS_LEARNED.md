# Lessons Learned

## Case Summary

- PaperID: `1711.08863`
- Eligible reproduction items: one numerical figure plus three independent
  analytic claim families
- Covered/uncovered: 1/3; coverage 25.00%, degree 20.16
- Main blocker: claim-specific methods for T002-T004 are absent; independent
  review remains a separate lifecycle gate

## Generalized Experience

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| Implement the general formula and the plotted closed form independently | It detects transcription and multiplicity errors before visual comparison | Require two representations when a paper provides both. |
| Count curves, not only figure numbers | A single panel can contain many distinct scientific observables | Record series semantics explicitly in each target. |
| Freeze data before opening the reference render | It proves visual tuning cannot alter scientific arrays | Keep numerical and RenderContract channels separate. |
| Do not send analytic sweeps to a GPU | Resource selection is part of efficiency | Estimate arithmetic complexity before using A100. |
| Separate reproducer falsification from independent paper assessment | A stable mismatch can still be a transcription or implementation defect | Persist a protocol-v2 pre-review artifact, but keep the assessment inconclusive until fresh review. |
| Test operator labels with a one-channel limit | Scalar coefficients can look correct while the Lindblad operator is attached to the wrong atom | Set all other couplings to zero and inspect the affected population derivative. |
| Do not equate “only one numerical plot” with “only one scientific result” | Theory papers may place their main results in equations and prose around schematic figures | After display classification, enumerate independent display-less analytic claims before declaring 100% coverage. |

## New Failure Modes

- Legacy plotting libraries can use materially different default dash lengths
  and draw order. Treat these as versioned RenderContract fields; never alter
  the frozen numerical arrays to compensate for raster differences.
- A failed isolated run may still leave a visually plausible staging artifact.
  Only artifacts named by a successful attestation may enter the authoritative
  project model.
- Excluding a schematic panel must not silently exclude the analytic theorem
  explained by its surrounding text; display role and scientific-claim role
  are separate decisions.

## Reusable Checks Or Tools

- The general point-pair enumerator provides an independent oracle for any
  closed giant-atom coefficient table.
- The hash-guarded renderer rejects any changed data CSV before source-aware
  presentation tuning begins.
- The campaign module validates immutable config-bound checkpoints before
  resume and aggregates only complete nonoverlapping shards.

## Harness Backlog Items

- Record plotting-library dash patterns and curve draw order explicitly in the
  RenderContract when validating legacy scientific figures.
- Add a reusable review check that asks whether each excluded schematic has an
  independent analytic claim in its surrounding text; this case exposed three
  missing whole-paper items.
