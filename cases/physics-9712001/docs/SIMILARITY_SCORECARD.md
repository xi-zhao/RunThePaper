# Similarity scorecard

The authoritative machine-readable scorecard is
`outputs/checks/similarity_scorecard.json` (schema v4).

- Overall score: **89.15/100**
- Similarity level: `numerical_feature_reproduction`
- Paper-parameter targets: 29/29
- Generated/data-backed targets: 29/29
- Paper-claim science status: 28 passed, 1 failed (`T004`)
- Numerical-runner manual interventions: 0
- Source pixels used by the numerical generator: forbidden / 0

| Target group | Count | Typical final score | Limiting evidence |
|---|---:|---:|---|
| Main Fig. 1 | 1 | 90.00 | analytic-reference cap; scientific pixels 97.47 |
| Table I | 2 | 99.98 | complete exact-cell comparison |
| Table II | 1 | 55.00 | essential paper claim fails on three stable rows |
| Main Fig. 3 | 3 | 86.79 | accepted scientific-region pixel score |
| Atomic formula/prose claims | 22 | 90.00 | analytic-reference cap after independent numerics |

The overall score is a quality metric, not a lifecycle decision. The Harness
reports `final_reproduction_ready=false` and names T004 as science-blocked, so
a high average cannot hide a failed paper claim. The exact per-target evidence
is retained in the machine scorecard and `TARGET_LEDGER.md`.
