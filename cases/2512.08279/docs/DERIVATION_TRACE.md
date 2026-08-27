# Derivation Trace

This case is intentionally derivation-first. The numerical layer may only
evaluate the objects derived here and indexed in `EQUATION_CARDS.json`. The
author's public MATLAB/notebook files are used to identify disclosed
parameters and source conventions; their stored matrices and plotted pixels
are not inputs to the independently generated evidence.

## 1. Vectorization and the GKSL matrix (`EQC001`)

The paper fixes

\[
\operatorname{vec}(|i\rangle\langle j|)=|i\rangle|j\rangle,
\qquad
\operatorname{vec}(ABC)=(A\otimes C^T)\operatorname{vec}(B).
\]

For the Hamiltonian part,

\[
\operatorname{vec}\!\left[-i(H\rho-\rho H)\right]
=-i(H\otimes I-I\otimes H^T)\operatorname{vec}(\rho).
\]

For one jump operator,

\[
\begin{aligned}
\operatorname{vec}(L\rho L^\dagger)
&=(L\otimes \overline L)\operatorname{vec}(\rho),\\
\operatorname{vec}\!\left[-\frac12 L^\dagger L\rho\right]
&=-\frac12(L^\dagger L\otimes I)\operatorname{vec}(\rho),\\
\operatorname{vec}\!\left[-\frac12\rho L^\dagger L\right]
&=-\frac12(I\otimes(L^\dagger L)^T)\operatorname{vec}(\rho).
\end{aligned}
\]

The ordering of the two loss terms can be exchanged in the written sum; the
matrix is

\[
\mathbf L=-i(H\otimes I-I\otimes H^T)
+\sum_k\left[
L_k\otimes\overline{L_k}
-\frac12L_k^\dagger L_k\otimes I
-\frac12I\otimes(L_k^\dagger L_k)^T
\right].
\]

The source writes the same matrix after choosing which vectorized factor is
listed first. A trace check is independent of that presentation. Using
\(\langle\!\langle I|\operatorname{vec}(X)=\operatorname{tr}X\),

\[
\langle\!\langle I|\mathbf L=0,
\]

because the gain term contributes
\(\operatorname{tr}(L\rho L^\dagger)=\operatorname{tr}(L^\dagger L\rho)\)
and the two anticommutator terms subtract the same quantity in halves.
Therefore \(e^{t\mathbf L}\) is trace preserving.

For the Fig. 3 jump
\(L=\sqrt{\Gamma}|0\rangle\langle1|\), \(H=0\), the master equation gives

\[
\rho_{11}(t)=e^{-\Gamma t}\rho_{11}(0),\qquad
\rho_{00}(t)=\rho_{00}(0)+(1-e^{-\Gamma t})\rho_{11}(0),
\]

\[
\rho_{01}(t)=e^{-\Gamma t/2}\rho_{01}(0).
\]

This analytic solution will be compared against the matrix exponential before
any optimization is attempted.

## 2. Choi reshuffling and normalization (`EQC002`)

Let \(K(t)=e^{t\mathbf L}\), with entries

\[
K_{ab,ij}(t)
=\langle a|\mathcal E_t(|i\rangle\langle j|)|b\rangle.
\]

The unnormalized Choi matrix is

\[
\begin{aligned}
J(\mathcal E_t)
&=\sum_{ij}|i\rangle\langle j|
  \otimes\mathcal E_t(|i\rangle\langle j|)\\
&=\sum_{ijab}K_{ab,ij}(t)
  |i\rangle\langle j|\otimes|a\rangle\langle b|.
\end{aligned}
\]

Thus this is a pure reshuffling of the four indices of \(K\), not another
matrix exponential. For the identity channel,

\[
J(\mathcal I)=\sum_{ij}|ii\rangle\langle jj|
=|I\rangle\!\rangle\langle\!\langle I|,
\]

so

\[
\operatorname{tr}J(\mathcal I)=d,\qquad
\operatorname{tr}_{\mathrm{out}}J(\mathcal I)=I_d.
\]

Every trace-preserving channel obeys the same output-partial-trace condition.
The program resource in Fig. 3 is therefore

\[
\pi_t=\frac{J(\mathcal E_t)}d,
\qquad \operatorname{tr}\pi_t=1.
\]

For a qubit, \(J(\mathcal E_t)\) is \(4\times4\), whereas \(\pi_t\) is a
normalized state on a four-level program register.

## 3. Why the SWAP-dephasing dynamics factor exactly (`EQC003`)

