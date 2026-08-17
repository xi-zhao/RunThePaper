# Paper Review Protocol V2

## Review question

Can a fresh reviewer independently inventory and falsify all numerical content in the Letter, including the micromaser parameter boundary and the duplicated Fig. 3(D) bias label, without reading the original reproduction conversation?

## Two-phase boundary

1. Phase 1 reads only the paper bundle and freezes every numerical figure, subfigure and quantitative text claim.
2. Phase 2 reads the immutable inventory plus formulas, clean-room code, configuration, frozen generated data, tests and run attestation.
3. The reviewer attempts to falsify each target using an analytic limit, invariant, convergence study or independent implementation.
4. Author computational code, author numerical arrays and the original reproduction-session explanation remain unavailable.

## Paper-error threshold

A source discrepancy is not a paper error by itself. Promotion requires source pinpointing, two distinct strong checks, explicit falsification, parameter and convergence audits, an independent numerical method, code-fault exclusion and fresh-context review.

## Known falsification focus

- Re-inventory Main Fig. 3(B-D) and determine whether the original Letter contains enough information to fix `N_ex` and thermal occupation.
- Recheck the micromaser tridiagonal reduction using a structurally independent solver.
- Test whether the weaker reconstructed stationary second peak is entirely attributable to missing parameters.
- Decide whether the lower Fig. 3(D) label should read `s=+0.05`; both visible upper and lower labels currently read `s=-0.05`.

Current classification: `inconclusive_source_label_discrepancy`; `paper_error_candidates=0`. No independent-review result may be fabricated by this reproduction context.
