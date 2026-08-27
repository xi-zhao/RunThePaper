# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | No author curve table was released in the frozen bundle. |
| feature_match | 2 | All numerical features pass analytic and independent-numerics checks. |
| partial_match | 0 | Some but not all checks pass. |
| input_match_only | 0 | Inputs match, outputs still differ. |
| blocked | 0 | Missing information prevents exact validation. |
| not_in_scope | 1 | Paper Fig. 1 is a non-numerical schematic. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2(a,b) | feature_match / complete reproduction | `outputs/checks/T001_scientific_checks.json`; mean registered SSIM 0.89205 | Minor raster/font/curve-sampling differences; no scientific failure | No author curve table; independent rendering stack |
| T002 | Fig. 3 | feature_match / complete reproduction | `outputs/checks/T002_scientific_checks.json`; registered SSIM 0.89008 | Minor raster/font/curve-sampling differences; no scientific failure | No author curve table; independent rendering stack |

## Quantitative Checks

- T001 proper-time quadrature versus independent Bessel series:
  maximum relative error `2.0875e-11`.
- T001 massless endpoint: exactly \(-\pi^4/180\) in the implemented analytic
  limit.
- T002 ratio identity \(E_0/E_L=1+E_c/E_L\): maximum row error `0`.
- T002 independent ratio representation: relative error `2.1213e-12`.
- At \(\alpha_0=25\), the four reproduced ratios lie in
  `[1.03937, 1.04434]`, consistent with the limit one.

## Paper Formula Findings

The plotted formulas are reproduced conditionally. Independent derivation
finds a factor-two radial-spectrum discrepancy in Eq. (11), a wrong Bessel
order in Eq. (36), and a wrong strong-coupling exponent in Eq. (31). Corrected
forms outperform the printed asymptotics numerically; the details are in
`DERIVATION_TRACE.md` and `T001_scientific_checks.json`.