The first numerical example uses

\[
\mathcal L=i\,\operatorname{ad}_S+
\lambda(\mathcal D_{\mathbb B}-\mathcal I),
\qquad \operatorname{ad}_S=[S,\cdot].
\]

The SWAP operator is diagonal in a Bell-adapted basis: the antisymmetric
state \(|\Psi_-\rangle\) has eigenvalue \(-1\), while the three-dimensional
symmetric subspace has eigenvalue \(+1\). Bell-basis dephasing preserves the
diagonal blocks in precisely that eigenbasis. Hence

\[
[\operatorname{ad}_S,\mathcal D_{\mathbb B}]=0,
\qquad
\mathcal D_{\mathbb B}\circ e^{it\operatorname{ad}_S}
=\mathcal D_{\mathbb B}.
\]

Because \(\mathcal D_{\mathbb B}^n=\mathcal D_{\mathbb B}\) for \(n\ge1\),

\[
\begin{aligned}
e^{\lambda t(\mathcal D_{\mathbb B}-\mathcal I)}
&=e^{-\lambda t}e^{\lambda t\mathcal D_{\mathbb B}}\\
&=e^{-\lambda t}\mathcal I
 +(1-e^{-\lambda t})\mathcal D_{\mathbb B}.
\end{aligned}
\]

Multiplication by the commuting coherent evolution gives

\[
e^{t\mathcal L}
=e^{-\lambda t}e^{it\operatorname{ad}_S}
+(1-e^{-\lambda t})\mathcal D_{\mathbb B}.
\]

This relation supplies two independent numerical checks:

1. the analytic mixture must agree with direct exponentiation of the full
   \(16\times16\) Liouvillian;
2. the mixture weights must be nonnegative and sum to one for every
   \(t\ge0\).

## 4. Exact Fig. 2 overlap (`EQC004`)

Using

\[
|01\rangle=\frac{|\Psi_+\rangle+|\Psi_-\rangle}{\sqrt2},
\]

the coherent SWAP evolution produces a relative phase \(e^{2it}\) between
the symmetric and antisymmetric components. The return probability of the
coherent branch is

\[
\left|\frac{e^{it}+e^{-it}}2\right|^2=\cos^2t
=\frac12(1+\cos2t).
\]

Bell dephasing deletes the cross term and gives return probability \(1/2\).
Weighting the two branches from Sec. 3,

\[
\begin{aligned}
f(t)
&=e^{-\lambda t}\frac{1+\cos2t}{2}
 +(1-e^{-\lambda t})\frac12\\
&=\frac12\left(1+e^{-\lambda t}\cos2t\right).
\end{aligned}
\]

For the paper value \(\lambda=0.5\), \(f(0)=1\) and \(f(t)\to1/2\). This is
the exact line in Fig. 2; no curve digitization is needed to recover its
values.

## 5. Fixed HPTP processor for the coherent branch (`EQC005`)

Write the SWAP spectral decomposition as

\[
S=\Pi_+-\Pi_-,
\qquad \Pi_++\Pi_-=I.
\]

The two-level program map is

\[
\mathcal M(X)=\frac{I_2}{2}\operatorname{tr}X+X-\Delta(X),
\]

where \(\Delta\) removes program coherences. Let

\[
V=\Pi_+\otimes\langle0|+\Pi_-\otimes\langle1|,
\qquad
\mathcal P(X)=2V(\mathcal I\otimes\mathcal M)(X)V^\dagger.
\]

For a block operator
\(X=\sum_{a,b\in\{+,-\}}X_{ab}\otimes|a\rangle\langle b|\),
\(\mathcal M\) replaces each diagonal program block by
\(\tfrac12\operatorname{tr}_P X\) and preserves off-diagonal blocks. The
processor therefore acts as

\[
\mathcal P(X)
=\sum_a\Pi_a\operatorname{tr}_P(X)\Pi_a
+2\sum_{a\ne b}\Pi_a X_{ab}\Pi_b.
\]

Hermiticity is preserved term by term. For the trace,

\[
\operatorname{tr}\mathcal P(X)
=\sum_a\operatorname{tr}[\Pi_a\operatorname{tr}_P(X)]
=\operatorname{tr}X,
\]

because the off-diagonal projector blocks have zero trace. Thus
\(\mathcal P\) is HPTP.

Choose the normalized program state

\[
|\pi_t\rangle
=\frac{e^{it}|0\rangle+e^{-it}|1\rangle}{\sqrt2}.
\]

