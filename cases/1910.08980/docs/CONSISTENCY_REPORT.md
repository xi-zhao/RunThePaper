# Consistency Report

## T001 — `n=32`

- Independent scientific checks: passed.
- Paper QAOA/RQAOA means from reference pixels: `0.4516/0.9988`.
- Generated means: `0.4850/0.9839`.
- Sorted distribution MAE: `0.0334/0.0149`.
- Scientific conclusion: strong feature match; the independent sample has the
  same roughly 0.5 RQAOA advantage.

## T002 — `n=100`

- Independent scientific checks: passed.
- Paper QAOA/RQAOA means from reference pixels: `0.4630/0.9658`.
- Generated means: `0.4672/0.9656`.
- Sorted distribution MAE: `0.00433/0.00413`.
- Scientific conclusion: near-identical empirical distributions and the same
  roughly 0.5 RQAOA advantage.

## Direct Pixel Status

`not_applicable` for both targets.  Per-position pixel difference would compare
unrelated random samples and therefore report instance randomness as a figure
error.  The declared replacement is a post-run scientific colored-bar
distribution metric, which uses source pixels only as evaluation evidence.

## Review Classification

- The shared scientific claim survives the formula, exact-solver, recursive
  energy, grid-refinement, and independent-ensemble checks.
- Exact published bar identity remains untestable because the paper omits the
  graph/coupling samples and ordering.
- Therefore target-level discrepancies are `inconclusive` at the paper-error
  boundary.  They must not be promoted to either `paper_error_candidate` or
  `reproduction_defect` without new evidence that resolves sample identity.
- Current paper-error candidates: zero.
