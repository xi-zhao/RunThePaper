# Paper Map

## Identity

- Paper ID: `2407.01296`
- Publication: *Geometry-adaptive formulation of non-Bloch bands in arbitrary dimensions and spectral instability*, Communications Physics **9**, 127 (2026)
- DOI: `10.1038/s42005-026-02546-2`
- Authors: Ze-Yu Xing, Yuncheng Xiong, Haiping Hu

## Scientific structure

| Section | Scientific role | Numerical targets |
| --- | --- | --- |
| Eqs. (1)–(10) | spectral potential and geometry-adaptive construction | T001/T003/T004/T005/T007 |
| Eq. (11), Main Fig. 2 | geometry-dependent non-Hermitian skin spectra | T001/T004 |
| Main Fig. 3 | geometry-dependent GBZ | T003 |
| Eq. (15), Main Fig. 4 | critical modes and spectral instability | T002 |
| Supplement S2, Eq. (S17)–(S22) | exact/Amoeba benchmark | T005 |
| Supplement S4, Eq. (S24)–(S26) | 1D critical skin modes | T006 |
| Supplement S5, Eq. (S27) | 2D nonreciprocal critical modes | T007 |
| Supplement S6, Eq. (S28) | directional winding | T008 |
| Supplement S7, Eq. (S29) | first-order disorder response | T009 |

Main Figs. 1/5 and Supplement Figs. S1/S3 are schematic context and are excluded from the numerical denominator. The complete item-level inventory is `figure_coverage.json`.

## Source policy

The paper PDF and supplement define scientific scope, equations, captions, and printed parameters. Author scientific code and numerical arrays are not generation inputs. Historical comparison utilities are quarantined and cannot raise lifecycle state or score. Original figure pixels are permitted only after numerical freeze in the render-diagnostic lane.

## Known incomplete specifications

- Main Fig. 4 does not print every state-selection, integer-cut, random-seed, or probe-grid choice.
- Supplement S5 does not print the two representative complex energies.
- Supplement S7 does not uniquely define its positive scalar observable or `N=935` integer geometry.

These are modeled as parameter/review boundaries, not silently guessed paper-exact values.
