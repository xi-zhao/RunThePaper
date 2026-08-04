# Numerical Methods

## Implementation

- Language: Python 3
- Main runner: `scripts/reproduce_context_dependence.py`
- Runtime dependencies: NumPy, SciPy, Matplotlib, Pillow, and Poppler
- Randomness: none in final targets; all final calculations are deterministic
  functions of the frozen released counts.

## Numerical scheme

Count tables are parsed directly from `source publication material.tar.gz`; the author notebooks
and `pyGSTi` are not executed. The implementation independently evaluates the
multinomial G-test, chi-square survival functions, aggregate standardized
score, Hochberg step-up correction, entropy-form JSD, TVD, SSTVD, and maximum
SSTVD. CSV files are written before figures are rendered.

## Paper-exact parameters

| Parameter | Fig. 2 | Fig. 3 | Source |
| --- | ---: | ---: | --- |
| Global family-wise significance | 0.05 | 0.05 | Sections IV-V |
| Top-level comparisons | 11 | 14 | Sections IV-V |
| Circuits | 1405 | 40 | Captions and Appendix A |
| Contexts per dataset family | 5 | 3 (`before`, `during`, `after`) | Captions/notebooks |
| Shots per circuit/context | 100 | 1024 | Caption/raw count totals |
| LSGST maximum core length | 256 | n/a | Section IV |
| Driven CNOT rungs | n/a | 7 | Section V/Fig. 3 |

## Checks

- G-test p-values reproduce the two worked examples after Eq. 6.
- Entropy JSD and `lambda/(2N)` agree within floating-point tolerance.
- Every selected row has the advertised sample size and two outcome fields.
- All Fig. 2 displayed values are checked after rounding at the paper's
  displayed precision; unrounded values are retained.
- All Fig. 3 SSTVD fractions are checked exactly because they are integer count
  differences divided by 1024.
- Source and generated panels are stored separately and provenance-labelled
  before visual comparison.

## Efficiency and reuse

- Complexity is linear in the number of circuit/context rows.
- Vector-free scalar loops keep every circuit identity explicit and auditable;
  the full workload is only a few thousand rows.
- Source PDFs are rendered once per target at fixed DPI.
- Paper-specific filenames, expected values, and circuit rules stay in this
  case and are not promoted into the frozen Harness.

## Known limitations

- The historical IBM hardware acquisition cannot be independently repeated.
- The Fig. 2 source plot has a factor-two JSD normalization discrepancy between
  Eq. 15 and the released plotting notebook; both representations are reported.
