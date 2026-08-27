# Similarity Scorecard

## Case Score

- Overall score: **79.31 / 100**.
- Similarity level: **numerical feature reproduction**.
- Interpretation: 13 targets contribute accepted scientific evidence, while 15
  attested clean-room target attempts remain unreproduced and one published
  channel definition is objectively underspecified. This score is separate
  from the 100% final-disposition rate.

## Figure Scores

| Target | Paper item | Score | Stage | Parameter match | Main limitation |
| --- | --- | ---: | --- | --- | --- |
| T001 | Fig. 2(b) | 47.5 | exploratory | proxy_model | absolute surface-code MLE curve not reproduced |
| T002 | Fig. 4(b) | 90.0 | final_reproduction | paper_exact | separate finite-size series attempted, not reproduced |
| T003 | Fig. 6(b) | 100.0 | final_reproduction | paper_exact | presentation styling only |
| T004 | Fig. 14(c) | 80.0 | exploratory | paper_subset | boundary-round convention reconstructed |
| T005 | Fig. 16(a) | 80.0 | exploratory | paper_subset | separate T016 subcurves attempted, not reproduced |
| T006 | Table I analytic rows | 100.0 | final_reproduction | paper_exact | simulation rows map to finalized T019/T020 attempts |

The score evaluates scientific features and numeric evidence. It does not award
credit for copying source panels or digitizing curves. Machine-readable scoring,
component reasons, caps, and physics assertions live in
`outputs/checks/similarity_scorecard.json`.

## Atomic Final Resolution

- `reproduced`: 26/272 items.
- `externally_blocked`: 1/272 item (Error Model B definition conflict).
- `attempted_not_reproduced`: 245/272 items.
- `pending`: 0/272 items.

## What Prevents A Higher Score

- The central surface-code panel families did not pass paper-method scientific
  acceptance after the bounded clean-room attempt.
- The arXiv source supplies vector plot assets but no raw samples or executable
  circuit/decoder implementation; this is context, not itself an external
  blocker.
- The paper does not disclose shots, seeds, fit windows, complete physical-error
  grids, or the exact circuit/decoder revision.
- The only local Monte Carlo is a clearly labeled repetition-code mechanism
  proxy and cannot establish the paper's absolute surface-code performance.
