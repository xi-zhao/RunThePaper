# Derivation Trace

## Basis and invariant

Use the ordered extended basis

```text
|cav>, |1>, ..., |N>, |S>
```

of dimension `d=N+2`. The Hamiltonian conserves the excitation in the first
`N+1` states. Lindblad jumps either preserve it or move it irreversibly to the
sink. Therefore a source excitation `rho(0)=|1><1|` remains a normalized,
positive density operator in this extended one-excitation space.

## EQ001 — coherent Hamiltonian and disorder

Main Eq. (1) becomes the matrix

```text
H[cav,i] = H[i,cav] = g
H[i,i+1] = H[i+1,i] = t + delta_t * X_i
H[i,i] = epsilon
H[cav,cav] = omega_a
H[S,:] = H[:,S] = 0
```

with independent `X_i ~ Normal(0,1)`. A common scalar energy is irrelevant, so
the resonant simulations set `omega_a=epsilon=0`. The source does not state the
mean hopping. We reconstruct `t=1 meV` from the SM Fig. S5 statement that the
QCLE peak is at `g≈t` and from cross-figure numerical agreement; this
assumption remains explicitly outside the formula gate.

## EQ002 — finite-temperature detailed balance

For Bose occupation `n=(exp(Delta/kBT)-1)^(-1)`, the paper gives

```text
gamma_em  = 2 J(Delta) (1+n)
gamma_abs = 2 J(Delta) n.
```

Their ratio is

```text
gamma_abs/gamma_em = n/(1+n)
                    = exp(-Delta/kBT).
```

The numerical figures parameterize `gamma_rec=gamma_em` and use
`gamma_abs=gamma_rec*exp(-1/x)` with `x=kBT/Delta`. Thus the reverse jump
vanishes continuously as `x->0` and becomes comparable to emission for
`x>>1`.

## EQ003 — jump families

Within the single-excitation basis,

```text
L_rec,i   = sqrt(gamma_rec) |cav><i|
L_abs,i   = sqrt(gamma_abs) |i><cav|
L_deph,i  = sqrt(gamma_deph) |i><i|
L_drain   = sqrt(gamma_lead) |S><cav|     (cavity drain)
          = sqrt(gamma_lead) |S><N|       (site-N drain).
```

Each jump enters `D[L]rho=L rho L† - {L†L,rho}/2`. The two drain choices are a
business rule of the physical experiment, so the implementation exposes them
as one explicit configuration value rather than scattering special cases.

## EQ004 — one-way eigenstate rate and sum rule

Let `w_k=|<cav|psi_k>|^2`. Since

```text
<psi_k|cav><i|psi_l>
```

factorizes, summing the squared matrix element over sites gives

```text
sum_i |<psi_k|cav><i|psi_l>|^2
  = w_k * sum_i |<i|psi_l>|^2
  = w_k * (1-w_l).
```

Therefore `W[k<-l]=gamma_rec*w_k*(1-w_l)`. For an ideal dark state `w_l=0`,
and for any dark destination `w_k=0`, so inflow to the dark sector is exactly
zero. Completeness gives `sum_k w_k=1`; hence the total escape rate from every
ideal dark state is exactly `gamma_rec`, independently of N. The case tests
this identity for several N and also checks the symmetry of the dephasing rate
matrix.

## EQ005 — lumped rescue dynamics

With a cavity drain the dark sector has no direct drain overlap. In the pure
rescue limit,

```text
dp_D/dt = -gamma_rec p_D,
p_D(t) = p_D(0) exp(-gamma_rec t).
```

The bright-to-sink cascade has two decay poles, `Gamma_B` and `gamma_rec`, so
the cumulative sink population is the SM Eq. (S16) two-exponential form. The
full simulation does not use the lumped approximation; it uses the exact
Lindblad equation and treats the exponential as an independent sanity check.

## EQ006 — column-vectorized Liouvillian

For column stacking, `vec(A rho B)=(B^T tensor A)vec(rho)`. Applying this to the
commutator and every dissipator gives SM Eq. (S19):

```text
L = -i (I tensor H - H^T tensor I)
    + sum_j [L_j* tensor L_j
      - 1/2 (I tensor L_j†L_j + (L_j†L_j)^T tensor I)].
```

The paper exponentiates a dense matrix. The case constructs the identical
sparse matrix and applies its exponential action with `expm_multiply`. A test
compares it against dense `scipy.linalg.expm` for a small system.

## EQ007 — manifold observables

Diagonalize the system Hamiltonian without the sink, sort eigenstates by
photonic weight, and define the two largest-weight eigenstates as bright. The
remaining `N-1` states are dark, exactly as SM Appendix E. Embedded projectors
give

```text
p_B=Tr(P_B rho), p_D=Tr(P_D rho),
p_cav=rho[cav,cav], p_S=rho[S,S].
```

`p_cav` is a diagnostic overlap inside the bright sector and is not added to
`p_B+p_D`; the invariant is `p_B+p_D+p_S=1` up to numerical tolerance.
