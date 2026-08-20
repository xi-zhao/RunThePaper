# Derivation Trace

## EQ001 — coherent states and the Husimi-Q distribution

For `m=-S,...,S`, write `k=S-m`. The Appendix expansion gives

```text
<S,m|theta,phi> = sqrt(C(2S,S+m))
                   cos(theta/2)^(S+m) sin(theta/2)^(S-m) exp(-i m phi),
Q(theta,phi) = |<theta,phi|psi>|^2.
```

The phase differs from the Appendix's `exp(i k phi)` only by a global
`exp(-i S phi)` and is therefore identical in Q. At theta=0 the state is
`|S,S>`; at theta=pi/2, phi=0 it is the x-polarized CSS. Binomial normalization
proves `<theta,phi|theta,phi>=1` and Q<=1.

## EQ002 — one-axis twisting

For `H=hbar chi Sz^2` and `mu=2 chi t`,

```text
U_OAT(mu) = exp(-i mu Sz^2/2).
```

In the Sz basis this is an exact diagonal phase, so no time-step integrator is
needed. Acting on `|pi/2,0>` yields every point in Fig. 2. The paper's Eqs.
(1)--(3) follow from `S_+(t)=S_+(0) exp[i mu(Sz+1/2)]` and the Appendix moment
identities.

## EQ003 — OAT transverse variances

The paper defines

```text
A = 1 - cos(mu)^(2S-2),
B = 4 sin(mu/2) cos(mu/2)^(2S-2),
V_plus/minus = S/2 * {1 + (S-1/2)/2 * [A +/- sqrt(A^2+B^2)]}.
```

`V_minus` is the smaller eigenvalue of the y-z covariance matrix after the
optimal transverse rotation. Minimizing it over mu produces the one-axis points
in Fig. 4. Expansion for `S>>1`, `|mu|<<1` gives
`V_min ~= 1/2 (S/3)^(1/3)` and `mu_0 ~= 24^(1/6) S^(-2/3)`.

## EQ004 — two-axis countertwisting

The two axes `(theta=pi/2,phi=+/-pi/4)` give

```text
S_+45^2 - S_-45^2 = Sx Sy + Sy Sx,
U_TACT(mu) = exp[-i mu (Sx Sy + Sy Sx)/4],  mu=4 chi t.
```

Starting from `|theta=0>` reproduces Fig. 3. The operator is Hermitian; the
unitary therefore preserves norm exactly up to eigensolver roundoff.

## EQ005 — minimum transverse variance

For a state whose mean spin is along z, define the symmetric covariance
`C_ij = <{Si-<Si>,Sj-<Sj>}/2>` for i,j in x,y. The variance along any transverse
unit vector is its Rayleigh quotient. Hence

```text
V_min = (Cxx+Cyy - sqrt((Cxx-Cyy)^2 + 4 Cxy^2))/2.
```

This independently reduces to S/2 for a CSS. It supplies the TACT observable
without using Fig. 4 pixels.

## EQ006 — Fig. 4 minima and limits

For each physical spin S>1, minimize the exact EQ003 OAT expression and the
exact EQ005 TACT covariance over the first squeezing interval. Compare with
the paper's three analytic references:

```text
V_CSS = S/2,
V_OAT,asym = 1/2 (S/3)^(1/3),
V_TACT,asym = 1/2.
```

The special S=1 zero-variance point is excluded exactly as stated in the Fig. 4
caption.
