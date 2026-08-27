# Derivation Trace

This case follows the paper's theory chain before running numbers. The point is to make sure the code is computing the same numerical object as the paper.

## D001: Random-Matrix Dynamics

Formula cards: `F001`, `F002`, `F009`.

The paper starts from a one-particle Hamiltonian family

```text
H = (H0 + lambda V) / sqrt(1 + lambda^2)
```

where `H0` is diagonal with independent Gaussian entries and `V` is a real symmetric GOE matrix. The perturbation parameter is written as

```text
Lambda = lambda^2 d / (2 pi)
```

so the code uses

```text
lambda = sqrt(2 pi Lambda / d)
```

The two regimes are:

- `Lambda=0.01`: weak mixing, integrable/Poisson-like;
- `Lambda=1000`: strong mixing, chaotic/GOE-like.

The numerical evolution is

```text
U(t) = exp(-i H t)
```

implemented by diagonalizing each real symmetric `H`.

## D002: Two-Photon Boson Sampling Probability

Formula cards: `F003`, `F004`.

For a collision-free two-photon input `(i,j)` and output `(r,s)`, the permanent of the `2 x 2` submatrix reduces to

```text
Per = U[r,i] U[s,j] + U[r,j] U[s,i]
```

and the output probability is

```text
p(r,s) = |U[r,i] U[s,j] + U[r,j] U[s,i]|^2
```

The experiment only keeps collision-free two-click events, so the case uses the conditional distribution

```text
p_cond(r,s) = p(r,s) / sum_collision_free p(r,s)
```

This is the probability vector used for every reproduced numerical figure.

## D003: Porter-Thomas Distance

Formula card: `F005`.

For `M=8`, `N=2`, the collision-free dimension is

```text
D = C(8,2) = 28
```

The Porter-Thomas reference distribution is

```text
P_PT(p) = D exp(-D p)
```

For each time, the code pools all probabilities across Hamiltonian instances and output configurations, then computes a Wasserstein-1 distance to the PT reference. The expected paper feature is:

- chaotic/GOE: distance dips near `t*=1.79`;
- integrable/Poisson: distance stays much larger.

## D004: Shannon Entropy

Formula card: `F006`.

For each probability vector,

```text
S(t) = - sum_i p_i(t) log p_i(t)
```

The ensemble average is compared with the Haar-random expectation

```text
S_Haar = -1 + sum_{i=1}^D 1/i
```

For `D=28`, this is about `2.927`. The reproduced chaotic curve peaks at `2.787` in the paper-time sparse run and near the same time in the ideal curve.

## D005: OTOC-Equivalent Observables

Formula card: `F007`.

The paper uses a mapping between two-photon boson-sampling probabilities and four-point OTOC-equivalent observables. Every OTOC path now uses the same conditional two-photon probability kernel as PT distance, entropy, and PR. Conditioning happens independently for each Hamiltonian and time before the ensemble average, so the 28 collision-free curves sum to one at every time.

For output configurations sharing one mode with the input, the short-time amplitude has one off-diagonal transition, so the probability scales as

```text
C(t) ~ t^2
```

For configurations sharing no occupied mode with the input, two off-diagonal transitions are needed, so the probability scales as

```text
C(t) ~ t^4
```

The generated checks measure slopes `1.999` and `3.999`, matching the derivation.

Fig. S5 is treated separately from Fig. S6: the former says all collision-free configurations and therefore includes the source-traced initial pair `(3,4)`, while the latter explicitly excludes the initial configuration from its FFT participation-ratio analysis.

## D006: Participation Ratio

Formula card: `F008`.

The global spreading of the probability vector is measured by

```text
PR(t) = 1 / sum_i p_i(t)^2
```

The key paper feature is strong separation:

- chaotic dynamics spread probability over many configurations;
- integrable dynamics remain localized.

At `t=1.79`, the local reproduction gives:

- chaotic PR: `12.51`;
- integrable PR: `1.05`.

## D007: Eq. S8 Source-Consistency Record

Formula card: `F010`.

Appendix A first defines

```text
Y = 1 - sum_{x in C} p_x
```

as excluded probability mass, and then prints Eq. S8 using powers and an exponential in `1-y`. The following prose describes the conditional probability as a ratio involving the Gamma distribution of `Y`. These three publication statements are transcribed together in `F010` so the next fresh reviewer can distinguish a reflected-variable convention, a missing prose definition, or a paper-formula discrepancy.

The author-side repair does not adjudicate among those possibilities and does not feed Eq. S8 into the generator. T004 samples and normalizes the conditional distribution directly.

## Formula Gate Result

The formula chain is accepted for numerical reproduction because:

- all ten cards in `EQUATION_CARDS.json` have open numeric gates; `F010` is a source-only audit card rather than a numerical dependency;
- the Hamiltonian normalization and `Lambda -> lambda` conversion are explicit;
- collision-free probabilities normalize to one;
- entropy and PT diagnostics use the same `D=28` space as the paper;
- OTOC short-time power laws match the analytical `t^2/t^4` expectation;
- main feature checks pass in `outputs/checks/reproduction_feature_checks.json`.
