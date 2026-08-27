# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 2 | Every tabulated paper value matches exactly. |
| feature_match | 2 | Independent numerics reproduce the paper feature and analytic checks. |
| partial_match | 0 | No numerical target is partial. |
| input_match_only | 0 | No target stops at parameter agreement. |
| blocked | 0 | No numerical target is blocked. |
| not_in_scope | 6 | Figures 1 and 3–7 are non-numerical schematics. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Remaining difference |
| --- | --- | --- | --- | --- |
| `T_FIG2` | Figure 2 A–F | feature_match | 7/7 checks; six panels; slope agreement | No author plotting data; analytic-reference cap is 90. |
| `T_TABLE1` | Table 1 | exact_match | 6/6 entries; independent exponent derivations | None. |
| `T_TABLE2` | Table 2 | exact_match | 38/38 numeric cells; block-sum cross-check | None. |
| `T_FIGA` | Appendix Figure A | feature_match | 6/6 checks; four series; percentile identity | No author plotting data; analytic-reference cap is 90. |

## Cross-Checks

- Every target uses `parameter_match=paper_exact`.
- Eight formula cards and four method traces are verified before numerical use.
- Four generated datasets back four final-reproduction figures.
- All ten physics assertions pass.
- All four pixel contracts pass; their aggregate pixel-fidelity score is
  `60.88`.
- Source references remain isolated from generated-data provenance.
