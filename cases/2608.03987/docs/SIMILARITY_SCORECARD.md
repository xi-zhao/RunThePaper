# Similarity Scorecard

## Whole-paper Status

- Atomic theoretical numerical items: `6`
- Items with acceptable generated artifacts: `3`
- Item coverage: `50.0%`
- Covered-item scientific fidelity: `(89 + 55 + 55) / 3 = 66.3/100`
- Whole-paper reproduction degree: `(89 + 55 + 55 + 0 + 0 + 0) / 6 = 33.2/100`
- Interpretation: Figure 8 passes at full scale; Figure 9(a,b) is independently
  computed but its central threshold classification is not reproduced; Table 1
  core, Table 1 extension, and Table 5 are declared but have no acceptable
  independent artifacts yet.

The machine scorecard's `72.0/100` remains a **covered-target quality mean** for
the two currently comparable target contracts, T008 and T009. It is not the
whole-paper reproduction degree: T009 contains two atomic panels, while the
three uncovered table targets are excluded from that quality mean and receive
zero credit in the item-level degree above.

## Figure Scores

| Target | Weight | Feature | Numeric | Scope | Raw | Capped score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T008 / Figure 8 | 1.0 | 50/50 | 30/35 | 15/15 | 95 | 89 |
| T009 / Figure 9 | 1.0 | 40/50 | 18/35 | 15/15 | 73 | 55 |
| T010 / Table 1 core | excluded | 0/50 | 0/35 | 0/15 | 0 | 0 |
| T011 / Table 1 extension | excluded | 0/50 | 0/35 | 0/15 | 0 | 0 |
| T012 / Table 5 | excluded | 0/50 | 0/35 | 0/15 | 0 | 0 |

T008 is capped at 89 because the benchmark scale and search-step budget match,
but the optimizer implementation and seed ensemble do not exactly match the
paper. T009 is capped at 55 because the essential `5e-4` threshold assertion
fails on nine additional circuits.

T010-T012 are aggregate-excluded only because no generated primary metric yet
exists; averaging their zeros into a *quality* mean would conflate coverage
with fidelity. They remain in the authoritative item denominator and therefore
lower the whole-paper reproduction degree exactly as shown above.

## Numerical Axes

- Figure 8: overhead Pearson correlation `0.9881`, MAE `0.0600`, law residual
  `4.44e-16`.
- Figure 9: overhead-series correlations `0.9857–0.9905`; gap correlation
  `0.3359`; threshold agreement `58/67`.
- All generated data have `independent_numerics` provenance.

The machine-readable scorecard is
`outputs/checks/similarity_scorecard.json`.
