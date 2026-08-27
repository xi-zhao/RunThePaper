# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact analytic/numeric match | 2 | Generated values equal the paper's closed forms and exact landmarks. |
| complete panel coverage | 4/4 | Every numerical subpanel is represented. |
| pixel contract passed | 2 | Canvas, axis geometry, density, and provenance gates pass. |
| blocked / partial | 0 | No scientific target is blocked or reduced. |

## Per-Target Consistency

| Target | Paper item | Scientific consistency | Pixel evidence | Remaining difference |
| --- | --- | --- | --- | --- |
| T001 | Main Fig. 1 | exact formula, symmetry, midpoint and limits | SSIM `0.884565`, axis IoU `0.972454`, ink proximity `0.954913` | font/math rasterization and annotation placement |
| T002 | Main Fig. 2(a-c) | exact 11 branches, bounds, crossings and singularities | SSIM `0.781102`, axis IoU `0.924759`, ink proximity `0.907293` | Wolfram vs Matplotlib typography and antialiasing |

The lower Figure 2 SSIM is not a hidden physics mismatch: the absolute
difference board concentrates on titles, labels, tick glyphs, and line
antialiasing, while all independently generated curves follow the exact source
equations. Source pixels did not enter generation.
