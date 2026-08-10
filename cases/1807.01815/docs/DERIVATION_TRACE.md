# Derivation Trace

## 1. Core object and invariant

The core object is a periodic constrained spin chain. A product configuration
is a word `n_0 ... n_(L-1)`, with `n_i` in `0,...,2s`, subject to the invariant
that two neighbouring occupations cannot both be nonzero. The projector in
main Eq. (1) enforces exactly this invariant. Within the allowed basis, a local
spin changes only by one unit,

\[
\langle n+1|S^x|n\rangle=\frac12\sqrt{(2s-n)(n+1)},\qquad
\langle n-1|S^x|n\rangle=\frac12\sqrt{n(2s-n+1)}.
\]

A move is allowed only when both neighbours of the changed site are zero.
This gives a real symmetric sparse Hamiltonian without consulting author code.
The factor `1/2` is essential: it makes the s=1/2 revival period approximately
`2 pi x 1.51 / Omega`, rather than the convention used by an `X`-normalized PXP
Hamiltonian.

## 2. Exact dynamics in a translation-by-two basis

Every quench state and measured sublattice observable is invariant under a
two-site translation. Let an orbit under `T^2` be `alpha`, with `p_alpha`
distinct product configurations. The normalized state is

\[
|\alpha\rangle=p_\alpha^{-1/2}\sum_{x\in\alpha}|x\rangle.
\]

Suppose applying `H` to one representative of `alpha` gives total amplitude
`A_(beta<-alpha)` into configurations in orbit `beta`. Counting the same edges
from both orbit ends gives

\[
H_{\beta\alpha}=\sqrt{\frac{p_\alpha}{p_\beta}}
A_{\beta\leftarrow\alpha}.
\]

The reverse expression is equal, so Hermiticity is preserved. The all-zero
state and the alternating `Z2` state each have a one-element `T^2` orbit. Exact
time evolution uses a Krylov exponential of this reduced Hamiltonian. For a
site that begins in `|0>`, translation symmetry makes its expectation equal to
the diagonal orbit observable

\[
S^z_{\rm odd}=\frac{2}{L}\sum_{i\in\mathrm{odd}}(n_i-s).
\]

For entanglement, orbit amplitudes are expanded back to every constrained
product state with factor `1/sqrt(p_alpha)`. Grouping amplitudes with identical
environment occupations gives

\[
(\rho_A)_{a a'}=\sum_e \psi_{a,e}\psi^*_{a',e},\qquad
S_A=-\sum_j\lambda_j\log_2\lambda_j.
\]

The trace, positivity, and `S_A(0)=0` are executable gates.

### Paper-scale pair blocking

The spin-half constraint permits only `|00>`, `|01>`, and `|10>` inside each
pair of physical sites. Let `X_L` (`X_R`) flip the left (right) spin within
this three-state basis, and let `P_L` (`P_R`) project that spin to zero. The
physical terms centred on the two sites adjacent to a block boundary combine
as

\[
h_{j,j+1}=X_{R,j}P_{L,j+1}+P_{R,j}X_{L,j+1}.
\]

Summing this bond term around 15 blocks includes each term of Eq. (1) exactly
once and preserves every inter-block constraint. It is therefore an exact
representation of the periodic L=30 Hamiltonian, not a tensor-network proxy.
The small-system test constructs both matrices independently and finds maximum
elementwise difference below `1e-14` on the constrained subspace.

A symmetric product formula over disjoint bond colours has local error
`O(dt^3)`. MPS truncation replaces an exact Schmidt spectrum only after each
gate, so the two independent controls are a halved `dt` lane and an enlarged
`chi` lane. Norm and energy conservation, forbidden adjacent-excitation
weight, and curve differences make both errors observable. The one-site
density matrix is obtained by first contracting one
three-state block and then tracing its unobserved physical spin; the six-site
density matrix is the contraction of three adjacent blocks.

## 3. Level statistics in the named symmetry sector

Equal-weight orbits of translations by one site and reflection are precisely
the trivial representation of the dihedral group: momentum zero and inversion
even. The same orbit-edge formula builds the exact block. After dense
diagonalization, sorted gaps `s_n=E_(n+1)-E_n` give

\[
r=\left\langle\frac{\min(s_n,s_{n-1})}
{\max(s_n,s_{n-1})}\right\rangle.
\]

Only numerical zero gaps below a disclosed tolerance are removed. `0<=r<=1`
is automatic. The Poisson and GOE anchors are approximately 0.386 and 0.536.
The paper does not print the size list behind Fig. 2(a), and the largest dense
blocks shown in the plot exceed the 16 GiB local budget; this target therefore
remains reduced-scale.

## 4. Variational MPS and tangent vectors

For a local lowest-weight spin state, direct expansion of a rotation about x
gives

