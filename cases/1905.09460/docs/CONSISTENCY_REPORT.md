# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| complete_reproduction | 2 | printed formulas and paper parameters independently reproduce the target |
| numerical_feature_reproduction | 2 | central feature matches; an unreported method choice prevents exact status |
| not_in_scope | 1 | Main Fig. 2 is schematic context |
| failed | 0 | no essential physics assertion failed |

## Per-target consistency

| Target | Level | What matches | Remaining difference |
| --- | --- | --- | --- |
| T001 Main Fig. 1 | complete | spectra, `h_c`, PT breaking, IPR, winding | stable winding is exactly quantized while source direct-determinant points scatter near `h_c`; lighter annotations |
| T002 Main Fig. 3 | feature | localized/broad spectra and transition at `2V0` | source transient controls and bandwidth definition are unreported |
| T003 Supp. Fig. S1 | feature | open spectra, immediate PT breaking, IPR, `(0,3)` edge count at `h=0` | source edge classifier is unreported; late-`h` counts differ |
| T004 Supp. Fig. S2 | complete | real/imaginary exact and first-order etalon curves | font, margin, and anti-aliasing pixels only |

The generation log explicitly records no reference files read and no digitized
data used. Pixel comparisons are built by a separate script after the
scientific check has passed.
