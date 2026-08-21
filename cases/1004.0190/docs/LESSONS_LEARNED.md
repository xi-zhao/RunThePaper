# Lessons Learned

1. A geometric “illustration” can encode a fully quantitative scientific region and belongs in scope when every vertex and boundary follows from equations.
2. Substitution into the paper's own closed form is a strong first falsification path, but a global constrained optimization is still needed to distinguish an arithmetic typo from a wrong maximizer.

## New Failure Modes

- Blindly treating the caption/text value as the acceptance oracle would force correct code to reproduce `1/6`, contradicting the printed formula.
- Counting roundoff-null Schmidt directions creates arbitrary noncommuting operators, while diagonalizing a Gram matrix can erase small physical directions by squaring the condition number. Apply the declared rank threshold directly to coefficient-map singular values.

## Reusable Checks Or Tools

- `geometric_discord_direct` independently minimizes the measurement-induced Hilbert-Schmidt distance.
- `operator_schmidt_commutator_norm` implements the zero-discord witness for any `2 x d` state.

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
