# Lessons Learned

## Case Summary

- Paper: *Information and Majorization Theory for Fermionic Phase-Space Distributions*.
- Paper ID: `2401.08523`.
- Final status: `complete_reproduction`.
- Reproduced: both main figures and all four numerical panels.
- Blockers: none.

## Generalized Experience

| Lesson | Why it matters | Future rule |
| --- | --- | --- |
| Audit the whole figure inventory before scaffolding | A tiny benchmark question can hide a large full-paper workload | Count all main/supplement numerical panels and estimate their real solver scale first. |
| One deep domain model beats per-figure scripts | Here one occupation variable supports every claim and plot | Identify shared scientific state and transformations before writing renderers. |
| Preserve Grassmann semantics | Replacing the soul with an ordinary float would be conceptually wrong | Store only numerical bodies and keep nilpotent algebra in the derivation gate. |
| Pixel evidence belongs after science | Styling can be tuned safely only after formulas and provenance pass | Isolate reference-reading code in a terminal evaluator. |
| Image-threshold metrics are color-sensitive | A two-level background RGB difference doubled perceived ink density | Match declared background style or calibrate the metric before changing curves. |

## Efficient Implementation

| Choice | Evidence | Scope |
| --- | --- | --- |
| vectorized closed forms | complete run in `0.554 s` | case-local scientific module |
| common renderer for all panels | exact canvas and consistent semantics | case-local |
| reusable Harness comparison board | SSIM and absolute difference with no source-to-generation path | already shared |

## Risks Avoided

- No source curve digitization or copied pixels.
- No artificial numerical figure for Appendix A, which has only analytic logic.
- No reduced target scope: the supplement was checked and contains no figures.
- No unnecessary dependency, GPU, remote service, or autonomous long loop.

## New Failure Modes

| Failure mode | Evidence in this case | Detection |
| --- | --- | --- |
| Full-paper scale hidden behind a tiny benchmark task | the previously audited candidate had dozens of panels despite a cheap benchmark | inventory every main/supplement panel and largest solver object before scaffolding |
| Background colors distort threshold-based pixel density | one RGB-level change moved line-density ratio from about 1.7-1.9 to 0.94-1.00 | compare blank-region style and report raw density before touching scientific curves |
| Grassmann soul flattened into ordinary numeric data | possible when implementing only plotted bodies | require derivation cards to state what remains symbolic and why |

## Reusable Checks Or Tools

| Candidate | Why reusable | Destination |
| --- | --- | --- |
| full-paper resource preflight | prevents late discovery of an oversized supplement or solver | `PRAgent-workflow/HARNESS_BACKLOG.md` |
| source/generation import-boundary assertion | makes the no-pixel-input claim mechanically auditable | future Harness provenance checker |
| existing pixel-layout + comparison board | exposed presentation differences without contaminating numerics | already in `rr_harness` |

## Possible Harness Improvement

A candidate-selection resource gate should record total numerical panel count,
largest scientific object, and estimated full-paper runtime before a case is
created. This case validates that gate; no shared Harness code was changed in
this commit.
