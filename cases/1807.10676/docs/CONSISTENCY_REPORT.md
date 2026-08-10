# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| physically_consistent | 12 composite targets / 42 subpanels | Formula-derived data pass the declared scientific gates |
| deferred_blocked / code_ready_external_required | 12 DFT entries | Shared implementation, decks, run contract, and acceptance exist; licensed high-memory VASP campaign not run |
| excluded_non_numeric | 10 grouped items | Schematics or analytic lookup/proof tables |

## Per-target result

| Target | Scientific result | Status | Remaining difference |
| --- | --- | --- | --- |
| T001 | Six reported alphas give near-zero velocity; phase-gap intervals recovered | passed | finite alpha/gap grids |
| T002 | A-D Wilson spectra have odd winding | passed | reduced loop grid and layout |
| T003 | Printed TB4 dispersion and flat separated branches | passed | no author array for pointwise numeric comparison |
| T004 | Lower TB4 branch has winding Wilson spectrum | passed | finite loop grid |
| T005 | Gamma/M/K level crossings follow the supplement sequence | passed | finite alpha grid |
| T006 | All nine reported-alpha continuum band panels | passed | reduced path sampling |
| T007 | First-magic-angle Gamma crossing pattern | passed | finite alpha grid |
| T008 | Six bands plus node creation/motion/vorticity maps | passed | reduced initial node-search grid |
| T009 | Eight PH-breaking panels from four printed parameter pairs | passed_with_note | one source angle-label discrepancy |
| T010 | Four supplementary Wilson panels | passed | reduced loop grid |
| T011 | Intervalley-gapped TB8 bands and trivialized lower-four Wilson spectrum | passed | finite grids |
| T012 | Localized projected Wannier density and tuned TB4-2V bands | passed | finite k/real-space grids |

The primary post-freeze scientific-region pixel mean is `43.281/100`; the full-canvas diagnostic mean is `91.9916/100`. The foreground metric is sensitive to line sampling and multi-panel registration, while the scientific gates above operate on generated values and topology.
