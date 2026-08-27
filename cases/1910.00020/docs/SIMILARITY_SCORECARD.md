# Similarity Scorecard

- Scientific similarity level: `numerical_feature_reproduction`.
- Harness-normalized score: **69.34/100**.
- Primary foreground pixel mean: **46.5946/100**.
- Full-canvas mean: **91.9579/100**, layout diagnostic only.

| Target | Scientific feature | Pixel foreground | Parameter match | Capped score |
| --- | --- | ---: | --- | ---: |
| T001 | transition crossing at 0.16 and printed-variable collapse | 46.5310 | reduced scale | 70.00 |
| T002 | local decoding-light-cone weight | 72.3916 | reduced scale | 70.00 |
| T003 | exact partial-record channel; paired data-processing order | 29.5069 | reduced scale | 70.00 |
| T004 | monotone surface order, beta_s=0.551 | 39.2612 | reduced scale | 70.00 |
| T005 | nonnegative cylinder branches | 40.5516 | reduced scale | 67.19 |
| T006 | nonnegative strip branches | 41.6046 | reduced scale | 67.56 |
| T007 | both supplemental light cones | 56.4348 | reduced scale | 70.00 |
| T008 | one/four-reference purification decay | 46.4752 | reduced scale | 70.00 |

The score is intentionally capped by `reduced_scale` and `source_figure_only` evidence. High white-background full-canvas similarity is not used to hide foreground mismatches. Physics features, formula gates, independent numerical provenance, and panel coverage are evaluated separately in `outputs/checks/similarity_scorecard.json`.
