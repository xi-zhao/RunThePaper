# Lessons Learned

## Case summary

- Paper: *Phase Structure of Driven Quantum Systems* (`1508.03344`).
- Scope: 7/7 numerical targets implemented; 12/12 science checks pass.
- Status: numerical-feature reproduction; one target paper-exact, six reduced.
- Main blockers: measured paper-scale compute cost and two publication
  ambiguities.

## Reusable lessons

| Lesson | Evidence | Future rule |
| --- | --- | --- |
| Separate code readiness from compute execution | complete runner/config vs 652-day CPU lower bound | compute-only defer is valid only with attested smoke plus real resource benchmark |
| Keep printed inconsistency explicit | Eq. (7) complex literal; incompatible duration statements | branch conventions; never silently choose/fix and never call it a paper error without fresh review |
| Finite-size parity changes presentation | L=8 even separation vs paper L=10 odd separation | diagnose parity before styling or sign manipulation |
| Render acceptance must follow data freeze | five hashes unchanged across rendering | source-aware rendering may tune style only, never physics |
| White-background pixel score is incomplete | primary scores >85 while foreground scores are much lower | retain scientific checks and foreground/SSIM as diagnostics; pixel cannot override physics |

## Failure-mode classification

- The v3 isolation failure was a **contract implementation defect**, fixed in
  v4; it was not a physics-code defect.
- Paper-scale absence is **compute capacity**, not “parameter not exact”.
- T005/T006 are **publication underspecification**, not compute problems and not
  confirmed paper errors.

## New Failure Modes

| Failure mode | Where it appeared | Detection rule |
| --- | --- | --- |
| Source formula is formally complex although the plot is positive | Eq. (7), T005 | evaluate the literal printed form and a physical positive form separately; record both |
| Printed time conventions cannot all hold | Eq. (8), paragraph and caption, T006 | dimensionally reconcile every period/duration statement before execution |
| Finite-size parity changes curve sign | T006, L=8 versus L=10 | audit separation parity before considering any render-layer sign change |

## Reusable Checks Or Tools

| Candidate | Why reusable | Suggested destination |
| --- | --- | --- |
| GPU pilot estimator | turns a real one-shard measurement into a scheduler budget without assumed speedup | Harness performance tooling |
| printed-convention consistency check | catches incompatible period/step definitions before paper-scale execution | formula/method gate |

## Harness backlog candidate

Add a reusable GPU pilot estimator that reads a paper-scale work-unit manifest,
runs one backend-parity shard, and emits a scheduler-hour request without
assuming an unmeasured accelerator speedup.
