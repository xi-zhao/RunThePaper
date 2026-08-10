# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| paper_parameter_feature_match | 10 | Thermodynamic formula/ODE targets use the paper's parameters. |
| reduced_scale_feature_match | 13 | Quantum targets reproduce the scientific feature at smaller `N_b`. |
| partial_match_with_source_discrepancy | 1 | S2 right is reproduced with its source semantic conflict explicit. |
| not_in_scope | 2 | Conceptual schematic groups. |

## Per-Target Consistency

| Targets | Paper item | Level | Foreground pixel range | Difference |
| --- | --- | --- | ---: | --- |
| T001 | Main Fig. 1(c) | reduced_scale_feature_match | 48.46 | smaller finite sizes |
| T002–T005 | Main Fig. 2 and insets | reduced_scale_feature_match | 31.64–40.69 | `N_b=16` vs 36 |
| T006–T007 | Main Fig. 3 | reduced_scale_feature_match | 25.63–46.76 | reduced size/branch set |
| T008,T010 | Main Fig. 4 finite-size regions | reduced_scale_feature_match | 39.35–39.66 | smaller sizes |
| T009 | Main Fig. 4 inset | paper_parameter_feature_match | 35.50 | render sampling differs |
| T011 | Supplement S2 left | reduced_scale_feature_match | 49.92 | `N_b=24` vs 600 |
| T012 | Supplement S2 right | partial_match_with_source_discrepancy | 50.66 | caption says variance; curves behave as squared means |
| T013–T015 | Supplement S3–S4 | reduced_scale_feature_match | 43.12–47.32 | smaller sizes/grid |
| T016–T019 | Supplement S5 | paper_parameter_feature_match | 35.97–38.56 | fewer generated trajectories |
| T020 | Supplement S6 | paper_parameter_feature_match | 73.08 | contour density/layout differs |
| T021–T024 | Supplement S7 | paper_parameter_feature_match | 26.97–32.16 | fewer generated trajectories |

## Source Issues Found

1. The source TeX writes `S±=Sx±Sy`; standard spin algebra and the later supplement
   require `S±=Sx±iSy`. The correction is explicit in the equation card and tests.
2. Supplement Fig. S2 right is called a variance plot, but its polarized-limit values
   and shapes are compatible with squared normalized means. The generated dataset
   contains centered variances, second moments, and squared means side by side. The
   paper-facing rendering uses squared means; a separate centered-variance figure is
   retained for falsification.

Neither issue is concealed by pixel fitting, and neither original curve is digitized.

## Protocol-v2 scientific-review boundary

This report preserves the two stable inconsistencies; it does not promote either to a
paper error.

| Issue | Current assessment | Missing evidence before `paper_error_candidate` |
| --- | --- | --- |
| Main-text `S_\pm` definition omits `i` | implementation uses the algebraically consistent standard ladder operator; source inconsistency recorded | paper-exact rerun, convergence, two independent derivations/checks, explicit falsification and fresh review |
| S2-right caption says variance while limiting behavior resembles squared means | `inconclusive`; paper-scale output freezes centered variance, squared mean, and second moment together | completed `N_b=600` run, strict numerical reference, convergence, two independent cross-checks, quantified discrepancy and fresh review |

The paper-scale execution contract sets `paper_error_candidate_emitted=false` by
construction.  Machine acceptance only proves that the declared numerical object ran
and passed invariants.  It cannot choose a statistic by pixel similarity, tune a stable
discrepancy away, or substitute for the protocol-v2 review gate.
