# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | No author raw theory arrays are available for pointwise comparison. |
| feature_match | 4 | Every in-scope theoretical target passes its scientific feature checks. |
| partial_match | 0 | No opened target has a failed rule. |
| input_match_only | 0 | All input-matched targets were executed. |
| blocked | 0 | Core theory reproduction has no blocker. |
| not_in_scope | 3 families | Hardware, calibration/tomography, and measured panels. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2D-F; S14-S16 | `feature_match` | norm/density errors <2e-15; visual ballistic fronts | no pointwise source array | paper provides rendered panels only |
| T002 | Fig. 3B-E; S12, S17 | `feature_match` | bounded entropy/correlation/concurrence; Eq. S29 velocity error 0.00223% | experimental LR-envelope arrays unavailable | source-data boundary |
| T003 | Figs. 3-4; S18-S20 | `feature_match` | strong-hardcore distance 0.0196 vs strong-free 1.177 | generated panels show raw G rather than per-panel normalized pixels | scientific pattern retained |
| T004 | Fig. S8 | `feature_match` | max double occupancy 0.02910 < 0.03 | heatmap replaces twelve line traces | presentation only |

## Backend Consistency

The independent CuPy run on an `NVIDIA A100-SXM4-80GB` passes all five
NumPy-signature comparisons. Absolute differences range from `7.40e-16` to
`1.08e-14`, well below the `1e-9` absolute and relative tolerance. This closes
the algorithm/backend consistency gate without changing the source-figure
evidence level.

## Scientific Interpretation

The decisive result is T003: under the calibrated attractive anharmonicities,
the normalized off-diagonal correlation pattern is about sixty times closer to
the explicit hard-core sector than to the free-boson sector. T004 independently
verifies why that limiting description is valid over the paper time window.
