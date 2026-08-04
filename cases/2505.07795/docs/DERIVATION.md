# Derivation

For the permutation operator defined in the source, closing the input and
output indices leaves one free (d^{N_A})-dimensional index per cycle:

$$
\operatorname{Tr}\rho_{N_A,k}(g)=d^{N_A l(g)}.
$$

Thus weights (w_g=d^{m l(g)}) produce a unit-trace moment only after division
by

$$
Z=\sum_g d^{(N_A+m)l(g)}=(d^{N_A+m})^{\overline{k}}.
$$

This yields

$$
\alpha_\infty(g)=\frac{d^{m l(g)}}{(d^{N_A+m})^{\overline{k}}}.
$$

For (x=d^{-(t+1)}), the source's raw coefficient is

$$
a_g=d^{-mk}\left[w_g+xq_g+O(x^2)\right],
$$

where

$$
q_g=\sum_{i<j}\left[
d^{\frac m2(l(g)+l(gs_{ij})+1)}-d^{m l(gs_{ij})}\right].
$$

After trace normalization,

$$
\delta\alpha_g=\frac{q_g}{Z}-\frac{w_g}{Z^2}
\sum_hq_h d^{N_A l(h)}.
$$

It follows algebraically that
`sum_g delta_alpha_g d^(N_A l(g))=0`. The frozen expression instead projects
with weights (d^{m l(g)}) and omits the permutation-operator traces, so it
cannot satisfy the stated constraint in general.
