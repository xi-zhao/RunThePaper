# Lessons learned

1. Bayes normalization factors often telescope; check this before building a
   sample-path simulation.
2. A mixture preserves fixed latent components inside its likelihood. Choosing
   a different component independently for each observed symbol creates a false
   rate function.
3. Rare-event Monte Carlo must be budgeted from the predicted exponent before
   it is prescribed.

## New Failure Modes

- `overlapping_piecewise_branches`: two advertised exclusive cases are true at
  the same parameters.
- `hybrid_latent_sector`: outcome-wise maxima are combined although no single
  latent component realizes them.
- `projector_with_fractional_eigenvalues`: an idempotent measurement is assigned
  arbitrary continuous eigenvalues.

## Reusable Checks Or Tools

- `code/src/scar_bayes.py` supplies zero-safe word likelihoods, exact Bayes
  telescoping, corrected Bernoulli rates, and Lucas dimensions.
- `code/scripts/run_ldp_audit.py` evaluates ultra-small binomial event
  probabilities exactly in log space.
