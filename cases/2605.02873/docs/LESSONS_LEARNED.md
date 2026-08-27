# Lessons Learned

## Case Summary

- Paper: *Fixed-detector tilt--defocus sensing by upstream source coding in a
  time-reversed Young interferometer*
- Paper ID: `2605.02873`
- Final status: frozen scientific and pixel scopes complete
- Main targets: Fig. 1(a-d) and Supplementary Fig. S1
- Main blockers: none

## What Worked

- Reading the full source bundle before coding exposed the complete target
  inventory, including the visible Fig. 1(d) panel and Supplementary Table S1.
- A single finite-slit Fresnel state object generated the baseline response,
  local scores, optimized codes, coded Fisher matrices, retention values, and
  width scan without local special-case formulas.
- Exact finite-interval Gauss--Legendre integration made convergence cheap and
  avoided arbitrary aperture truncation.
- Analytic checks were stronger than image comparison: finite differences
  validated the score derivatives, noise-metric orthogonality validated the
  code construction, and paper-text matrices validated the downstream Fisher
  calculation.
- Scientific gates were completed before pixel tuning. SHA-256 equality of all
  five CSVs proved that layout repair did not change generated data.

## What Was Difficult

- Non-nested source grids created a small interpolation floor even when the
  underlying Fisher matrices agreed at \(10^{-6}\) relative scale. A convergence
  threshold must reflect what its interpolation metric actually measures.
- A pure relative tolerance misclassified the rounded near-null first row of
  Table S1. The disclosed hybrid absolute-plus-relative tolerance preserved the
  mismatch while avoiding a false failure.
- Matplotlib floored a nominal 4.81-inch, 100-dpi canvas to 480 rather than 481
  pixels on this platform. A 0.0001-inch guard restored deterministic crop
  dimensions.
- Pixel overlap was initially dominated by outer margins, title placement, and
  font size rather than curve geometry.
- The Fig. 1(d) raster and paper text contain a small numerical inconsistency in
  the second toy retention value.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Separate scientific and pixel lanes | a visually close curve can still use the wrong model, and a correct curve can be unregistered | gate rendering repair on passed scientific evidence |
| Treat near-zero references with hybrid tolerances | relative error is unstable near a physical null | report absolute and relative errors; predeclare an absolute floor |
| Validate derivatives independently | downstream agreement can hide a sign or phase error | compare analytic derivatives with direct finite differences |
| Preserve branch identity explicitly | normalizing or reordering curves can conceal swapped physics | bind every visible series to a stable series ID |
| Hash data across pixel repair | style work must not contaminate numerical evidence | record pre/post hashes for every generated dataset |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Using a convergence threshold without modeling interpolation error | A/B failed although their physical checks were strong | use nested grids or document the interpolation floor |
| Pure relative comparison near zero | S1's first rounded row appeared 2.43% off | use an absolute-plus-relative bound and retain both errors |
| Assuming requested raster size equals saved size | A/C crops differed by one pixel | verify actual PNG dimensions before pixel evidence |
| Optimizing SSIM before registration | early boards mixed curve and layout differences | align canvas/axes first, then interpret SSIM |
| Treating source-panel labels as exact data | Fig. 1(d) raster conflicts slightly with text | prioritize verified equations and textual/tabular references, disclose the raster discrepancy |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Full paper/claim/target map before numerics | every paper reproduction | prevented omission of Fig. 1(d) and S1 |
| Exact finite-domain quadrature | finite apertures or compact supports | stable Fisher values with 192/256 nodes |
| Two-grid convergence plus analytic checks | oscillatory numerical fields | separates sampling effects from model errors |
| Source pixels only on the reference side | every visual comparison | all generated CSVs derive solely from formulas |
| Byte-level integrity check after styling | pixel repair reruns the renderer | all five CSV SHA-256 values remained unchanged |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| `non_nested_grid_interpolation_floor` | Fig. 1(a,b) convergence | compare nested-grid restriction or estimate interpolation order |
| `rounded_near_null_reference` | Table S1 at 20 \(\mu\)m | flag small denominators and require absolute error |
| `nominal_canvas_flooring` | 481-pixel A/C panels | assert saved image dimensions before crop creation |
| `source_text_raster_inconsistency` | Fig. 1(d) second toy bar | compare equations, main text, table, and visible annotation separately |
| `pixel_margin_dominates_overlap` | B/D/S1 initial evidence | inspect axis box, ink margins, and proximity before changing line data |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| generated-data hash guard for pixel repair | enforces separation between science and styling | future harness pixel workflow |
| saved-canvas dimension assertion | catches platform rounding before crop failure | pixel layout crop preflight |
| hybrid near-null tolerance helper | makes absolute/relative policy explicit | numerical evidence utilities |
| source-reference consistency ledger | records disagreement among formula, text, table, and raster | paper-map or evidence schema |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Disposition |
| --- | --- | --- |
| vectorized two-interval Gauss--Legendre field | all targets complete in 0.07--0.22 s | keep case-local |
| shared solved state for panels A-D | avoids recomputing model components inside each panel handler | keep case-local |
| small 2-by-2 whitened eigensystem | direct, auditable retention calculation | keep case-local |

## Harness Backlog Items

The campaign explicitly forbids changes to `PRAgent-workflow` and shared backlog
files. The reusable candidates above are recorded only in this case and were
not promoted during this repeat.

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| high | byte-integrity gate for pixel-only repairs | five unchanged CSV hashes across two repair rounds | case-local candidate |
| medium | automatic nominal-versus-saved canvas check | A/C one-pixel failures | case-local candidate |
| medium | near-null tolerance diagnostic | S1 first row | case-local candidate |

## Prompt Or Workflow Changes

- Make “registration before SSIM” an explicit checkpoint.
- Ask numerical checks to state whether grids are nested.
- Require reports to distinguish source-internal inconsistencies from
  reproduction errors.