\[
\langle n|e^{-i\theta S^x}|0\rangle=(-i)^n
\sqrt{\binom{2s}{n}}\cos^{2s-n}(\theta/2)\sin^n(\theta/2).
\]

Inserting these coefficients into the paper's two-by-two MPS produces the
amplitude of every valid configuration. Both the state and its collective odd
and even derivatives are evaluated by differentiating the matrix product.
After explicit finite-ring normalization,

\[
|\partial_\mu\psi\rangle=\frac{|\partial_\mu\Phi\rangle}{\|\Phi\|}
-\frac{|\Phi\rangle\,\mathrm{Re}\langle\Phi|\partial_\mu\Phi\rangle}
{\|\Phi\|^3}.
\]

This provides a direct check of Supplement I's thermodynamic normalization and
avoids relying on a possibly mis-copied closed expression for `H^2`.

## 5. TDVP flow and leakage

The Gram projection of `-iH|psi>` onto the two tangent vectors produces main
Eq. (4):

\[
\dot\theta_e=f(\theta_e,\theta_o),\qquad
\dot\theta_o=f(\theta_o,\theta_e),
\]

\[
f(x,y)=\Omega\left[1-c_x^{4s-2}+c_x^{4s-2}c_y^{2s}
+2s\sin(x/2)c_x^{6s-1}\tan(y/2)\right],
\quad c_x=\cos(x/2).
\]

The physical accuracy is evaluated from the definition rather than inferred
from the plotted colour:

\[
\gamma=\frac1{\sqrt L}\left\|iH|\psi\rangle+
\dot\theta_e|\partial_e\psi\rangle+
\dot\theta_o|\partial_o\psi\rangle\right\|.
\]

At either Neel product point, the allowed Hamiltonian action is exactly the
collective tangent, so `gamma` tends to zero. Increasing the finite MPS ring
checks convergence to the thermodynamic heat map. Coordinate singularities at
equivalent angle charts are crossed by a chart change; they are not regularized
into a different physical flow.

## 6. Deformed model

For s=1/2 the supplemental perturbation changes each allowed flip by the two
next-nearest `S^z` values. Direct algebra of the printed flow shows that at
`h=0`

\[
\sec(y/2)[\cos^2(y/2)+\cos^2(x/2)\sin(x/2)\sin(y/2)]
\]

is exactly the s=1/2 specialization of `f(x,y)`. Thus Fig. S1 has a strict
undeformed cross-check. For Fig. S2, the supplement does not provide a closed
formula for the deformed residual. The implementation therefore builds the
deformed Hamiltonian itself and evaluates the same MPS residual norm around
the closed orbit. A separate Gram projection of this matrix Hamiltonian agrees
with the printed deformed flow within `3.9e-4` at `L=12`, so the Hamiltonian and
flow implementations cross-check one another before the residual is used.

The resulting Fig. S2 curves converge from `L=10` to `L=14` within
`1.4e-7`, but the error minimum lies at `h/Omega=0.07` and the fluctuation keeps
decreasing through `h/Omega=0.08`; the printed minimum near `0.045` is not
obtained. Because the supplement omits the deformed residual construction and
numerical orbit-integral procedure, protocol-v2 records
`parameter_ambiguity`, not a curve silently fitted to source pixels.
`paper_error_candidate` remains ineligible because `paper_exact` and
`fresh_independent_review` fail; the other three hard gates pass.

## 7. Non-fitted physical anchors

The constrained infinite-temperature magnetization is

\[
\langle S_i^z\rangle_\infty=-s\frac{-1+4s+\sqrt{1+8s}}
{1+8s+\sqrt{1+8s}},
\]

giving `-0.2236068`, `-0.5`, and approximately `-1.05317` for
`s=1/2,1,2`. The one-site random-state entropy at s=1/2 is approximately
`0.8505`. These values are validation targets, never fit parameters.

## Equation-to-code map

| Card | Planned implementation | Executable check |
| --- | --- | --- |
| EQ-H, MTH-T2, MTH-DIH | `src/scar_tdvp/constrained.py` | small full-basis equality, Hermiticity, norm conservation |
| EQ-H, EQ-ENT, MTH-BLOCK-TDMRG | `src/scar_tdvp/fig2_tdmrg.py` | exact block mapping, dense-vs-MPS time evolution, product entropy, norm/energy/refinement and resume checks |
| EQ-MPS, EQ-GAMMA | `src/scar_tdvp/tdvp.py` | MPS norm, tangent orthogonality, product-point residual |
| EQ-FLOW, EQ-DEF-H, EQ-DEF-FLOW | `src/scar_tdvp/tdvp.py` | h=0 identity, direct Hamiltonian-to-flow projection, orbit period, chart continuity |
| EQ-R, EQ-ENT, EQ-THERM | `src/scar_tdvp/constrained.py` | bounds, density-matrix identities, analytic thermal values |
