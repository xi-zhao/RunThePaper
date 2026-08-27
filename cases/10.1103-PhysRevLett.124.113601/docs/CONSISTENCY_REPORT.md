# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| complete_reproduction | 1 | Fig. 3 passes paper parameters, vector-path checks, and pixel-layout evidence. |
| feature_match | 3 | The remaining figures pass their physical feature contracts but retain metadata caps. |
| partial_match | 0 | No target has a failed essential feature. |
| blocked | 0 | All declared computations completed locally. |
| not_in_scope | 1 | Fig. 1 apparatus schematic. |

## Per-Target Consistency

| Target | Level | Evidence | Match | Remaining difference |
| --- | --- | --- | --- | --- |
| T001 / Fig. 2 | feature_match | `fig2_state_thresholds.json`, vector check | mobility edge/index/energy; 377-point IPR match | excited-state threshold normalization absent |
| T002 / Fig. 3 | complete_reproduction | mechanism, vector and pixel checks | intercept, divergence, momentum peaks, channel indices, layout | no author CSV, but source vector paths are pointwise references |
| T003 / Fig. 4 | feature_match, exploratory | Fig. 4(a)/(b), vector and pixel checks | onsets/endpoints and harmonic minima | linear/nonlinear convention split; missing continuation metadata |
| T004 / Fig. S1 | feature_match, exploratory | density, vector and pixel checks | all five shape/peak/localization transitions | source-calibrated pump samples |
| D001 | diagnostic pass | `finite_size_and_trap.json` | size/trap claim qualitatively supported | paper publishes no diagnostic curve |

Fig. 3, Fig. 4, and Fig. S1 are pixel-registered with exact canvas dimensions. Full-image SSIM is `0.860`, `0.792`, and `0.786`; Harness axis-box IoU is `0.962`, `0.924`, and `0.984`.
