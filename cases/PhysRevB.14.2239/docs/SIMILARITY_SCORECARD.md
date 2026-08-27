# Similarity Scorecard

- Overall scientific evidence score: **89.57/100**.
- Atomic item coverage: **8/10 = 80.00%**.
- Covered-item fidelity: **89.62/100**.
- Paper reproduction degree: **71.70/100**; uncovered items score zero.
- Primary complete-scientific-region pixel mean: **92.27/100**.
- Pixel range: **81.35–97.17**; all six regions pass `>=80`.
- Similarity level: `numerical_feature_reproduction`.

| Target | Pixel/claim metric | Evidence cap | Final target score |
| --- | ---: | ---: | ---: |
| T001 | 92.2840 | 90 analytic-reference | 90 |
| T002 | 92.9607 | 90 analytic-reference | 90 |
| T003 | 96.1605 | 89 paper-subset | 89 |
| T004 | 97.1696 | 89 paper-subset | 89 |
| T005 | 81.3544 | 89 paper-subset | 89 |
| T006 | 93.6773 | 90 analytic-reference | 90 |
| T007 | 100% supporting assertions | 90 analytic-reference | 90; denominator helper only |
| T008 | no independent Cantor-spectrum artifact | uncovered | 0 |
| T009 | no independent continuity artifact | uncovered | 0 |

Pixel difference is the primary render comparison, but it cannot erase
provenance. T003–T005 stop at 89 because the author did not publish the plotting
sample density. The other targets stop at the analytic-reference cap of 90
until fresh independent review. Machine-readable schema-v4 details and causal
diagnoses are in `outputs/checks/similarity_scorecard.json`.

The 89.57 score is the historical weighted target score over T001-T007. The
public paper-level metric is the atomic reproduction degree, which does not
double-count T007 and assigns zero to the two newly exposed claims.
