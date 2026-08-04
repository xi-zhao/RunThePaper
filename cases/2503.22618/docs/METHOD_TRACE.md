# Method trace

1. Recover the real PRL and all source assets.
2. Separate the source's PXP/TEBD claims from the synthetic frozen extension.
3. Execute the frozen Bayesian recursion on full outcome words.
4. Prove and numerically verify the telescoped marginal-likelihood identity.
5. Reduce the no-decay event to two Bernoulli tails.
6. Evaluate their exact log probabilities with `gammaln`/`logsumexp` through
   (k=200000).
7. Verify the PBC dimension with an integer Fibonacci recurrence.

This exact T0/T1 audit dominates a GPU Monte Carlo for a probability near
(10^{-1994}).
