# Derivation Trace

## Measurement probability

In the two-dimensional good/bad subspace, one amplification operation rotates
the state angle by `2 theta_a`. Starting at `theta_a`, after `m` operations the
good amplitude is `sin((2m+1)theta_a)`. Squaring it gives the Bernoulli
probability used by the numerical sampler. The `m=0` limit recovers `p=a`.

## Joint likelihood and MLE

For independent counts `h_k` from `N_k` Bernoulli trials, multiplication of
binomial kernels gives Eq. (5). Combinatorial factors are independent of
`theta_a`, so maximizing the stable log form is equivalent to maximizing the
paper likelihood. The estimator is constrained to the full physical domain
`theta_a in [0,pi/2]`, then transformed through `a_hat=sin^2(theta_hat)`.

## Fisher information

Differentiating one binomial log-likelihood with
`p_k=sin^2(q_k theta_a)`, `q_k=2m_k+1`, and
`d theta_a/d a = 1/(2 sqrt(a(1-a)))` gives
`I_k=N_k q_k^2/[a(1-a)]`. Independence adds information, yielding Eq. (10).
Direct query counting gives `N_q=sum N_k q_k`. Cauchy's inequality and the
asymptotic unbiased-MLE limit yield Eq. (13).

## Schedule sums

For LIS, `q_k=2k+1`. Therefore
`sum q_k=(M+1)^2` and
`sum q_k^2=(M+1)(2M+1)(2M+3)/3`.
Thus `N_q~N_shot M^2`, `I~N_shot M^3/[a(1-a)]`, and
`epsilon~N_q^(-3/4)` at fixed `N_shot`.

For EIS, `m_0=0` and `m_k=2^(k-1)` for `k>=1`, so the largest query weight and
both geometric sums are controlled by `2^M`. Hence
`N_q~N_shot 2^(M+1)`, `I~N_shot 2^(2M+2)/(3a(1-a))`, and
`epsilon~N_q^(-1)`.

## Complexity table

The classical sampling relation `epsilon~N_q^(-1/2)` gives query and direct
post-processing complexity `O(epsilon^-2)`. Eliminating `M` for LIS gives
`O(epsilon^-4/3)` queries; an `O(1/epsilon)` brute-force grid times
`O(M)=O(epsilon^-2/3)` likelihood work gives
`O(epsilon^-5/3)`. EIS gives `O(epsilon^-1)` queries and an
`O(epsilon^-1 log epsilon^-1)` global search.

## Conventional QAE and resource counts

Appendix A defines the four nearest phase-grid integers. Mapping these
candidates back through `sin^2` creates an independently executable
quantization-error curve. For Table 2, the explicit circuit decomposition
reduces to `C_proposed(q)=14q+4`, `Q_proposed=3`,
`C_conventional(2^r)=262*2^r-127+r(r+1)`, and
`Q_conventional=7+r`; substitution reproduces every frozen row.

All executable equations are represented in `EQUATION_CARDS.json`. The
reader-facing `DERIVATION.md` is generated from those cards and is not edited
by hand.
