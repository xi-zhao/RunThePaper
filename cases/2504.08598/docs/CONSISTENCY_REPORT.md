# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | No whole figure is claimed pointwise/pixel exact. |
| feature_match | 2 | Main Figures 5 and 6 reproduce their scientific behavior. |
| partial_match | 1 | Appendix Figures 8-9 execute fully but retain named mismatches. |
| input_match_only | 0 | Every opened target has generated outputs. |
| blocked | 1 | Figure 7 has a conflicting source control. |
| not_in_scope | 6 | Figures 1-4 and Tables 1-2 are context/input items. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Figure 5 | feature_match | A/B/C/E/F strict curve; D feature; E/F final distributions pass feature gate | F sorted TVD 0.08595; D is not strict | source propagation/index conventions and finite-step details are undisclosed |
| T002 | Figure 6 | feature_match | G/H/I proper-coloring and target probabilities agree within feature thresholds | sorted TVD 0.05256-0.10121 | CSV basis ordering is undisclosed; full interaction implementation may differ in hidden precision |
| T003 | Figure 8 | partial_match | A-C strict; D feature; F final distribution feature | curve E, curve F, distribution E fail | the paper's `k=chi-1` ground-including color convention is sensitive to finite tails and target indexing |
| T003 | Figure 9 | partial_match | G/I strict; J feature | distribution H fails | non-equidistant square K4 is explicitly sensitive to attractive inter-level interactions |
| T004 | Figure 7 | blocked | final PDF Appendix A.2 versus caption | protocol-c Omega conflict | missing authoritative source input |

## Source Interpretation Audits

### Tetrahedron I

Multiplying the printed Table-1 tetrahedron coordinate pattern directly by
Table 2's 5.90 um value creates edges of `sqrt(2)*5.90 um`, contradicting the
table's “lattice spacing” wording and quoted blockade-radius discussion. The
implementation therefore treats 5.90 um as the physical edge length and records
the `1/sqrt(2)` normalization in code and tests.

### Distribution indexing

Author CSVs list probabilities by row without defining whether the first or
last atom/level is the fast basis index. Raw-index TVD is retained as evidence,
but acceptance uses sorted TVD plus semantic target/proper-coloring mass. This
does not permit changing generated values or hiding named mismatches.

## Claim Boundary

This case verifies a numerical feature reproduction of the published
multilevel model and a source-bound future hardware handoff. It is not a real
hardware result, a calibrated device program, a Pasqal cross-validation, a
paper-exact reproduction, or an advantage demonstration.
