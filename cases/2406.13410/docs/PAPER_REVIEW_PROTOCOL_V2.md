# Paper Review Protocol V2

This case also audits whether the paper's quantitative claims survive an
independent implementation.

1. Phase 1 reads only the full paper and supplement/appendices and freezes all
   numerical figures, subfigures, and quantitative claims.
2. Phase 2 receives the frozen inventory plus equation cards, independent code,
   configurations, generated arrays, and execution evidence.  It does not read
   the original reproduction conversation.
3. Every target gets an explicit falsification attempt, including limiting
   cases and at least one alternative numerical or analytic check.
4. A discrepancy is initially `inconclusive`.  `paper_error_candidate` requires
   two distinct strong checks, stable convergence, parameter/convention
   exclusion, a falsified alternative explanation, and fresh independent
   review.
5. Missing author inputs can block paper-exact reproduction but may not be
   replaced by digitized pixels or guessed arrays.

The two deterministic review bundles and their request are ready under
`outputs/review/`.  The inventory bundle contains only the full paper/source
materials; the falsification bundle contains the frozen inventory contract,
formula cards, code, generated arrays, machine checks, and isolated execution
evidence.  Narrative reproduction reports and source-rendering artifacts are
excluded by the Harness.

No `independent_review.json` is present: this agent has already seen the
implementation context and therefore cannot honestly act as the fresh
reviewer.  Lifecycle status must remain review-pending until a separate context
commits Phase 1 before opening Phase 2 and submits a schema-v2 result.
