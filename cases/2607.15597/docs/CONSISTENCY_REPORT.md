# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 3 | paper-exact tables/formula values |
| feature_match | 2 | central physical feature independently recovered |
| partial_match | 8 | source-constrained or proxy-model result |
| blocked | 10 | classified numeric items without required source input/metadata/compute |
| not_in_scope | 2 | schematic or algorithm-trace-only figures |

## Pixel Presentation Consistency

| Gate | Result | Meaning |
| --- | ---: | --- |
| exact canvas dimensions | 8/8 | generated PNG width and height equal the source raster |
| eligible layout contracts | 3/3 | T001/T003/T007 pass aspect, ink-bbox, density, and overlap contracts |
| strict full-image SSIM ≥ 0.95 | 0/8 | no image is claimed pixel-exact |

The best SSIM is 0.8297 and the mean is 0.7524. Differences are dominated by unavailable author curve points, fonts, and Inkscape/manual post-processing; T003 additionally preserves the source-raster direction only in the presentation lane while the scientific lane follows the caption formula.

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Remaining difference / reason |
| --- | --- | --- | --- | --- |
| T001 | Fig. 2 | feature_match | closure `1.73e-16`, concurrence(T) ≈ 1 | author curve data absent |
| T002 | Fig. 3 | partial_match | endpoints 5–15 μs; N=100 low-ℓ error 0.0706 | author schedules absent |
| T003 | Fig. 4 | partial_match | 1995 μm crossover | panel-b source raster contradicts formula |
| T004 | Table S1 | exact_match | 70.71 kHz, 11.44 μm, 12.16 nm | paper reports rounded values |
| T005 | Table S2 | exact_match | analytic decay rows | none |
| T007 | Fig. S1/Table S4 | feature_match | ten exact modes; residual `1.06e-14` | schedule is independently optimized; source says both 25 and 17 segments |
| T008 | Fig. S3/Table S6 | partial_match | `η²` ratio 3.998 | analytic proxy replaces QuTiP |
| T009 | Table S7 | exact_match | 7 and 72 hybrid gates; 6/logical | none |
| T010 | Fig. S5/Table S11 | partial_match | thresholds and 66× factor | Monte Carlo markers not regenerated |
| T011 | Table S13 | partial_match | distances 11.69 and 17.54 μm | source `C4` prose/table conflict |
| T012 | Fig. S6 | partial_match | concurrence(T) 0.99917 | approximate decay, no full Lindblad solve |
| T013 | Fig. S7 | partial_match | thermal ordering recovered | analytic proxy model |
| T014 | Table S14 | partial_match | budget arithmetic | source entries reused as inputs |

Machine-readable verdicts live in `outputs/checks/`; scientific comparison images are in `comparison-artifacts/`, and pixel difference boards are in `outputs/pixel_registered/comparisons/`.
