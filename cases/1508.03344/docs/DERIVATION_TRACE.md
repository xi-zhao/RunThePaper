# Derivation trace

## Floquet eigensystem

For a binary drive with stages `(H_a,t_a)` and `(H_b,t_b)`, chronological
evolution gives `U(T)=exp(-i H_b t_b) exp(-i H_a t_a)`. Quasienergies are the
principal phases of the unitary eigenvalues divided by the total period.

The Ising parity `P=prod_i sigma_i^z` commutes with every `z`, `zz` and
nearest-neighbor `xx` term. Restricting to one parity sector is therefore exact
and prevents the symmetry doublets from contaminating level statistics.

## Log-normal drive

If `log X ~ N(mu,1)`, then
`std(X)=sqrt((e-1)e^(2mu+1))`. The printed rule `omega=2W`, with
`W=max(std(J),std(h))`, fixes `T=pi/W`. The three drive intervals have
durations `T/4,T/2,T/4` and hopping multipliers `1,e,1`.

## Statistical and order observables

Sorted circular eigenphases define gaps `delta_n`; the ratio is
`min(delta_n,delta_n+1)/max(...)`. The SG susceptibility is the average of the
squared two-point expectations over all site pairs, eigenstates and disorder
samples.

A non-negative operator spectral function requires the Lehmann weight
`|<alpha|sigma_i^+|beta>|^2`. The literal printed unsquared matrix element is
generally complex and cannot yield the positive curves in Fig. 2(c); both
forms are retained for review.

## Source contradictions

Eq. (8), the numerical paragraph and the Fig. 2(d) caption specify mutually
incompatible duration statements. The primary reconstruction uses the
dimensionless couplings directly with `T1=1,T2=pi/2`, because the caption
explicitly fixes `T1` and the disorder intervals are expressed as `h_i T1`
and `J_i T2`. A normalized-total-period branch rescales the two durations while
preserving those dimensionless products. Neither branch is selected from
source pixels.
