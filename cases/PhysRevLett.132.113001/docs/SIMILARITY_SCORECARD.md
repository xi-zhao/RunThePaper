# Similarity Scorecard

- Overall score: **66.0 / 100**
- Level: `numerical_feature_reproduction`
- Scope: 12 independently generated targets; 5 use paper-exact printed
  formulas/tables, 6 use paper subsets, and T009 is a leading-Dirac proxy.

The score is scientific rather than cosmetic.  Pixel scoring is not applicable
because the generated plots are not geometrically registered to the paper;
post-freeze boards are diagnostic only.  Seven targets carry explicit
paper-exact boundary failures, so their scores are capped even when their
declared internal checks pass.

| Targets | Scientific result | Main cap |
| --- | --- | --- |
| T001-T002 | Exact Stark matrix and branch structure | reconstructed hyperfine factors |
| T003 | Six-component calculated spectrum | measured array/covariance unavailable |
| T004 | Published metrology-plane scalars | incomplete covariance geometry |
| T005-T006 | Exact printed regression models | measurement points unavailable |
| T007-T008 | Main numerical tables | Table I displayed-row closure |
| T009 | Leading field-free Dirac table | higher QED/finite-size terms absent |
| T010 | 20 Stark-table entries within 2.16 kHz | hyperfine approximation |
| T011-T012 | Decimal binding and Rydberg claims | printed rounding/measurement arrays |

Machine record: `outputs/checks/similarity_scorecard.json`.
