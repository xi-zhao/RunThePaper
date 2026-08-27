# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | Independent point values are not identical to the author's stochastic trees. |
| feature_match | 1 | Figure 8's analytic law and full-scale structure pass. |
| partial_match | 1 | Figure 9 is fully computed but its threshold claim differs. |
| input_match_only | 0 | No target stops at input validation. |
| blocked | 0 | No required target is blocked. |
| not_in_scope | 13 | Eight schematic figures and five numerical tables are outside this run. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T008 | Figure 8 | feature_match | `outputs/checks/numerical_feature_checks.json#targets/T008` | Law residual `4.44e-16`; author/independent overhead MAE `0.0600` | Different stochastic contraction trees change `(m,r)` but not the identity. |
| T009 | Figure 9(a,b) | partial_match | `outputs/checks/numerical_feature_checks.json#targets/T009` | 57/67 below `5e-4` versus paper 66/67; 9 threshold disagreements | The clean-room cotengra+NNI search explores a different tree landscape than the authors' TreeSA implementation. |

## Integrity Boundary

The primary loader opened 122 raw payloads: 12 qsim circuits, 55 structured
circuit JSON files, and 55 observable files. It opened zero author result,
network, plan, or optimizer-study payloads. Author numeric records are loaded
only after the clean-room campaign for comparison.
