# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 2 | Algebra and Fig. 3(c) public metrics match. |
| feature_match | 3 | Figs. 4/5/8 proxy, Fig. 6 proxy, and pairwise controls pass. |
| partial_match | 2 | Fig. 3(a) depth and Fig. 7 crossings differ. |
| blocked_exact | 6 | Fig. 3(b) and exact Figs. 4-8 need author state. |
| not_in_scope | 2 | Schematic/method-only figures. |

## Per-Target Consistency

| Target | Level | Evidence | Difference / boundary |
| --- | --- | --- | --- |
| ALGEBRA_CORE | exact_match | feature verdict | none across 264 cases |
| FIG3C_NATIVE | exact_match | Fig. 3 CSV | 19 gates/depth 12 exact; input transcribed |
| FIG3A_ZAP | partial_match | Fig. 3 CSV | census exact; depth 121 vs 128 |
| ROUTING_PROXY | feature_match | routing verdict | all eight classes covered under toy geometry |
| ROUTING_PROXY_SCALING | feature_match | scaling verdict | trend passes; timings are local M4 values |
| ROUTING_PROXY_SENSITIVITY | partial_match | sensitivity verdict | degree structure passes; zero of three break-even contours appear |
| FIG3B_ZX | blocked_exact | contract | no executable source/config |
| FIG4-8_EXACT | blocked_exact | contract | no unique author generator/route ensemble |

The Fig. 7 discrepancy is treated as evidence about the proxy model, not as a
failed opportunity to tune the output toward the paper.
