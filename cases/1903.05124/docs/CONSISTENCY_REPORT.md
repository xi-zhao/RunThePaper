# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | Numeric values match reference data or paper values. |
| feature_match | 5 | Scientific or algorithmic feature matches; T001/T004/T006 are reduced-scale and T002/T003 are paper-scale. |
| partial_match | 1 | T005 passes all seven panels/core checks but not the frozen exponent-depth stability check. |
| input_match_only | 0 | Inputs match, outputs still differ. |
| blocked | 0 | Missing information prevents exact validation. |
| not_in_scope | 0 | Schematic, experimental, or external context. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2(b–e) | feature_match | `outputs/checks/t001_scientific_checks.json`, `comparison-artifacts/main_fig2_feature_comparison.png` | All four qualitative/numerical structures pass and mean `|Delta p_c|=0.00409`, but heatmap/scans are coarser and the `d=1` exponent reaches its search bound. | The feature campaign uses 8–24 realizations, four transition sizes through `L=24`, and coarse probability grids; author seeds and raw trajectories are unavailable. |
| T002 | Supp. Fig. S2(a–d) | feature_match | `outputs/checks/t002_scientific_checks.json` | Independent Monte Carlo noise remains. | Author random seed and raw samples are unavailable. |
| T003 | Supp. Fig. S3(a–h), upper/lower | feature_match | `outputs/checks/t003_scientific_checks.json`, `comparison-artifacts/supp_fig_s3_comparison.png` | Caption says lower error bars are standard deviation, but the source raster scale agrees with standard error; generated odd-step saturation lines are at `t=19,17` versus the same visible source locations. | Likely caption/plot uncertainty-label mismatch; both SD and SE are persisted, SE is rendered explicitly. |
| T004 | Supp. Fig. S4(a–g), including insets | feature_match | `outputs/checks/t004_scientific_checks.json`, `comparison-artifacts/supp_fig_s4_feature_comparison.png` | All ten items, transition locations, and entropy-collapse checks pass; mean `p_c` error is `0.01182` and mean `nu=1.074`, but only four sizes through `L=24` are generated. | The source uses sizes through `L=64` and denser statistics; author seeds and raw trajectories are unavailable. |
| T005 | Supp. Fig. S5(a–g) | partial_match | `outputs/checks/t005_scientific_checks.json`, `comparison-artifacts/supp_fig_s5_feature_comparison.png` | All core scans/collapses and transition locations pass; mean `p_c` error is `0.00484`, but generated mean `nu=1.114` and span `0.679` do not reproduce the paper's weak depth dependence. | Feature campaign stops at `L=24` with eight realizations per cell, versus paper sizes through `L=64` and much denser sampling/statistics. |
| T006 | Supp. Fig. S6(a–c) | feature_match | `outputs/checks/t006_scientific_checks.json`, `comparison-artifacts/supp_fig_s6_feature_comparison.png` | All three block-size panels pass: `p_c` is strictly increasing, fitted `nu` has span `0.155`, and positive `alpha` estimates are constant-compatible within their uncertainties; mean `nu=0.989` and `alpha` noise differ from the source's tighter values. | Feature campaign preserves all six `m` and exact `d/m=3`, but stops at `L=24` with 8/16 realizations per cell rather than paper sizes through `L=64` and denser statistics. |

## Source inconsistency found during T003

At late odd steps, the independently generated trajectory-level standard
deviation of `Delta S_meas` is roughly `0.86–0.94`. With 240 realizations its
standard error is roughly `0.055–0.061`, which matches the visible error-bar
scale in the source figure. Rendering the literal standard deviation makes a
dense band nearly an order of magnitude taller than the source. This report
therefore does not claim that the caption and raster are simultaneously
reproduced: raw CSV columns preserve both, while the visual comparison uses
the standard error and flags the likely source-label error.
