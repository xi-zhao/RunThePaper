# Lessons Learned

1. A proof paper without figures still requires a whole-paper inventory of equations, constructions, numerical examples, and explicitly unresolved claims.
2. Recomputing `C(rho)` from the same eigenspectrum is not an independent convex-roof check. A complete check must construct an attaining ensemble and independently recover its HJW isometry.

## New Failure Modes

- Treating “no figures” as “nothing to reproduce” drops the central scientific result.
- A random optimizer can only supply an upper bound to the convex roof. It cannot replace the positive-branch equal-preconcurrence construction or the zero-branch phase-polygon construction.

## Reusable Checks Or Tools

- `wootters.model.hjw_decomposition` verifies ensemble reconstruction for arbitrary density-matrix rank.
- `wootters.model.concurrence_spectrum` provides a stable Hermitian route that can be cross-checked against the non-Hermitian product spectrum.
- `wootters.model.optimal_decomposition` constructs and verifies both branches of the convex-roof optimum rather than inferring attainability from random search.

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper:
- PaperID:
- Final status:
- Main reproduced targets:
- Main blockers:

## What Worked

- 

## What Was Difficult

- 

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |

## Prompt Or Workflow Changes

-
