# Similarity Scorecard

## Case Score

- Overall score: **73.61/100**
- Similarity level: `numerical_feature_reproduction`
- Meaning: central analytic dynamics and disclosed tables reproduce quantitatively; source-constrained and proxy-model targets capture the paper feature without claiming author-run identity.

The score evaluates numerical content rather than color, line width, marker, layout, or camera choice.

This is a historical evidence score, not a live execution gate. The current
derivation-first readiness matrix is:

- guarded final runs passed: Fig. 2, Table S1, Table S2, and Table S7
  (internal targets T001, T004, T005, and T009);
- exploratory-only: T002, T007, T008, T011-T014;
- blocked: T003 and T010 because EQC010 remains source-only.

## Pixel Gate

- Exact source canvas size: **8/8**
- Best full-image SSIM: **0.8297** (T012)
- Mean full-image SSIM: **0.7524**
- Strict `SSIM >= 0.95`: **0/8**
- Historical layout-contract evidence: **3/3 passed** for T001, T003, and T007
- Active layout targets after migration: **2/2 passed** for T001 and T007

This presentation gate is reported separately and does not increase the 73.61 scientific score. T003's earlier layout result is retained as historical evidence but cannot authorize a new run. The other rendered figures remain outside the active pixel frontier because their formula/provenance gates are reconstructed, source-only, closed, or proxy-model constrained.

## Target Scores

| Target | Weight | Score | Historical artifact stage | Parameter match | Interpretation |
| --- | ---: | ---: | --- | --- | --- |
| T001 Fig. 2 | 3.0 | 80 | final_reproduction | paper_exact | exact closure/CZ dynamics; source data points unavailable |
| T002 Fig. 3 | 1.5 | 50 | exploratory | unknown | duration surrogate matches endpoints; schedules absent |
| T003 Fig. 4 | 1.5 | 76 | exploratory | paper_subset | 2 mm timing crossover; panel-b source inconsistency |
| T004 Table S1 | 0.7 | 99 | final_reproduction | paper_exact | operating point agrees after paper rounding |
| T005 Table S2 | 0.7 | 100 | final_reproduction | paper_exact | decay conversion exact |
| T007 Fig. S1 | 1.3 | 80 | exploratory | paper_subset | exact modes and independent 25-segment closure |
| T008 Fig. S3 | 1.0 | 55 | exploratory | proxy_model | thermal trend and `η²` scaling only |
| T009 Table S7 | 0.5 | 100 | final_reproduction | paper_exact | gate accounting exact |
| T010 Fig. S5 | 0.9 | 55 | blocked review evidence | paper_exact inputs | printed Fowler law misses Table S11 by roughly 2–8×; scientific evidence ineligible pending clarification |
| T011 Table S13 | 0.7 | 89 | exploratory | paper_exact | circular-state formula anchors |
| T012 Fig. S6 | 0.8 | 55 | exploratory | proxy_model | unitary trajectory plus disclosed decay approximation |
| T013 Fig. S7 | 0.8 | 55 | exploratory | proxy_model | thermal ordering and floors only |
| T014 Table S14 | 0.6 | 89 | exploratory | paper_exact | disclosed error-budget arithmetic |

## What Prevents A Higher Score

The limiting evidence is scientific input, not plotting fidelity: no raw author curves, no exact multi-ion toggle schedule, no MQDT state-tracking dataset, no qLDPC simulator/decoder configuration, and no full open-system notebook. T003 also cannot be awarded source-raster agreement because its panel-b raster contradicts the caption formula.

The authoritative component-level scientific scores and caps are in `outputs/checks/similarity_scorecard.json`; pixel metrics are in `outputs/checks/pixel_similarity.json` and `outputs/checks/pixel_evidence.json`.
