# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 1 | General and closed-form coefficient arrays agree within floating-point roundoff. |
| feature_match | 1 | The plotted topology-dependent zero-decay behavior matches. |
| partial_match | 0 | No partially accepted target is counted as covered. |
| reproduced analytic claim | 3 | T002-T004 have independent derivations, exact witnesses and isolated checks. |
| not_in_scope | 27 | Atomic formula/schematic display items retained but excluded. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2, all curves | exact formula + feature match | `target_checks.json`, frozen CSV, comparison board | Only rasterization/font antialiasing can differ | Matplotlib-version and font-renderer presentation differences. |
| T002 | Arbitrary multi-point topology theorem | analytic identity match | factorization artifact + isolated attestation | No scientific discrepancy found | Direct sums and emission-phasor factorization agree. |
| T003 | Protected-chain tunability theorem | exact rank/feature match | identity-minor proof + constructive checks | No scientific discrepancy found | Exact all-N witness closes the former finite-size gap. |
| T004 | Protected all-to-all control theorem | exact rank/feature match | triangular-minor proof + N=3 checks | No scientific discrepancy found | Exact all-N witness and printed constructions agree. |

The atomic scientific result is 4/4 reproduced: coverage 100.00%, fidelity and
reproduction degree 87.66. Fresh review remains a separate lifecycle gate.

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
