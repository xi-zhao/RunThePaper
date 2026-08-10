# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| physically consistent / paper physical parameters | 8 | main invariants or spectra reproduced with printed parameters |
| feature match / reduced numerical grid | 3 | DOS and two sweeps reproduce the feature with declared finite grids |
| deferred | 2 | first-principles DFT panels lack exact benchmark metadata/workflow |
| excluded non-numerical | 4 panel groups | schematics only |

## Per-target evidence

| Target | Scientific consistency | Pixel primary | Main evidence / remaining difference |
| --- | --- | ---: | --- |
| T001 | winding and texture match | 75.54 | `N_w=-0.9969`; source also overlays stacking icons/markers |
| T002 | narrow Chern bands and TB fit match | 49.45 | dispersion is close; text placement and exact plotting density differ |
| T003 | enhanced DOS and integer resets match | 59.69 | finite MBZ grid/broadening suppress source peak heights |
| T004 | negative curvature map and Chern match | 71.31 | map topology/range match; color interpolation differs |
| T005 | two-degree band ordering matches | 62.63 | dispersion agrees; annotations omitted from scientific render |
| T006 | two gap-closing branches match | 64.85 | estimates 1.75 and ~3.2 degrees versus printed ~1.74/~3.1 |
| T007 | three phase regions and boundaries match | 91.89 | strongest registered pixel match; finite sweep interpolation remains |
| T008 | remote-conduction valence bands match | 59.58 | cutoff-3 with 0.64 meV worst high-symmetry convergence difference |
| T009 | isolated conduction pair matches | 48.70 | curves match feature; labels/annotation density differ |
| T010 | 1.2-degree spin-mixed spectrum matches | 55.62 | remote bands leave top spectrum stable |
| T011 | two-degree spin-mixed spectrum matches | 40.77 | scientific branches match; crop/line alignment is least similar |

All pixel numbers are literal foreground RGB mean-absolute differences after the predeclared scientific axes/map crops are registered. Full-canvas similarity (89.07 mean) is diagnostic only.

## Review classification

- The formula-derived continuum mechanism and printed transition
  neighborhoods are supported by the current independent run.
- T003/T006/T007 remain reduced-grid evidence until the code-ready 203-unit
  paper-scale campaign is executed and frozen.
- D001-D002 cannot adjudicate the paper bands without exact relativistic
  pseudopotential/workflow identity.
- Stable differences in either group are `inconclusive` at the paper-error
  boundary.  Current paper-error candidates: zero.
