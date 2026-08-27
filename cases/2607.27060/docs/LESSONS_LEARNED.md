# Lessons Learned

## What Worked

- Mapping panels to four explicit series prevented a visually plausible but
  incomplete reproduction.
- Log-domain error predicates avoided overflow without altering integer
  thresholds.
- Current-pass/predecessor-fail certificates caught the exact semantic risk in
  the paper's Appendix-A binary-search pseudocode.
- Keeping scientific and pixel lanes separate made it possible to report
  pixel 100 while still qualifying an overgeneralised scientific statement.

## New Failure Modes

1. A first cross-target assertion incorrectly combined “lowest `N`” with
   “lowest `g`” at every `M`.  The generated data rejected it.  The corrected
   model treats the factor-two second-order gate cost explicitly and records a
   crossover.
2. A literal equality check on reported `lambda` values was too strong.  The
   paper uses conservative norm inputs; acceptance should require a safe upper
   value, not equality with one independently computed tighter bound.
3. Direct exponentiation during search can overflow before the bracket reaches
   the physically relevant scale.  Predicate comparisons belong in log space.

## Generalisable Practices

- For monotone threshold figures, store both sides of every discrete optimum.
- Separate “method minimises algorithmic steps” from “method minimises total
  cost”; per-step cost can reverse the ordering.
- Treat rounded or conservative parameters as part of the paper target while
  auditing their derivation separately.
- Source images may reveal that a visual check is worth running, but parameter
  repair must come from formulas, text, or verified source methods—not pixels.

## Reusable Checks Or Tools

- A generic monotone-integer threshold certificate could verify current-pass
  and predecessor-fail conditions across future cases.
- A generic claim checker should distinguish optimisation objectives (`N`
  versus `g`) and search for crossovers before accepting “best method” prose.
- A stable PSD square-root helper based on Hermitian eigendecomposition avoids
  singular-matrix warnings in Choi-bound diagnostics.

## Frozen-Trial Promotion Boundary

These are candidate Harness improvements, but this Trial deliberately does not
modify `PRAgent-workflow`, framework, kernel, campaign, protocol, manifest, or
backlog files.  Promotion belongs to a later candidate version after the
frozen evaluation closes.
