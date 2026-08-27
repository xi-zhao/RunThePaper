# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: `Non-Hermitian Chern bands`
- PaperID: `1804.04672`
- Final status: main physics story-line targets are reproduced at
  `numerical_feature_reproduction` / digitized-source-validation level.
- Main reproduced targets: `T001` cylinder spectrum, `T002` cylinder phase
  diagram, `T003` open-boundary phase diagram, `T004` square spectra and
  wave-packet dynamics, `T005` disk finite-size fitting, and `T006` disk phase
  diagram.
- Main blockers: author plotting data, full panel pixel-layout validation, full
  independent square/disk finite-size scans for source-table phase boundaries,
  and blue point-cloud matching.

## What Worked

- Case selection, source ingestion, formula trace, paper-parameter execution,
  marker-only rendering, and conservative scoring are complete for `T001`.
- Separating `edge_localization_candidate` from the paper's red
  `chiral_edge_subset` prevented a physically misleading red-branch claim.
- The accepted red subset follows the analytic chiral edge traces
  `E_+(kx)=sin(kx)+i gamma` and `E_-(kx)=-sin(kx)-i gamma`;
  right-eigenvector edge weight is diagnostic, not the hard gate.
- The source EPS can be parsed directly enough to extract data-axis red/blue
  point references; the filtered EPS red point count is `102`, matching the
  generated red trace count.
- Red-branch point matching is now a hard check: mean distance `0.0098`, max
  distance `0.0263`.
- Fig. 3(a)'s red gapless region is now generated from the analytic open-y
  non-Bloch band-touching boundaries
  `m=1+sqrt(1-2 gamma+2 gamma^2)` and
  `m=1+sqrt(1+2 gamma+2 gamma^2)`, not from source-image fitting.
- The Fig. 3(a) source red curve remains as digitized validation only; its
  current RMSE is `0.0148`.

## What Was Difficult

- Boundary localization alone was not a good enough edge-state classifier:
  `13026` of `14400` spectrum points were labeled as candidates, which is
  consistent with non-Hermitian skin localization contaminating the criterion.
- The original source EPS could not be rasterized directly without
  Ghostscript, but its PostScript drawing commands were still parseable enough
  to extract red/blue point-object references.
- Fig. 3(a) exposed a misleading repair direction: a local source-PDF red-curve
  deviation looked like a numerical error, but the physics check showed the
  generated high-gamma right boundary follows the non-Bloch band-touching
  condition. Low-resolution source digitization must not override the physical
  boundary definition.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Boundary-localized does not automatically mean topological edge branch | Non-Hermitian systems can localize bulk states through the skin effect, so a naive edge-weight threshold can color the wrong physics | Require a declared edge-branch classifier that separates skin-localized bulk states from chiral edge states before red styling or line connection |
| Analytic edge traces are better than boundary-weight coloring | The paper's red branch follows `E_+(kx)=sin(kx)+i gamma` and `E_-(kx)=-sin(kx)-i gamma`, while boundary weight overlabels skin-localized bulk states | Trace the analytic edge branch first, keep non-Bloch bulk distance and edge weight as diagnostics, then validate against source EPS points |
| EPS source paths can become a validation reference even when rasterization fails | `energy.eps` could not be rendered by ImageMagick without Ghostscript, but the CMYK point objects were parseable | Add a lightweight source-path extraction step before giving up on pixel/source validation |
| Physical boundary definition beats local source-pixel fitting | Fig. 3(a)'s right red boundary at high gamma follows the analytic non-Bloch band-touching value even when low-resolution source digitization locally differs | For phase diagrams, derive the physical boundary first, then use digitized source curves only as validation evidence |
| Case learning needs a generated digest | The case accumulated lessons across T001-T006, but the early `LESSONS_LEARNED.md` lagged behind later repair passes | Generate `CASE_LEARNING_DIGEST.md/json` after each paper so the next paper starts from absorbed experience |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Edge-weight classifier overclaims chiral branches | The first render labeled most points as `edge_localization_candidate` | Keep the candidate label diagnostic; require spectral/topological criteria before `chiral_edge_subset` |
| Source-pixel local deviation can overrule physics if used too early | Fig. 3(a) source-PDF digitization under-read the high-gamma right boundary locally | Treat source digitization as validation after formula/model gates, not as the primary physical definition |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Render marker-only when the caption says all `k_x` spectra are shown together without specifying `k_x` | Complex spectra or unordered eigenvalue clouds | `first_target.png` has zero line segments, avoiding the earlier failure mode of connecting unrelated band-index rows |
| Score conservatively when a partial pointwise gate passes | The red branch now passes EPS point matching, but blue point-cloud distance and pixel layout are not enforced | `similarity_scorecard.json` uses `digitized_curve`, keeps `T001` at `84.0`, and records the remaining blue-cloud/pixel gate |
| Generate a case learning digest after every substantial repair loop | Multi-target cases can accumulate lessons faster than the human-maintained lessons file | `CASE_LEARNING_DIGEST.md/json` now extracts reusable lessons and promotion candidates from project state, scorecard, repair work items, and `LESSONS_LEARNED.md` |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `partial_target_coverage` | `T001`, Fig. 3(b) cylinder spectrum | If only the red branch has pointwise EPS validation and blue-cloud/pixel-layout gates are missing, cap the score below complete reproduction |
| `source_pixel_overfit_risk` | `T002`, Fig. 3(a) cylinder phase boundary | If a digitized source curve conflicts locally with an analytic/non-Bloch boundary, classify the discrepancy before changing the model. |
| `physical_boundary_proxy_threshold` | `T002`, Fig. 3(a) cylinder phase boundary | Avoid finite-grid proxy thresholds when the paper model provides a traceable band-touching boundary. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Edge-branch classifier contract | Many topological spectra need to separate physical edge modes from bulk/skin modes before styling | `PRAgent-workflow/rr_harness/target_contract.py` or repair planner extension |
| EPS point-object extraction | Some arXiv source figures preserve colored marker objects even when original plotting data is unavailable | `PRAgent-workflow/rr_harness/source_reference.py` or a case-to-generic extraction helper |
| Analytic phase-boundary checker | Phase diagrams often have source images with low-resolution local distortions but formula-derived boundaries | case-local physics module first; promote generic phase-boundary contract if repeated |
| Case learning digest | Every multi-target paper should leave machine-readable learning output for the next paper | `PRAgent-workflow/rr_harness/case_learning_digest.py` |

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
| high | Add edge-state/branch classifier contract and repair-planner rule for red-branch identity failures | `1804.04672` `T001` boundary localization labeled `13026/14400` points, while the accepted analytic red trace contains `102` points | copied_to_backlog |

## Prompt Or Workflow Changes

- None yet.
