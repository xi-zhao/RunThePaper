# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | Author numerical arrays are unavailable, so no target claims value-by-value equality. |
| feature_match | 12 | Formula-derived data pass scientific checks and reproduce the plotted numerical feature. |
| blocked | 1 | Main Fig. 1(c) lacks a uniquely specified DFT environment. |
| not_in_scope | 4 | Main Fig. 1(a), 1(b), 4(b), and 4(c) are schematics. |

The single blocked item is `D001`, Main Fig. 1(c). Its direct cause is absent
first-principles inputs, its root cause is publication underspecification, and code
fault is not applicable until a unique DFT benchmark contract exists. It contributes
zero to the 64.62/100 paper reproduction degree; it is not silently removed from the
92.31% coverage denominator.

## Quantitative anchors

| Target | Paper statement | Reproduction | Difference/status |
| --- | --- | --- | --- |
| T002 | top-band width about 11 meV | 10.91495 meV | 0.08505 meV below the rounded statement |
| T002 | isolated top band | 12.96038 meV global isolation gap | passed |
| T003 | two-degree density-axis step 2.55e12 cm^-2 | 2.552924e12 cm^-2 | 0.115% above |
| T004 | localized Wannier orbital | normalization 1.000000 | passed |
| T007 | J2/J1 reaches 0.06 near 3 degrees | 0.060394 | passed |
| T010 | top-band width about 20 meV | 20.60747 meV | agrees with rounded scale |
| T010 | isolated top band | 3.27516 meV global isolation gap | passed |

Cutoff 5-to-6 changes the main and supplement band paths by at most 0.000987 and
0.000183 meV. All Hamiltonian, ordering, normalization and threshold checks pass.

These results support the paper at feature scale; they do not prove every published
array value. The paper-scale runner adds cutoff-7/cutoff-8 and NumPy/SciPy checks, but
its full 578-condition campaign has not run. Consequently no discrepancy in this case
is currently eligible for a `paper_error_candidate` assessment.
