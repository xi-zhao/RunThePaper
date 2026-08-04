# Derivation

Under the frozen Bayesian update, the predictive evidence at step (j) is
(z_j=\sum_s\nu_{j-1}(s)\mu_s^{(o_j)}). Multiplying the Bayes denominators
telescopes:

$$
\prod_{j=1}^k z_j
=\sum_s\nu_0(s)\prod_{j=1}^k\mu_s^{(o_j)}.
$$

Therefore, for two scars and (n) bullet outcomes,

$$
\frac{W_k}{W_0}
=\frac{\tfrac12\left[a^n(1-a)^{k-n}+b^n(1-b)^{k-n}\right]}
{q^n(1-q)^{k-n}}.
$$

Writing (p=n/k), the asymptotic log growth is not a hybrid of the best
bullet and best circle factors. It is the envelope of two fixed sectors:

$$
g_\mu(p)=p\log\frac{\mu}{q}
+(1-p)\log\frac{1-\mu}{1-q},\qquad
X_k\to\max\{g_a(p),g_b(p)\}.
$$

For each (mu\ne q), the unique zero is

$$
p_\mu=-\frac{\log[(1-\mu)/(1-q)]}
{\log(\mu/q)-\log[(1-\mu)/(1-q)]}.
$$

The no-decay exponent is consequently

$$
\Gamma=\min_{\mu\in\{a,b\}}D(p_\mu\Vert q),
$$

with (Gamma=0) only when (q=a) or (q=b). For interior parameters the
feasible tail is never empty, so the frozen (+\infty) branch does not exist.

At ((a,b,q)=(0.37,0.81,0.62)), the selected (b) sector gives
(p_b=0.7216810415287975) and
(Gamma=0.02292773216024946).
