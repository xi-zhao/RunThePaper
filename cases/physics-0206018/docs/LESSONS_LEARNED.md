# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: Boundary element method for resonances in dielectric microcavities
- PaperID: physics-0206018
- Final status: feature_reproduced
- Main reproduced targets: Figs. 5-7
- Main blockers: publication prose and Fig. 4 disagree on the displacement
  sign; fresh review remains missing

## What Worked

- The exterior double-layer jump sign was fixed by an analytic circular-cavity
  benchmark before the coupled-cavity run.
- One frozen boundary null vector can drive both near- and far-field panels.

## What Was Difficult

- The trace-Newton determinant update can jump between nearby resonances on a
  reduced/changed geometry; smallest-singular-value mesh convergence is the
  safer falsification check.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Validate BIE signs on a separable shape | A sign error still produces smooth, plausible pictures | Require a circle/sphere benchmark before opening geometry targets |
| Distinguish omitted implementation freedom from contradictory physics input | A paper may declare many meshes equivalent yet still contradict itself on geometry | Model the equivalence class separately; record the source conflict and forbid paper-exact promotion |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Under-resolved optical theorem | Coarse meshes gave correct-looking spectra but poor flux balance | Record both `b` and optical-theorem residual |
| Prose/figure sign conflict | Literal `+0.5R` geometry changed the Fig. 5 cross section qualitatively, while Fig. 4 and the historical feature run use `-0.5R` | Audit text, schematic axes, and numerical figures together before a long production run |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Shared immutable state | Multiple figures derive from one eigenmode | Figs. 6-7 use the same hashed boundary vector |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Newton pole hopping | Resonance refinement at reduced mesh | Compare singular value, seed neighborhood, and mesh continuation |
| Publication parameter contradiction | Example prose versus Fig. 4 displacement direction | Keep the case below unqualified paper-exact and submit the contradiction to fresh review |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| BIE analytic-shape gate | Detects orientation/jump mistakes before expensive runs | harness scientific-check pattern |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Vectorized Hankel quadrature | 73 points plus fields completed in 159 s | keep case-local until a second BEM case appears |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P2 | Add flux/optical-theorem check type | It exposed under-resolution independently of pixel appearance | proposed |

## Prompt Or Workflow Changes

- Open formula gate, validate on separable geometry, run isolated numerics,
  freeze arrays, then open the RenderContract comparison channel.
