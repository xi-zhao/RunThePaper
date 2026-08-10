# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: Exact Spectral Form Factor in a Minimal Model of Many-Body Quantum Chaos
- PaperID: `1805.00931`
- Final status: partial scientific reproduction; numerical feature reproduction
- Main reproduced targets: all numerical regions T001--T005; T005 paper-exact
- Main blockers: Figure 2 ensemble/Hilbert scale, Figure 3 `4^t` scale, fresh review

## What Worked

- A single exact eigendecomposition produces the complete SFF time series.
- Formula-derived protected-sector deflation makes the desired transfer eigenvalue observable.
- Frozen hashes cleanly separate numerics from render and source-comparison channels.

## What Was Difficult

- Transfer Arnoldi cost varies sharply near weak disorder because of clustered roots.
- An apparently cheap analytic curve hid an `O(t^4)` per-point recomputation.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Profile analytic/reference curves too | A helper can dominate a supposedly heavy simulation | Time each target component before scaling hardware. |
| Separate scale from formula validity | Correct formulas do not imply paper-exact output | Encode parameter match per target and cap scores. |
| Compare pixels only after freeze | Styling evidence must not feed scientific arrays | Hash data before and after every render/comparison script. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Recomputing combinatorial structure | Dihedral ranks were rebuilt for all 1000 times | Use closed forms for long curves; reserve constructive checks for a bounded audit range. |
| Conventional Arnoldi at large `t` | Krylov vectors scale as `4^t` | Use a memory-bounded block/power design before moving to A100. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Retain failed attestations | A timeout or rejection contains useful audit evidence | v1/v2 prove no outputs were accepted before v3. |
| Scientific crop pixel metric | Parameter-aware visual comparison | Foreground scores expose real curve mismatch despite high background-dominated SSIM. |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Reference-helper complexity explosion | thermodynamic SFF curve | Add a long-range runtime regression test. |
| Background-dominated pixel score | full Figure 2/3 SSIM | Report foreground scientific-region metric as primary and full SSIM as diagnostic. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Frozen-data render hash check | Prevents scientific values changing during styling | generic RenderContract helper |
| Per-section isolated timing | Locates non-obvious bottlenecks | isolated-run manifest |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Closed-form long-time multiplicity curve | reduced >900 s timeout to negligible helper cost | case-local physics; generic performance lesson |
| Matrix-free local butterflies | reaches `t=9` without dense `4^t x 4^t` matrix | case-local operator pattern |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P2 | Add analytic-helper profiling guidance | two 900 s timeouts from a reference helper | candidate |

## Prompt Or Workflow Changes

- Require per-component timing before selecting local CPU versus A100.
- Preserve reduced-scale status even when render geometry and scientific crop comparison pass.
