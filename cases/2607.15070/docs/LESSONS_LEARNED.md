# Lessons Learned

## Case Summary

- PaperID: `2607.15070`
- Final status: complete scientific and pixel reproduction
- Targets: T001 (Figure 2a,b), T002 (Figure 3)
- Blockers: none

## What Worked

- Closing formula and method gates before execution exposed four inconsistent
  printed substeps without contaminating the numerical path.
- Positive Bessel series made paper-scale execution fast and stable.
- Original proper-time quadrature gave a structurally independent numeric
  check.
- Data-first target runners prevented failed assertions from producing
  apparently final figures.

## What Was Difficult

- A first convergence threshold compared cutoffs that were too close to the
  production truncation error; tightening both cutoffs resolved the false
  negative without changing the model.
- Matplotlib's direct PNG rasterizer produced a different ink density from the
  source's PDF rasterization. Rendering generated PDFs through Poppler aligned
  the pixel-evidence measurement path.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Re-derive from the earliest trustworthy formula | Later paper asymptotics may contain transcription errors | Quarantine inconsistent substeps and verify against the original integral |
| Use independent representations | A transformed series cannot validate itself | Pair fast production formulas with sparse direct integration |
| Match rasterization paths for pixel QA | Renderer differences can mimic style mismatch | Compare source and generated vector figures through one rasterizer |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | Prevention |
| --- | --- | --- |
| Treating the printed small-coupling formula as trusted | Eq. (42) repeats `K_2` where direct expansion yields `K_3` | Track powers of proper time before applying the Bessel identity |
| Overly strict tail test at an insufficient reference cutoff | Initial T001 scientific check failed | Compare production and a meaningfully tighter cutoff |
| Comparing PDF-derived source ink with Agg PNG ink | Three density contracts initially failed | Rasterize both sides through Poppler |

## Recommended Practices

| Practice | When to use it | Evidence |
| --- | --- | --- |
| Target-scoped environment guard | Every numerical runner and test | T001 and T002 reject the wrong target/stage |
| Analytic endpoint checks | Singular or limiting plots | Zero coupling, correction divergence, and ratio-to-one all pass |
| Separate scientific and pixel scores | Any figure reproduction | Scientific 90.0 and pixel 82.56 remain independently interpretable |

## New Failure Modes

| Failure mode | Detection | Repair |
| --- | --- | --- |
| Scientific false negative from weak reference cutoff | Production/reference delta exceeds tolerance while direct quadrature agrees | Tighten the reference cutoff and keep the physics threshold explicit |
| Cross-rasterizer pixel-density bias | Bounding boxes align but ink-density ratios fail together | Standardize the vector-to-raster path |

## Reusable Checks Or Tools

| Candidate | Value | Destination |
| --- | --- | --- |
| Same-rasterizer pixel preflight | Separates renderer bias from layout/style defects | Future harness backlog after the frozen Trial |
| Formula-power audit before Bessel conversion | Detects wrong Bessel order | Reproduction-method checklist |

## Efficient Reproduction Implementations

| Implementation | Evidence | Scope |
| --- | --- | --- |
| Positive Bessel-argument truncation | Full targets finish in 0.815 s and 0.528 s | Keep case-local |
| Log-proper-time quadrature checkpoints | Agreement below `4e-13` | Keep case-local |

## Harness Backlog Items

No harness file was modified because this controlled Trial freezes the Harness.
The two reusable candidates above are recorded here for later triage;
`copied_to_backlog: no (frozen-harness boundary)`.

## Prompt Or Workflow Changes

Keep the current order: paper map, formula gate, method gate, target
authorization, independent data, scientific assertions, rendering, then pixel
evidence.
