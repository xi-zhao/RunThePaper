# Derivation Trace

## From the Ising objective to the plotted blue bars

For an active signed Ising matrix `J`, Appendix C gives every level-1
correlation `M_uv` in closed form.  Summing `J_uv M_uv` separates the beta
dependence into

\[
E(\beta,\gamma)=A(\gamma)\sin^2(2\beta)
 +B(\gamma)\cos(2\beta)\sin(2\beta).
\]

Writing `t=2 beta` gives

\[
E=A/2-(A/2)\cos(2t)+(B/2)\sin(2t),
\]

so the global fixed-gamma maximum is

\[
E_\beta^{\max}(\gamma)=\frac{A+\sqrt{A^2+B^2}}{2}.
\]

The implementation searches one complete integer-coupling gamma period and
polishes the best basins continuously.  Dividing by an independently proved
zero-gap MILP optimum gives the QAOA ratio.

## From correlations to the red bars

At each RQAOA step the interacting pair with largest `|M_uv|` is selected and
the constraint `z_v=sign(M_uv) z_u` is imposed.  Substitution transforms

- `J_uv z_u z_v` into the constant `J_uv sign(M_uv)`;
- `J_vk z_v z_k` into `sign(M_uv) J_vk z_u z_k`;
- parallel interactions into their algebraic sum.

The same level-1 optimization is repeated on the reduced integer-weight Ising
model until the paper cutoff.  A zero-gap MILP solves the final `n_c` variables,
and the constraints are reversed to recover all original spins.  The code
checks the exact identity between the reconstructed energy and the reduced
energy plus every accumulated constant.

## Exact denominator

Represent a spin by `z_u=1-2b_u` and an edge disagreement by
`d_uv=b_u XOR b_v`.  Then `z_u z_v=1-2d_uv`.  Four standard linear
inequalities impose the XOR relation, so the signed Ising maximum is a binary
linear program.  The final data accepts only a solver-proved zero gap.

## Public-information boundary

All disclosed scientific parameters are exact.  Instance identity is not:
the paper omits graph edge lists, coupling arrays, and seeds.  A declared
master seed creates a new deterministic 16-instance ensemble at each paper
size.  Consequently the scientifically testable result is the distribution and
RQAOA advantage, not equality of each bar with the author's unpublished sample.
