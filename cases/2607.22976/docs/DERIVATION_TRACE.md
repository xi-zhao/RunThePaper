# Derivation Trace

## Core model

The paper's numerical object is one single-band Laurent polynomial per domain,

`h_alpha(beta) = sum_d t[alpha,d] beta^d`.

For a homogeneous domain, the real-space row stencil
`(H psi)_x = sum_d t[alpha,d] psi_(x+d)` returns
`h_alpha(beta) psi_x` for `psi_x=beta^x`. This identity fixes the hopping
orientation used by the code. On a ring the index is periodic; on the opened
chain, terms crossing the `3|1` cut are omitted.

## DW001: winding mismatch and finite spectra

For fixed complex energy `E`, multiply `h_alpha(beta)-E` by `beta^s` and
count its roots inside the unit circle. The argument principle gives

`w_alpha(E) = n_inside - s_alpha`.

The interface invariant is `Delta_alpha=w_(alpha+1)-w_alpha`. The blue/red
regions of Fig. 2(a) are therefore computed from roots, independently of any
source image. Finite eigenvalues and right eigenvectors come from direct
diagonalization of the 186-site ring.

## DW002: constrained Ronkin minimum

If the ordered roots have `mu_m=log|beta_m|`, Jensen's formula gives

`R_alpha(mu;E) = log|a_-s| - s mu + sum_m max(0, mu-mu_m)`.

It is convex and piecewise linear. The ring constraint is
`sum_alpha r_alpha mu_alpha=0`. In three domains, a minimum occurs at an
intersection where at least two coordinates equal root breakpoints; the third
is fixed by the constraint. Enumerating all such intersections is exact for
this piecewise-linear problem and avoids optimizer-dependent tolerances.

## DW003: standing and traveling sectors

For root counts `(2,3,4)` the source derives

- `lambda_0 = r1*mu_11 + r2*mu_21 + r3*mu_32`;
- `lambda_1 = r1*mu_12 + r2*mu_22 + r3*mu_33`.

Case I requires an adjacent equal-modulus pair inside a maximal common-winding
sector and produces a standing wave. Case II requires `lambda_0=0` or
`lambda_1=0`; it balances one dominant mode from every domain and produces a
traveling wave. Finite-ring energies are classified by the smallest normalized
residual among these published conditions. No panel coordinate is digitized.

## DW004: flux winding

Each hopping is multiplied by the distributed phase in Eq. (12). The source
does not map the Laurent exponent to an oriented site label, so the code fixes
positive flux by `beta -> beta exp(i Phi/N)`; reversing every site label
reverses the reported sign of `W` without changing its nonzero support. The integer

`W(E_B) = Delta_Phi arg det[H(Phi)-E_B] / (2 pi)`

is evaluated from a closed flux mesh. Traveling branches shift with the
round-trip phase; standing branches are fixed by local equal-modulus pairs.

## DW005: density of states

The two independent potentials are

- `Phi_Ronkin(E)=min_mu R(mu;E)`;
- `Phi_diag(E)=mean_m log|E-epsilon_m|`.

Both are converted to density by the same central-difference Cartesian
Laplacian and the factor `1/(2 pi)`. Agreement is assessed by support overlap,
correlation, and normalized absolute error, not by reading the source heatmap.

## DW006: opened chain

Cutting the `3|1` interface removes the global round-trip sector. The remaining
thermodynamic spectrum is the union of the constituent OBC spectra, while the
finite opened-chain spectrum is computed from the same local stencil with the
cut enforced explicitly.

## Unreported choices

The figure source contains no code or data. The finite interface stencil,
representative Fig. 2 eigenstate indices, Fig. 3 reference energies, and DOS
grid are therefore documented configuration choices. They may affect visual
alignment but do not alter the tested topological and Ronkin identities.
