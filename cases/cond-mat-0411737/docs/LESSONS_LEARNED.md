# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: *Quantum Spin Hall Effect in Graphene*.
- PaperID: `cond-mat-0411737`.
- Final status: numerical feature reproduction; authoritative review pending.
- Main reproduced targets: T001, complete Main Fig. 1 band axes; all remaining
  quantitative claims checked analytically.
- Main blockers: the publication omits Fig. 1 strip width/grid; fresh-context
  independent review is missing.

## What Worked

- A geometric clean-room ribbon construction reproduced the topological edge
  crossing without author code, arrays or digitized curves.
- Symmetry, topology, continuum and material-scale checks made code-fault
  attribution substantially stronger than visual comparison alone.
- Separating the numerical runner from rendering produced a clean attestation
  without relaxing process isolation.

## What Was Difficult

- A visually plausible honeycomb cut can actually be a bearded edge; site
  coordination and the flat-band momentum interval must be tested.
- The paper's missing strip width affects branch density even though the
  central topology is width-stable.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Keep Matplotlib out of the scientific runner | Font discovery may spawn processes and weaken/violate isolation | Freeze arrays first; render in a separate hashed channel |
| Test boundary topology, not only Hermiticity | A wrong edge termination can still yield a valid Hermitian matrix | Assert coordination and a known edge-state landmark |
| Distinguish science from finite-size presentation | Missing width changes branch count but not the QSH invariant | Report exact affected scope and use width convergence |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Wrong honeycomb termination | Same-row A/B retention produced a bearded edge | Encode edge coordination and Kramers-crossing tests before full runs |
| Renderer inside sandbox | Matplotlib attempted two `fc-list` child processes | Make RenderContract a separate post-freeze entrypoint |
| Treating absent width as paper exact | Foreground line density differs although science passes | Use `paper_subset` and a publication-underspecified causal diagnosis |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Hash scientific data before opening source figures | Every figure reproduction | Band CSV remained `6fd0f561...fed293` before/after rendering and comparison |
| Use symmetry-unique scientific crops | Source contains an inset over a duplicated symmetric region | Left-half score 91.19; full canvas remains diagnostic only |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Benign library subprocess attempts | v1 isolated run, Matplotlib font scan | Fail closed on every subprocess and record the denied events |
| Manuscript cross-reference drift | Three equation numbers | Fresh-context reviewer should check prose/equation bidirectional consistency |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Frozen-data RenderContract guard | Proves plotting cannot alter numeric arrays | Harness rendering contract |
| Boundary-coordination invariant | Catches geometrically wrong but Hermitian lattice cuts | Case method-test pattern |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Reused geometry plus conserved-spin blocks | 32,080 rows and three widths in 0.554 s | Keep lattice kernel case-local |
| Separate rendering/comparison channel | clean v2 attestation, zero forbidden access | Promote workflow pattern |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P1 | Formalize numeric-run/render-run separation as a Harness contract field | v1 failed only because Matplotlib probed fonts; v2 passed unchanged science | proposed |

## Prompt Or Workflow Changes

- Always classify missing publication metadata at the exact affected target
  scope; do not report a generic “not paper exact” label.
