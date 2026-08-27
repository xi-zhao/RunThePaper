# Similarity Scorecard

## Case score

- Overall: **63.55 / 100**
- Level: `numerical_feature_reproduction`
- Stage: `exploratory`; every scored target is `reduced_scale`.
- Provenance: five of five targets use `independent_numerics`.
- Pixel status: `not_applicable` for every target because plots are not
  geometry-registered to the publication panels.

| Target | Weight | Feature /50 | Numeric /35 | Scope /15 | Final score |
| --- | ---: | ---: | ---: | ---: | ---: |
| T002 Fig. 2(b) | 1.0 | 44 | 16 | 15 | 70 (reduced/source-only cap) |
| T003 Fig. 3(d–f) | 1.5 | 45 | 17 | 15 | 70 (reduced/source-only cap) |
| T004 Fig. 4 theory | 1.5 | 32 | 10 | 7.5 | 49.5 |
| T005 Supp. S1 | 0.5 | 39 | 13 | 15 | 67 |
| T006 Supp. S2 theory | 0.5 | 41 | 14 | 15 | 70 |

The machine-readable scorecard is
`outputs/checks/similarity_scorecard.json`; Harness normalization reports no
findings.  Ten essential numerical physics assertions pass.  T004 nevertheless
stays below the feature band because only two primary depths have complete
double boundaries.  Reduced phase/tube sampling, reconstructed cloud/tube
details, source-figure-only comparison, and missing experimental arrays prevent
a higher or final-reproduction score.
