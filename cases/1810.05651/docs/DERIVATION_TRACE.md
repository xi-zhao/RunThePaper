# Derivation Trace

Every formula used by `scripts/reproduce_context_dependence.py` is represented
in `EQUATION_CARDS.json`. `DERIVATION.md` is generated from those cards and is
not edited by hand.

## EQ001 - multinomial log-likelihood ratio

For context `c` and outcome `m`, maximize the multinomial likelihood separately
under the alternative, giving `p_hat[c,m] = x[c,m] / N[c]`. Under context
independence, pool the counts and obtain
`p_hat[0,m] = sum_c x[c,m] / sum_c N[c]`. Substituting both maximum-likelihood
solutions into `-2 log(L0/L1)` cancels multinomial coefficients and yields the
G-test form

`lambda = 2 sum_(c,m) x[c,m] log(x[c,m] / E[c,m])`,

where `E[c,m] = N[c] sum_c x[c,m] / N`. Each of `C` probability vectors has
`M-1` free entries while the null has one vector, hence
`k = (C-1)(M-1)`. The implementation verifies the two one-qubit examples quoted
after Eq. 6 and uses `chi2.sf(lambda, k)`.

## EQ002 - Hochberg family-wise correction

Sort the `Q` p-values increasingly. For each one-based rank `l`, test
`p_(l) <= beta / (Q-l+1)` and retain the largest passing rank. All p-values no
larger than the resulting pseudo-threshold are significant. Inverting the
chi-square survival function gives the LLR threshold. The implementation also
checks that the number of selected circuits equals the retained Hochberg rank.

## EQ003 - aggregate detection

Independence of distinct circuit count pools makes log likelihood ratios
additive, so `lambda_agg = sum_q lambda_q`; chi-square degrees of freedom add
likewise. Standardizing a chi-square variable by its exact mean `k_agg` and
variance `2 k_agg` gives Eq. 13. The implementation compares the independently
computed values against every displayed Fig. 2 matrix entry and the notebook's
five-context summary.

## EQ004 - Jensen-Shannon identity

Using weights `pi_c=N_c/N`, substitute the empirical distributions
`P_c(m)=x[c,m]/N_c` into the entropy definition. Expanding the entropies gives

`2 N JSD = 2 sum_(c,m) x[c,m] log(x[c,m]/E[c,m]) = lambda`.

The code computes JSD both from this identity and independently from the
entropy definition and requires agreement to floating-point precision.

The released Fig. 2 notebook instead plots `lambda/(2*100)` for two pools of
100 shots, whereas Eq. 15 uses `lambda/(2*200)`. Therefore the paper-compatible
lower panel is exactly twice the standard JSD. Both columns are retained in the
CSV; this source-figure normalization artifact does not alter any LLR,
p-value, detection, or trend conclusion.

## EQ005 - TVD and SSTVD

For two binary distributions, Eq. 18 reduces to the absolute difference
between either outcome probability. SSTVD is deliberately nullable, not zero,
when the circuit fails the corrected individual-circuit test. The maximum is
taken only over non-null SSTVD values. The IBM check requires all seven
before/after comparisons to remain undetected and all seven before/during
comparisons to be detected.

## Independent checks

- source trace against the frozen TeX equations and notebook algorithms;
- algebraic LLR/JSD identity;
- degrees-of-freedom count and chi-square limiting distribution;
- normalization of every probability vector;
- exact per-pool shot counts (100 for Fig. 2 and 1024 for Fig. 3);
- all published matrix counts and SSTVD values checked from raw count files;
- no value is digitized from a plotted curve or copied from a source panel.
