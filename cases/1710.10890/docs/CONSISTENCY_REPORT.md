# Consistency Report

This report separates a valid generated artifact, code readiness, and agreement
with the paper. All seven baseline artifacts are independently generated and
hash-backed; T005 is an inconclusive method-equivalence gap, T007 is a proxy,
and the T007/T008 3D production campaign is code-ready but unrun.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | No target has both exact inputs and high-confidence numeric agreement over every observable. |
| feature_match | 5 | T001--T004 and T006 reproduce their declared scientific feature. |
| partial_match | 2 | T005 is parameter-ambiguous; T007 is qualitative only. |
| input_match_only | 0 | No target is accepted from inputs alone. |
| code_ready_unrun | 1 campaign | 12-task 3D production/refinement contract exists and passed smoke only. |
| blocked | 1 | Main Fig. 4 lacks exact per-curve atom numbers for a paper-exact comparison. |
| not_in_scope | 2 classes | Experimental arrays and schematic insets are not reconstructed. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(a) | feature_match | collapse at 56.8508 G | detailed curve differs | original coupled-channel model is unpublished |
| T002 | Main Fig. 1(b) | feature_match | rising critical-number boundary | field mapping differs | inherited reconstructed interaction lane |
| T003 | Main Fig. 2(c), Fig. 3(c) | feature_match | monotone ratio inside analytic band | band location/width differ | inherited reconstructed interaction lane |
| T004 | Main Fig. 3(a) | feature_match | 18.6489 and 22.5561 thresholds | field mapping differs | inherited reconstructed interaction lane |
| T005 | Main Fig. 3(b) | inconclusive | converged radial profiles and frozen arrays | stable/metastable width ordering is reversed | unstated width observable and reconstructed scattering lane prevent protocol-v2 paper-error classification |
| T006 | Supplement Fig. S1(a--c) | feature_match | exact printed potential and force-gradient signs | residual raster mismatch | line rendering and stated waist uncertainty |
| T007 | Supplement Fig. S2 theory | partial_match | late expansion is suppressed by 12 Hz confinement | absolute curves do not overlap | frozen artifact is a TF-scaling proxy and the calibration atom number is missing |
| T007 3D | Supplement Fig. S2 method | code_ready_unrun | smoke covers free/12 Hz GPE, TF-radius observable, recovery and refinements | no production curve | A100/H100 run and exact calibration N are absent |
| T008 | Main Fig. 4 theory | code_ready_unrun | smoke covers stated preparation, transfer, local-LHY dynamics and levitation | no production curve | A100/H100 run and per-curve N are absent |

The full-canvas similarity of 93.2922 is presentation diagnostics only. The
primary comparison is the predeclared scientific-theory mask, 59.6688 over
T001--T006. Source pixels never feed numerical arrays.

No current result is a `paper_error_candidate`. A failed paper-scale invariant
or convergence check is a `reproduction_defect`; passing under the explicit
N=4e5 assumption remains `inconclusive` for paper agreement.