Its diagonal entries are \(1/2\), while its off-diagonal entries carry the
phase \(e^{\pm2it}/2\). Substitution gives

\[
\begin{aligned}
\mathcal P(\rho\otimes|\pi_t\rangle\langle\pi_t|)
&=\sum_{a,b=\pm}e^{i(s_a-s_b)t}\Pi_a\rho\Pi_b\\
&=e^{itS}\rho e^{-itS},
\end{aligned}
\]

where \(s_+=1\) and \(s_-=-1\). This constructs the coherent branch from the
paper's formulas alone. The reproduction will construct its Choi matrix from
matrix units rather than load the authors' `J1.mat` or `J2.mat`.

## 6. From an HPTP processor to an unbiased sampler (`EQC006`)

Any HPTP map can be decomposed into two physical channels:

\[
\mathcal P=p_+\mathcal E_+-p_-\mathcal E_-,
\qquad p_\pm\ge0.
\]

Because all three maps are trace preserving,

\[
p_+-p_-=1.
\]

The minimum total weight

\[
\kappa=p_++p_-=\|\mathcal P\|_\diamond
\]

is the sampling overhead for a trace-preserving Hermiticity-preserving map.
Sample branch \(\alpha\in\{+,-\}\) with

\[
q_\alpha=\frac{p_\alpha}{\kappa}
\]

and attach sign \(s_+=1,s_-=-1\). If a physical shot yields observable value
\(o_\alpha\), use

\[
\widehat o=\kappa s_\alpha o_\alpha.
\]

Then

\[
\mathbb E\widehat o
=\sum_\alpha q_\alpha\kappa s_\alpha o_\alpha
=p_+o_+-p_-o_-
=\operatorname{tr}[O\mathcal P(\rho)].
\]

This is the variance-minimizing branch distribution for a fixed signed
two-channel decomposition. The public notebook samples the two stored
subnormalized CP maps equally; the new implementation instead recovers the
weights independently and samples according to \(p_\pm/\kappa\).

For the full SWAP-dephasing channel, one first samples the physical outer
mixture in Sec. 3. Only a coherent-branch event requires the signed inner
estimator. The expected result remains exactly \(f(t)\).

## 7. Programming cost and the Fig. 3 ordinate (`EQC007`)

The paper defines

\[
\gamma_\epsilon(\pi_t,\mathcal L,T)
=\log_2\min_{\mathcal P}\left\{
\|\mathcal P\|_\diamond:
\frac12\|\mathcal P(\cdot\otimes\pi_t)-e^{t\mathcal L}\|_\diamond
\le\epsilon,\ \forall t\in[0,T]\right\}.
\]

Define the nonlogarithmic optimum

\[
\kappa_\epsilon=2^{\gamma_\epsilon}.
\]

These are not interchangeable labels:

- \(\gamma_\epsilon\) is the additive logarithmic resource monotone;
- \(\kappa_\epsilon\) is the multiplicative quasi-sampling overhead;
- the source Fig. 3 vertical axis is \(2^{\gamma_\epsilon(\mathcal L)}\);
- the disclosed scripts store `p1+p2`, so they also compute
  \(\kappa_\epsilon\), not \(\gamma_\epsilon\).

At the physical boundary \(\kappa=1\), \(\gamma=0\). Both quantities will be
stored in the generated dataset, but only \(\kappa_\epsilon\) will be plotted
against the source panel.

## 8. Program-state contraction (`EQC009`)

