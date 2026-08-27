# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: *Topological Band Theory for Non-Hermitian Hamiltonians*
- PaperID: `1706.07435`
- Final status: six claims verified; six targets and 15/15 theory-numerical
  panel items reproduced.
- Main reproduced targets: continuum bulk/edge spectra, exceptional-point
  sheets and winding, phase transition, domain-wall surface, cylinder bands,
  and hybrid-point anisotropy.
- Main blockers: none scientific; presentation fidelity remains `60.28/100`.

## What Worked

- Freezing the complete figure/claim scope before execution prevented the easy
  exceptional-point panel from being mistaken for a full-paper reproduction.
- Reducing domain-wall matching to sum/difference equations produced a stable,
  branch-explicit solution and made nonlinear roots an independent check rather
  than the primary generator.
- Scientific arrays were written and validated before any original Figure was
  rendered into the comparison directory.

## What Was Difficult

- The paper prints matching equations but not its solver or continuation rule;
  the missing method had to be reconstructed from the common-spinor invariant.
- A raw sampled distance threshold produced small disconnected holes near a
  bulk-gap boundary. Selecting the connected physical component around the
  maximum gap was more faithful than weakening the physics criterion globally.
- Whole-figure raster scores are dominated by aspect ratio, 3D camera, and
  typography even when the numerical surfaces agree at machine precision.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Solve interface states from shared-eigenspace invariants before invoking generic roots. | Common-spinor or transfer-matrix problems often contain algebraic structure hidden by the paper's nonlinear presentation. | Derive determinant sum/difference relations, then use nonlinear roots only as an independent spot check. |
| Freeze scientific data before opening pixel evidence. | It makes source-pixel leakage mechanically auditable. | Runners must not import, read, or depend on `internal-paper-reference/`; compare only after run artifacts exist. |
| Treat raster similarity and scientific fidelity as separate scores. | 3D camera and font drift can lower pixel overlap without changing the physical result. | Report both scores and optimize render-only parameters after science passes. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Stopping after the easiest Figure | Main Fig. 2 was CPU-fast and initially looked like a plausible baseline. | Enforce 15/15 panel coverage from the frozen full-paper inventory before declaring completion. |
| Using a generic eigensolver at an exactly defective point as the only test | Numerical eigenvalues near the hybrid origin showed conditioning-scale noise. | Pair direct eigensolver checks with exact rank and nilpotency invariants. |
| Applying a pointwise visibility threshold to a sampled continuum | Boundary sampling holes broke an otherwise physical edge segment. | Select the connected component anchored at the maximum bulk-gap distance and retain the original threshold. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Paper-equation result plus independent implementation check | Closed-form two-level spectra or interface formulas | Analytic/direct errors range from `1e-16` to `1e-14`; Supplement Fig. 2 also passes nonlinear roots. |
| Boundary weights for open-system band classification | Cylinder or ribbon spectra | Both chiral branches have matched boundary weight above `0.985`. |
| Directional exponent fits | Anisotropic exceptional or hybrid degeneracies | Supplement Fig. 4 recovers exponents `0.5` and `1.0`. |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Full-paper scope silently collapses to one attractive Figure | Early T002-only state | Require every scoped numeric panel to map to a reproduced or explicitly blocked target. |
| Defective-point eigensolver noise is misread as a physics failure | T006 origin | Require exact nilpotency/rank checks alongside generic diagonalization. |
| Whole-image pixel score hides which panel/layout feature is wrong | Six-figure V0 pixel audit | Emit per-panel crops and structure-aware camera/layout diagnostics before any tuning. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Common-spinor domain-wall solver contract | Applies to two-band Dirac interfaces with complex parameters. | Harness method-card example and optional scientific helper. |
| Three-way original/reproduction/difference board | Makes post-generation pixel evidence inspectable without opening machine JSON. | `build_pixel_evidence.py` presentation output. |
| Connected physical-component selector | Preserves sampled continuum branches without relaxing global tolerances. | Numerical-geometry utility with anchor and threshold evidence. |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Algebraic domain-wall matching | Main Fig. 1 executes in `0.455 s`; the 121×121 Supplement surface executes in `0.157 s`. | Promote the invariant/check pattern; keep paper conventions case-local. |
| Vectorized analytic 2×2 spectra | T002/T003/T006 each execute below `0.41 s`. | Promote sheet tracking and direct-eigenvalue unordered-pair checks. |
| Dense paper-exact cylinder diagonalization | 482 full `80×80` eigensystems execute in `3.91 s`. | Keep simple dense baseline; add sparse mode only for larger systems. |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P1 | Build labelled three-way pixel boards and per-panel scores directly from pixel evidence, without relying on host ImageMagick fonts. | All six comparisons were generated, but labels had to remain in Markdown because the local ImageMagick font registry was empty. | copied to `PRAgent-workflow/HARNESS_BACKLOG.md` |
| P1 | Add a structure-aware 3D presentation diagnostic for aspect ratio, camera, and mesh density. | Scientific residuals are machine-precision while whole-image presentation mean is only `60.28`. | copied to `PRAgent-workflow/HARNESS_BACKLOG.md` |

## Prompt Or Workflow Changes

- Completion language must name both claim coverage and numerical panel
  coverage; one reproduced Figure is never a proxy for full-paper completion.
- Original figures may be rendered only after the target runner has produced
  structured arrays and passed scientific checks.
