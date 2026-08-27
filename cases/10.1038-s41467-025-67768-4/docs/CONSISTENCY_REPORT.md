# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| paper_exact | 1 | Supplementary Fig. 9 follows the cited analytic fit at paper parameters. |
| feature_match | 4 | T002-T005 reproduce the intended mechanism/trend with missing calibration details. |
| table_exact_with_caveat | 1 | T007 reproduces the table but falsifies the exact invariant. |
| source_discrepancy | 1 | T001's independently checked literal model disagrees with the paper curve and awaits fresh review. |
| uncovered_numeric | 2 targets / 3 items | qLDPC and lattice-surgery targets lack executable definitions. |

## Per-Target Consistency

| Target | Paper item | Level | What agrees | What differs / likely reason |
| --- | --- | --- | --- | --- |
| T001 | Main Fig. 2(c) | source_discrepancy | exact feedback formula, low-r ordering, correction benefit | high-r sign change absent from source; actual amplification convention undisclosed |
| T002 | Main Fig. 3(c), Supp. Fig. 4 | feature_match | distance ordering and uncorrected overlap | endpoint offsets from missing per-gate/readout calibration |
| T003 | Main Fig. 3(e) | feature_match | M ordering and smooth decline | M=2-4 too optimistic under aggregate proxy |
| T004 | Main Fig. 4(b,c), Supp. Fig. 7(a,c,e) | feature_match | code algebra, Bloch contraction, r=1 anchors | high-r decay depends on unstated surface injection rate |
| T005 | Supp. Fig. 8 | feature_match | complete-ZNE advantage and distance ordering | suppression 4.11-5.07 vs paper 3.2-4.1; aggregate model too optimistic |
| T006 | Supp. Fig. 9 | paper_exact | both panels, three distances, two budgets, exact d=11 anchor | remaining SSIM loss is rendering/finite-fit presentation |
| T007 | Supp. Table 3 | table_exact_with_caveat | all printed values | exact schedule is 13.600, 9.286, 7.048, 5.680%; paper values have 1.9005% relative cumulative spread |
| T008 | Supp. Fig. 2 | uncovered | item is explicitly inventoried; paper identifies the code and physical error rate | 0/1 covered: circuit/noise process, decoder configuration, and trial contract are unpublished; code fault not applicable |
| T009 | Supp. Fig. 10(b,c) | uncovered | both panels are separately inventoried; ZNE formulas are known | 0/2 covered: exact schedule, syndrome rounds, decoder, and sampling contract are unpublished; code fault not applicable |

## Coverage boundary

The eligible denominator is 16 atomic scientific numerical items. Thirteen
have accepted evidence; the three T008/T009 items above do not. All 31
schematic, experimental, hardware, and acquisition-context items remain in the
inventory as explicit exclusions and therefore do not silently inflate or
depress the 81.25% scientific-numerical coverage.

## Cross-Checks

- Feedback closed form vs exhaustive `4^3` Pauli patterns: maximum error
  approximately `2e-15`.
- Surface code: X/Z stabilizer ranks 4/4, logical anticommutation true,
  distance 3, zero decoder failures, channel normalization error
  `2.22e-16`.
- Bloch-circle radius identities: errors below `1.7e-16`.
- Logical-memory anchor: `2.0337517782742424e-10` at `p=1e-3,d=11`.
- ZNE moment residual: below `1.2e-13`.

## Pixel Evidence

Registered pixel comparison is meaningful only for pure numerical assets:

| Item | SSIM | Interpretation |
| --- | ---: | --- |
| Supp. Fig. 8 | 0.6695 | same structure; calibration-dependent positions differ |
| Supp. Fig. 9 | 0.7005 | strong layout and feature agreement |
| Supp. Table 3 | 0.4764 | values exact; font rasterization dominates difference |

Mixed experimental/simulation panels use labelled two-panel comparisons and
explicit `pixel_status=not_applicable`; experimental markers are never
regenerated from paper pixels.
