# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| covered display items | 8 | Figs. 1–5 plus three independently counted Fig. 6 series have generated evidence. |
| supporting checks | 1 group | T007's 11 checks validate the display targets without adding a reproduction item. |
| uncovered theorem families | 2 | T008 and T009 have no independent claim-specific artifacts. |

## Per-target consistency

| Target | Level | Evidence | Remaining difference |
| --- | --- | --- | --- |
| T001 | feature match, paper parameters | q bands, trace, symmetries, 92.28 pixels | no author pointwise array for direct numeric comparison |
| T002 | feature match, paper parameters | all printed families, 92.96 pixels | original line-connection microstyle only |
| T003 | feature match | exact L2 map, 1162 intervals, 96.16 pixels | author rational cutoff/line density unprinted |
| T004 | feature match | exact C2 map, 513 intervals, 97.17 pixels | author rational cutoff/line density unprinted |
| T005 | feature match | delta-alpha=0.01, band bound, 81.35 pixels | author rational cutoff/raster unprinted |
| T006 | exact printed anchors + feature match | all three energies/order/residuals, 93.68 pixels | source has no author numeric wave array |
| T007 | supporting checks | 11/11 passed | not counted as a separate reproduction item |
| T008 | uncovered | Section VI claim is registered | independent Cantor/zero-measure artifact missing; code fault unexcluded |
| T009 | uncovered | Section VII claim is registered | independent set/measure convergence artifact missing; code fault unexcluded |

The RenderContract changed only orientation, axes geometry and visible style.
`outputs/checks/render_manifest.json` proves the frozen numerical hashes are
identical before and after rendering.
