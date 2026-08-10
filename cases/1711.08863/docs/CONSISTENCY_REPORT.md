# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 1 | General and closed-form coefficient arrays agree within floating-point roundoff. |
| feature_match | 1 | The plotted topology-dependent zero-decay behavior matches. |
| partial_match | 0 | No partial scientific target remains. |
| blocked | 0 | No data or compute blocker. |
| not_in_scope | 12 | Main and supplement schematic figure groups. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2, all curves | exact formula + feature match | `target_checks.json`, frozen CSV, comparison board | Only rasterization/font antialiasing can differ | Matplotlib-version and font-renderer presentation differences. |

## Protocol-v2 Paper Audit

Main Fig. 2 survived alternative-implementation, limiting-case, refinement,
and caption-inventory falsification attempts. The reproducer-side result is
therefore provisionally `paper_supported_by_reproduction`, but the formal paper
assessment remains `inconclusive` until fresh-context review.

A stable supplementary discrepancy is recorded in
`paper_review_protocol_v2.json`: Eq. `ME2AtomsMirror` attaches the `gamma_2`
decay coefficient to `D[sigma_-^a]`, whereas the preceding collapse operator
and the one-atom limit both require `D[sigma_-^b]`. This is likely a local
symbol typo and does not affect T001. It is explicitly **not** labeled
`paper_error_candidate` without the required fresh reviewer.
