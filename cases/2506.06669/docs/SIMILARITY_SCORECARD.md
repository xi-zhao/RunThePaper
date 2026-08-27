# Similarity Scorecard

## Primary paper-level measure

| Component | Value |
| --- | ---: |
| Eligible reproduction items | 60 |
| Covered items | 55 |
| Uncovered items | 5 |
| Coverage | **91.67%** |
| Mean fidelity over covered items | **69.30/100** |
| Reproduction degree | **63.52/100** |
| Evidence grade | **E1** |

The reproduction degree is `mean(item fidelity, uncovered = 0)`, equivalently
`coverage × covered-item fidelity`. This makes every omitted or failed eligible
item visible rather than allowing high scores on a subset to hide missing scope.

The critical-item floor is 60. Thirteen critical items are below it: five Main
Fig. 4(d,f) items mapped to T007, four Fig. S10 items (D001 plus three T010
panels), and the four uncovered claims C001-C004. The scientific level is
therefore capped at `partial_reproduction`.

## Historical target aggregate

The legacy ten-target score is **68.73/100**. It is retained for continuity but
is secondary because its targets mix source items with auxiliary counterpart
calculations and do not give newly enumerated uncovered items weight.

| Target | Historical score | Role in the 60-item measure |
| --- | ---: | --- |
| T001 | 70.50 | auxiliary diagnostic; source Fig. 1(c-d) is schematic |
| T002 | 62.19 | covers 9 supplemental simulation items |
| T003 | 84.33 | auxiliary theory counterpart to experimental Fig. 2(d-f) |
| T004 | 75.64 | covers 10 Main Fig. 3(a-b) theory curves |
| T005 | 72.73 | auxiliary theory counterpart to measured tomography |
| T006 | 75.87 | covers 12 Supp. Fig. S8(d-f) theory series |
| T007 | 52.12 | covers 5 Main Fig. 4(d,f) theory items; below critical floor |
| T008 | 75.42 | covers 12 Supp. Fig. S7(d-f) theory series |
| T009 | 63.52 | covers 4 Supp. Fig. S9 items |
| T010 | 55.00 | covers S10(b-d); physics-capped |
| D001 | 0.00 | S10(a), uncovered |
| C001-C004 | 0.00 each | four uncovered no-display claims |

## Pixel boundary

Pixel comparison is a fidelity component after scientific generation, not a
coverage substitute. Only predeclared theory regions are primary; full-canvas
scores diagnose layout. Original pixels may inform canvas, axes, font, line,
palette and interpolation in the RenderContract lane, but never physical
parameters or numerical arrays.

Machine-readable authorities:

- `outputs/checks/authoritative_reproduction_state.json`
- `outputs/checks/similarity_scorecard.json`
- `outputs/checks/pixel_evidence.json`
- `figure_coverage.json`
- `causal_diagnoses.json`
