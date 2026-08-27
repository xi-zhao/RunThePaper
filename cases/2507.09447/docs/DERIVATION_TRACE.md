# Derivation Trace

## 1. Core Numerical Object

For each energy and disorder strength, compute one ordered vector:

```text
Gamma(E,W) = (gamma_1, gamma_2, gamma_3, gamma_4).
```

All Lyapunov predictions are derived from this vector. Independent finite-chain
diagonalization is retained as a comparator, not folded into the same code path.

## 2. Hamiltonian Convention

The paper defines `t_{j-i}=t_{i,j}`. For `M=2`, row `i` of the eigen-equation is

```text
t_2 psi_(i+2) + t_1 psi_(i+1) + w_i psi_i
+ t_-1 psi_(i-1) + t_-2 psi_(i-2) = E psi_i.
```

This fixes both the dense OBC/PBC matrix and the transfer matrix. A unit test
compares one transfer step with this Hamiltonian row to catch reversed hopping
indices.

## 3. Site Transfer Matrix

Solving for `psi_(i+2)` gives

```text
[psi_(i+2)]   [-t_1/t_2, (E-w_i)/t_2, -t_-1/t_2, -t_-2/t_2] [psi_(i+1)]
[psi_(i+1)] = [1, 0, 0, 0]                                      [psi_i]
[psi_i    ]   [0, 1, 0, 0]                                      [psi_(i-1)]
[psi_(i-1)]   [0, 0, 1, 0]                                      [psi_(i-2)].
```

This is the `M=2` specialization of Appendix S3's one-site companion matrix
`tilde T_l(E)`. It advances one physical site, so growth is normalized per site.

## 4. Stable Lyapunov Spectrum

Direct products overflow. The formal 2026 supplemental S6 confirms periodic QR
stabilization. The implementation uses QR at each step:

```text
Z_i = T_i Q_(i-1),  Z_i = Q_i R_i,
gamma_s = limit_N (1/N) sum_i log |(R_i)_(ss)|.
```

The final exponents are sorted ascending. In the clean limit, the transfer
matrix is constant and its eigenvalues are the roots `beta_s` of

```text
sum_(s=-2)^2 t_s beta^s - E = 0,
```

so `gamma_s=log|beta_s|`. This is the primary formula/normalization test.

## 5. OBC/PBC Potentials and Density

For `M=2`, the non-Hermitian Thouless relations reduce to

```text
phi_OBC = gamma_3 + gamma_4 + log|t_2|,
phi_PBC = sum_(gamma_s>0) gamma_s + log|t_2|.
```

The independent finite-chain comparator is

```text
phi_L(E) = (1/L) sum_n log|E_n-E|.
```

Density is the two-dimensional Laplacian `rho=(1/2pi) nabla^2 phi` on a
documented grid. Second derivatives amplify finite-transfer noise, so raw
potentials remain the primary check and any display smoothing is recorded.

## 6. State Transition and Mobility Edge

The two central exponents define three states:

```text
gamma_2 < 0 < gamma_3       -> ALM
gamma_2 = 0 or gamma_3 = 0  -> UCS / mobility edge
same sign                    -> skin mode.
```

The essential exponent is the central exponent closer to zero. Its zero contour
is the mobility edge. This rule lives once in the core module.

## 7. Winding Criterion

Let `n_P(E)` be the number of positive exponents. Appendix S5 proves

```text
nu(E) = M - n_P(E) = 2 - n_P(E).
```

The reproduction checks this in two independent ways: count positive QR
exponents, and unwrap the phase of `det[E-H(exp(i theta))]` for a finite twisted
chain. Agreement away from contours validates the topology without using pixels.

## 8. ALM Fraction

The paper defines

```text
alpha = integral rho_OBC(E) Theta[-gamma_2(E) gamma_3(E)] d^2E.
```

For a finite OBC ensemble, the same observable is estimated as the fraction of
eigenvalues whose independently evaluated central exponents straddle zero. The
paper does not publish its quadrature/ensemble details, so the first estimate is
exploratory.

## 9. Supplemental nearest-neighbour hopping convention

For Eqs. (S32) and (S33), the row-`j` eigen-equation is

```text
(t+gamma+w_j) psi_(j+1) + v_j psi_j
+ (t-gamma+w_(j-1)) psi_(j-1) = E psi_j,
```

where `w=0` for the quasiperiodic model and `v=0` for the off-diagonal model.
Therefore the transfer recurrence must divide by the superdiagonal coefficient
`H[j,j+1]=t+gamma(+w_j)`. The ED and transfer implementations share this
convention, and row-residual tests now fail if `t+gamma` and `t-gamma` are
interchanged.

## 10. Unidirectional density identity

With only one nearest-neighbour hopping direction and OBC,

```text
H = diag(w_1,...,w_L) + t S_+
```

is triangular. Its eigenvalue multiset is exactly `{w_i}`, independent of the
nonzero one-way hopping. Hence the empirical OBC spectral measure converges to
the onsite distribution and `rho_OBC=rho_w`. The numerical check compares the
finite eigenspectrum and onsite multiset; it does not digitize a curve.

## 11. Fig. S3 precision observable

For every arithmetic precision `b` and probe energy,

```text
delta_phi_method^(b)(E)
  = |phi_method^(b)(E) - phi_ED^(256)(E)|.
```

Two independently written paths are used: arbitrary-precision dense ED and a
4x4 modified-Gram-Schmidt QR transfer product. The code accepts the full
published `L=1000`, 1600-realization contract. The isolated run executes a
small multiprecision pilot to validate the path and measure a paper-scale
resource projection; it does not promote the pilot ordering to Fig. S3.

## 12. Fig. S4 Lyapunov-gap scaling

The central-exponent gap is

```text
Delta_gamma^L(E0) = gamma_3^L(E0)-gamma_2^L(E0),
d_L = |Delta_gamma^L(E0)-Delta_gamma^1000(E0)|.
```

The full published size grid and `E0=-0.9328+0.2210i` are evaluated. A linear
fit of `log(d_L)` against `L` is compared with a power-law alternative fitted
against `log(L)`. The paper does not state the disorder ensemble, realization
identity, averaging order, or QR interval for S4, so those implementation
choices remain explicit rather than inferred from its plotted pixels.

## Version Boundary

The main-figure targets follow arXiv v1, while the separately identified
published-supplement targets retain their own source identity. Published S1-S4
claims are never silently substituted for arXiv-v1 claims; they are mapped to
separate items and targets with explicit parameter and compute boundaries.
