# Similarity Scorecard

## Case Score

- Overall score: `70.85/100`
- Similarity level: `numerical_feature_reproduction`
- Interpretation: the algebraic compiler core and Fig. 3 native mechanism pass;
  ZAP counts are exact with a seven-layer depth mismatch; three routed targets
  are independently generated but strictly capped as proxies.

## Figure/Method Scores

| Target | Weight | Feature | Numeric | Coverage | Final score |
| --- | ---: | ---: | ---: | ---: | ---: |
| ALGEBRA_CORE | 0.18 | 48/50 | 34/35 | 13/15 | 90 |
| FIG3C_NATIVE | 0.24 | 46/50 | 32/35 | 11/15 | 89 |
| FIG3A_ZAP | 0.18 | 42/50 | 25/35 | 7.5/15 | 74.5 |
| ROUTING_PROXY | 0.18 | 45/50 | 8/35 | 14/15 | 55, proxy cap |
| ROUTING_PROXY_SCALING | 0.12 | 37/50 | 5/35 | 12/15 | 54, proxy cap |
| ROUTING_PROXY_SENSITIVITY | 0.10 | 25/50 | 3/35 | 7/15 | 35, partial proxy cap |

## Evaluation Metadata

| Target | Critical | Data-backed | Parameter match | Failure type |
| --- | --- | --- | --- | --- |
| ALGEBRA_CORE | true | true | paper_exact | none |
| FIG3C_NATIVE | true | true | paper_subset | missing_benchmark_metadata |
| FIG3A_ZAP | true | true | paper_subset | partial_target_coverage |
| ROUTING_PROXY | false | true | proxy_model | missing_benchmark_metadata |
| ROUTING_PROXY_SCALING | false | true | proxy_model | missing_benchmark_metadata |
| ROUTING_PROXY_SENSITIVITY | false | true | proxy_model | proxy_break_even_not_reproduced |

## What Prevents A Higher Score

- The Fig. 3 circuit support stream is transcribed from the target panel because the six clauses are absent. Recomputed counts are useful diagnostics, but they do not count as independent scientific coverage.
- The ZAP gate order gives depth `121`, not the paper's `128`.
- Author benchmark generators, geometry, seeds, compile environment, and route
  traces are unavailable for exact Figs. 4-8.
- The toy router does not reproduce Fig. 7 break-even contours and has no ZX
  comparison stream.

Machine-readable record: `outputs/checks/similarity_scorecard.json`.
