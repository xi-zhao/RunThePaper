# Derivation Trace

1. Operator-Schmidt SVD gives left operators `S_n`; zero left discord is equivalent to their pairwise commutation, and rank greater than `d_A` is a witness.
2. Minimizing Hilbert-Schmidt distance over a measurement axis gives `D_G=(||x||^2+||T||^2-k_max)/4`. Direct dephasing minimization is an independent cross-check.
3. For Bell-diagonal states, positivity forms the printed tetrahedron and separability the `L1` octahedron. Zero discord lies on coordinate axes.
4. Substitution gives Bell vertices `1/2`, facet centers `1/18`, and the true octahedral maximum `1/16` at permutations of `(±1/2,±1/2,0)`.
5. The DQC1 block state yields control expectations `alpha Re Tr(U)/d` and `alpha Im Tr(U)/d`; its discord vanishes exactly when Hermitian and anti-Hermitian parts are linearly dependent.
6. For a multipartite state, permuting one subsystem to the left turns the problem into that subsystem versus the composite remainder. The same operator-Schmidt commutator theorem then applies independently to every subsystem. A local projective basis in dimension `d` has `d^2-d` real search directions, so a product-basis optimization has dimension `sum_j(d_j^2-d_j)`.
7. For fixed local projectors, projective dephasing is the Hilbert--Schmidt orthogonal projection onto the corresponding diagonal operator algebra. Therefore the nearest state in that fixed algebra is `Delta(rho)` itself, and the multipartite objective reduces to `||rho-Delta(rho)||_2^2`. Optimizing complex Givens coordinates over each `U(d_j)/U(1)^d_j` makes the paper's stated multipartite extension executable. Because the paper does not print a unique multipartite convention, simultaneous local dephasing is recorded as a reconstructed, explicitly testable choice.

Use this file for formula-heavy papers. Every implemented equation should map
back to a source equation or an explicit derivation step.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until its formula dependencies are traceable and
the formula gate is not closed.

## Equation Cards

### EQ001

- Source:
- Latex:
- Role:
- Derived from:
- Steps:
- Symbols:
- Numerical form:
- Code pointer:
- Status:
- Open questions:
