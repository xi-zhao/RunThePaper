# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: *Energy Spectra of Compressed Quantum States*
- PaperID: `2507.07191`
- Final status: numerical feature reproduction; declared targets complete, full paper scope incomplete
- Main reproduced targets: PRL-Bench idx91, Figure 1, Lambda(D), and Figure 2 Predict+
- Main blockers: unreleased DMRG states and degenerate-eigenspace convention

## What Worked

- The paper's strict-concavity proof gives a safer root solver than an
  unconstrained `findroot` call.
- Full-precision structured output lets residuals be checked independently of
  rounded display values.
- One checkpointed AFHM spectrum can serve several downstream paper assets;
  recomputing the same 65,536-state object per figure would be wasteful.
- Source vector PDFs are quantitative data: exact curve and marker coordinates
  provide much stronger validation than a visual screenshot comparison.

## What Was Difficult

- Frozen gold mixed a correct root with a noncanonical example residual.
- The HM support statement required an active-subset proof not written in the
  benchmark solution.
- Small batched SVDs were initially launch-bound on A100. Raising the runtime
  batch from 256 to 2048 reduced sector-6 entropy time to 58 seconds and made
  the two largest sectors practical without changing checkpoints or physics.
- The published tuned m column is sensitive to unreported eigenvector choices
  inside degenerate AFHM eigenspaces; averaged Figure 1 curves and Predict+
  curves can match while individual-M_i-derived m still misses printed digits.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Residuals are acceptance thresholds, not gold constants | Solver precision changes the last residual digits | Store a maximum residual and a root tolerance separately. |
| Support claims require active-set semantics | A decomposition may list zero coefficients | Check the largest feasible subset or prove all KKT weights positive. |
| Paper-derived benchmark is a distinct product state | Synthetic parameters can validate a theorem without reproducing a paper figure | Label scope explicitly and keep paper-figure coverage separate. |
| Shared scientific state should be a first-class artifact | Figure 1, Lambda(D), and Predict+ all depend on the same AFHM spectrum | Checkpoint once by symmetry sector and let target runners consume it. |
| A visible curve may be reproducible even when an intermediate scalar is not | Gaussian broadening and bin averages are less sensitive to degenerate-basis rotations than individual M_i values | Gate each published asset separately; never let one close curve silently certify all intermediates. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Boundary optimizer initialization | SLSQP starting at the maximum-compression point stopped at a worse feasible boundary | Use analytic Jacobians and an interior-facing deterministic warm start; keep the proof-backed solver authoritative. |
| Treating every paper asset as one all-or-nothing figure | Figure 2 mixes Actual, Predict+, and Predict series with different input requirements | Split panels into series-level coverage items and declare blockers per series. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Source/formula gate before numerics | Formula-heavy synthetic benchmarks | Eight equation cards passed before the solver was implemented. |
| Independent primal check | Closed-form or dual optimizers | SLSQP agreed within `2.2e-11` in probability. |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Noncanonical residual gold | Task 2 | Recompute at multiple working precisions and gate by an upper bound. |
| Inactive-index support shortcut | Task 5 | Maximize inverse weights over all support-size-minus-one subsets. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Residual-policy audit | Applies to any high-precision benchmark | Future benchmark-gold audit helper. |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Strict-concavity bracketed dual bisection | 303 iterations, complete artifact in under one second | Keep case-local until a second domain uses the same model. |
| Fixed-magnetization ED plus spin-flip reuse | Full 16-spin spectrum with only sectors 0-8 and resumable checkpoints | Promote as a reusable many-body reproduction pattern after a second case. |
| Legacy source-asset comparison | A post-freeze comparison lane existed in the historical case | Keep it out of the public package; never use source coordinates to set physical parameters or generated arrays. |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`private validation harness/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`private validation harness/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| medium | H066: add benchmark residual-contract and active-support gates | Frozen residual changed with precision while the root stayed fixed, and support required an active-subset proof | proposed |
| medium | H067: add a terminal completed-target state to the reproduction loop | Every claim and audit passed, but the generic loop still requested a state adapter instead of stopping cleanly | implemented in `42e3e56` |
| medium | H068: report declared-target completion and full-paper completion as separate axes | T001-T004 pass while DMRG-dependent source series remain blocked | demonstrated in this migration |

## Prompt Or Workflow Changes

- For paper-derived benchmark cases, require an explicit `synthetic` versus
  `paper-reported` scope field before scoring.
- Inventory compound figures at series level when different curves require
  different source inputs.
