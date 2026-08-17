# Consistency Report

This file states which outputs match the paper and which do not.

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 0 | No author numeric array exists for pointwise comparison. |
| feature_match | 1 | T001 reproduces the complete scientific band feature. |
| partial_match | 0 | Some but not all checks pass. |
| input_match_only | 0 | Inputs match, outputs still differ. |
| blocked | 0 | Missing information prevents exact validation. |
| not_in_scope | 4 | Fig. 1 inset, Fig. 2(a-b) and Fig. 3 are schematics. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1 band axes | feature_match | 14/14 checks; pixel 91.19 | Generated line density is 0.507 of the paper crop and the exact finite-strip branch count cannot be certified. | The paper omits ribbon width and k-grid; width 20 is declared and converged, never fitted to source pixels. |

## Paper Review Findings

Three equation-number references are internally inconsistent: the strip prose
and Fig. 1 caption point to Eq. (7) although the lattice Hamiltonian is Eq. (6),
and the microscopic SO expectation-value prose points to Eq. (8) although that
operator is Eq. (7). The scientific meaning is unambiguous and unaffected.
Classification remains `inconclusive_pending_fresh_review`; no paper-error
candidate is emitted.