Order the retrieval-map input as \(S\otimes P\) and its output as \(S'\).
Expand its Choi matrix:

\[
J^{\mathcal P}_{SPS'}
=\sum_{ijab}
|i\rangle\langle j|_S\otimes|a\rangle\langle b|_P
\otimes\mathcal P(|i,a\rangle\langle j,b|).
\]

For a program state
\(\pi=\sum_{ab}\pi_{ab}|a\rangle\langle b|\), the effective channel has

\[
J[\mathcal P(\cdot\otimes\pi)]
=\sum_{ijab}\pi_{ab}|i\rangle\langle j|
\otimes\mathcal P(|i,a\rangle\langle j,b|).
\]

Now

\[
\operatorname{tr}\!\left[
|a\rangle\langle b|\,\pi^T
\right]=\pi_{ab},
\]

so the same result is

\[
J[\mathcal P(\cdot\otimes\pi)]
=\operatorname{tr}_P\left[
J^{\mathcal P}(I_S\otimes\pi^T\otimes I_{S'})
\right].
\]

The transpose is therefore dictated by the Choi convention, not a numerical
artifact. A normalization check follows immediately:

\[
\operatorname{tr}_{S'}J^{\mathcal P}=I_{SP},
\quad\operatorname{tr}\pi=1
\quad\Longrightarrow\quad
\operatorname{tr}_{S'}J[\mathcal P_\pi]=I_S.
\]

## 9. Hermiticity-preserving diamond norm SDP (`EQC010`)

The general Watrous/QETLAB primal for a map with Choi matrix \(J\) uses two
positive blocks. When \(J=J^\dagger\), swap symmetry permits their average to
be chosen equal. The remaining block constraint is

\[
\begin{pmatrix}
Z&-J\\
-J&Z
\end{pmatrix}\succeq0.
\]

A block Hadamard rotation diagonalizes it:

\[
\begin{pmatrix}
Z-J&0\\
0&Z+J
\end{pmatrix}\succeq0.
\]

Therefore

\[
\|\Phi\|_\diamond
=\min_{Z,\mu}\left\{
\mu:
Z-J(\Phi)\succeq0,
Z+J(\Phi)\succeq0,
\operatorname{tr}_{\mathrm{out}}Z\preceq\mu I
\right\}.
\]

The two first inequalities imply \(Z\succeq0\) after addition. For clarity
the implementation will still impose it explicitly.

The identity-channel check fixes the normalization. Choose
\(Z=J(\mathcal I)\); then

\[
Z-J(\mathcal I)=0,\qquad
Z+J(\mathcal I)\succeq0,\qquad
\operatorname{tr}_{\mathrm{out}}Z=I,
\]

so \(\|\mathcal I\|_\diamond\le1\). Trace preservation supplies the matching
lower bound, hence the optimum is one.

For the Fig. 3 error condition,

\[
\frac12\|\Delta\|_\diamond\le\epsilon,
\]

we can eliminate \(\mu\) and impose

\[
Z\pm J(\Delta)\succeq0,\qquad
\operatorname{tr}_{\mathrm{out}}Z\preceq2\epsilon I.
\]

This explicit factor of two is a mandatory unit test.

## 10. Finite-grid programming-cost SDP (`EQC008`)

For one qubit system and one Choi-state program copy:

- \(d_S=2\);
- \(d_P=d_S^2=4\);
- retrieval input dimension \(d_Sd_P=8\);
- retrieval output dimension \(2\);
- \(J^\mathcal P,J_\pm\) are \(16\times16\);
- every effective-channel difference and every \(Z_k\) is \(4\times4\).

At sampled times \(t_k\), define

\[
\pi_k=\frac{J(e^{t_k\mathcal L})}{2},
\qquad
\Delta J_k=
\operatorname{tr}_P\!\left[
J^\mathcal P(I_S\otimes\pi_k^T\otimes I_{S'})
\right]
-J(e^{t_k\mathcal L}).
\]

The finite-grid approximation solved in the public scripts is exactly

\[
\begin{aligned}
\kappa_\epsilon^{(N)}=\min\;&p_++p_-\\
\text{s.t. }&
J^\mathcal P=J_+-J_-,
\quad J_\pm\succeq0,\\
&\operatorname{tr}_{S'}J_\pm=p_\pm I_{SP},
\quad
\operatorname{tr}_{S'}J^\mathcal P=I_{SP},\\
&Z_k+\Delta J_k\succeq0,\quad
Z_k-\Delta J_k\succeq0,\quad Z_k\succeq0,\\
&\operatorname{tr}_{S'}Z_k\preceq2\epsilon I_S,
\qquad k=1,\ldots,N.
\end{aligned}
\]

The exact supplemental SDP is recovered at \(\epsilon=0\) with equality to
the target channel. The finite-\(\epsilon\) form follows from the main
definition plus Sec. 9 and matches the disclosed QETLAB constraints.

The equality

\[
\operatorname{tr}_{S'}(J_+-J_-)
=(p_+-p_-)I_{SP}=I_{SP}
\]

again gives \(p_+-p_-=1\), so the objective is a legitimate signed-channel
overhead.

## 11. Fig. 3 physical models and exact finite grids (`EQC011`)

Both curves use

\[
L_0=\sqrt{0.1}|0\rangle\langle1|.
\]

The blue branch has \(H=0\); the red branch has \(H=Z\). Since the
amplitude-damping dissipator is phase covariant around \(Z\), the red
channel has the same populations as the blue channel and

\[
\rho_{01}^{(Z)}(t)
=e^{-0.05t}e^{-2it}\rho_{01}(0).
\]

This analytic form is a second independent check of the Liouvillian and Choi
conventions.

The public scripts disclose

\[
T=10,\quad N=1000,\quad
\epsilon_\ell=0.005\ell,\quad\ell=0,\ldots,40,\quad
n_{\mathrm{Choi\ copies}}=1.
\]

They allocate MATLAB's vector

\[
0:T/N:T=(0,0.01,\ldots,10),
\]

which has 1001 entries, but loop only over `j=1:sample`. The actual
constraints therefore use

\[
t_k=0.01k,\qquad k=0,\ldots,999,
\]

ending at \(9.99\). The paper caption describes the intended interval as
\([0,10]\). We will preserve both facts:

1. the final source-matching run uses the disclosed 1000-point
   \(0,\ldots,9.99\) grid;
2. a separate sensitivity run includes \(t=10\) and reports whether the
   optimum changes beyond solver tolerance.

This is a source-disclosed discretization detail, not permission to tune
parameters against the image.

## 12. Base programmability contract (EQC013)

A single processor \(\mathcal P\) and a time-indexed family of normalized
program states \(\pi_t\) implement the interval family when

\[
\frac12\left\|\mathcal P(\,\cdot\otimes\pi_t)-e^{t\mathcal L}\right\|_\diamond
\le \epsilon,\qquad 0\le t\le T.
\]

At \(\epsilon=0\) this is an exact complete-basis channel identity. If
\(\mathcal P\) is CPTP, the protocol is quantum programmable; allowing an HPTP
processor yields quasiquantum programmability. The clean-room finite check
constructs one fixed controlled processor for two qubit channels, supplies
several diagonal program states, and verifies the retrieved convex map on all
four matrix units. It separately executes a signed HPTP combination. These
checks instantiate the definition; they do not prove a universal
programmability theorem.

## 13. Choi and compatible link conventions (EQC014)

With the normalized maximally entangled state

\[
\Phi_d=\frac1d\sum_{i,j}|ii\rangle\langle jj|,
\]

the paper uses the unnormalized Choi operator
\(J(\mathcal N)=d(\mathcal I\otimes\mathcal N)(\Phi_d)\). In explicit
indices, compatible composition is

\[
J(\mathcal F\circ\mathcal E)_{ic,jd}
=\sum_{a,b}J(\mathcal E)_{ia,jb}J(\mathcal F)_{ac,bd}.
\]

The isolated check assembles both sides independently and verifies the
identity on qubit channels. It also checks contraction-order commutativity for
a compatible commuting family and associativity for three maps. A fresh proof
audit still owns the general labelled-space compatibility statement.

## 14. HPTP implementability resource (EQC015)

For a trace-preserving Hermiticity-preserving map,

\[
\nu(\mathcal N)=\log_2\min_{\eta_\pm,\mathcal E_\pm}
\left\{\eta_++\eta_-:
\mathcal N=\eta_+\mathcal E_+-\eta_-\mathcal E_-,
\ \mathcal E_\pm\ {\rm CPTP}\right\}.
\]

The finite witness uses the signed Pauli map
\(\mathcal N=1.5\,\mathcal I-0.5\,\mathcal X\). Its two-channel
decomposition has overhead \(2\), and the normalized Choi trace norm gives the
same value. Tensor products multiply the overhead, while unitary pre/post
processing preserves it.

The supplement calls composition subadditive but prints an equality. The
clean-room witness composes \(\mathcal N\) with the CPTP map
\(\mathcal M=0.5\,\mathcal I+0.5\,\mathcal X\):

\[
\mathcal N\circ\mathcal M=\mathcal M,\qquad
\|\mathcal N\circ\mathcal M\|_\diamond=1
<2=\|\mathcal N\|_\diamond\|\mathcal M\|_\diamond.
\]

This is a finite falsification of a universal equality and support for
subadditivity. It remains an author-side discrepancy until a fresh reviewer
adjudicates the paper's intended claim.

## 15. Numerical authorization checklist

Before either target may run, the following must hold:

1. all fifteen equation cards pass source and independent-derivation checks;
2. `DERIVATION.md` is regenerated from the cards;
3. the target manifest declares the exact observable and parameter mapping;
4. the method cards name independent checks rather than author arrays;
5. the command is wrapped by `run_target.py`;
6. final execution uses the paper/source-exact physical parameters.

The first numerical stage is limited to convention tests and a measured small
SDP. The 41-by-1000 solve is not authorized until that small run supplies a
runtime and memory estimate.
