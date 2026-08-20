# Derivation

## Model to matrix

The paper studies spinless fermions at half filling on a periodic chain,

$$
H=\sum_i\left[w_i n_i+V(n_i-\tfrac12)(n_{i+1}-\tfrac12)
+t(c_i^\dagger c_{i+1}+h.c.)+t'(c_i^\dagger c_{i+2}+h.c.)\right],
$$

with `V=2` and `t=t'=1`.  The implementation enumerates every bit string with
`L/2` occupied sites.  Diagonal terms are accumulated directly.  A hop is
allowed only when source and destination occupations differ; its sign is
`(-1)^m`, where `m` is the number of occupied sites crossed in canonical site
order.  Periodic nearest- and next-nearest-neighbour hops therefore receive the
same fermionic parity treatment as interior hops.  The resulting matrix is
real symmetric and is diagonalized in full, not by a low-energy approximation.

## Disorder ensemble

For each sample, independent standard normal values `x_i` are generated and
conditioned exactly as stated in the paper:

$$
w_i=W\,x_i/\sqrt{L^{-1}\sum_i x_i^2}.
$$

Thus each finite sample, rather than only the ensemble, has mean-square
disorder `W^2`.  Deterministic seed derivation makes every `(L,W,sample_id)` an
immutable work unit and prevents overlap across shards.

## Spectral observable

For sorted eigenenergies `E_n`, define `delta_n=E_{n+1}-E_n` and

$$
r_n=\frac{\min(\delta_n,\delta_{n-1})}
          {\max(\delta_n,\delta_{n-1})}.
$$

All interior spacings of every full spectrum are used.  The Poisson reference
is `P(r)=2/(1+r)^2`, with exact mean `2 ln 2 - 1`.  The GOE reference is built
from independently sampled real symmetric matrices.  Neither paper pixels nor
digitized source curves enter these calculations.

## Finite-size crossings

The disorder mean `r(W,L)` is computed from generated spectra.  Adjacent-size
crossings are found from sign changes of `r(W,L_a)-r(W,L_b)` and linearly
interpolated.  When reduced sampling gives no sign change, the nearest approach
is reported explicitly rather than relabelled as a crossing.  This distinction
is preserved in `outputs/data/crossing_drift.csv`.
