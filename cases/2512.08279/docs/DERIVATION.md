# Derivation

## 1. GKSL generator and Choi convention

The implementation uses

\[
\operatorname{vec}(ABC)=(A\otimes C^T)\operatorname{vec}(B).
\]

For Hamiltonian \(H\) and jump operators \(L_k\),

\[
\mathbf L=-i(H\otimes I-I\otimes H^T)
+\sum_k\left[
L_k\otimes\bar L_k
-\frac12L_k^\dagger L_k\otimes I
-\frac12I\otimes(L_k^\dagger L_k)^T
\right].
\]

The channel is \(K(t)=e^{t\mathbf L}\). Its unnormalized Choi matrix is the
index reshuffling

\[
J(\mathcal E_t)
=\sum_{ijab}K_{ab,ij}(t)
|i\rangle\langle j|\otimes|a\rangle\langle b|.
\]

For a trace-preserving qubit channel,
\(\operatorname{tr}_{\rm out}J=I_2\), and the normalized program state is
\(\pi_t=J(\mathcal E_t)/2\).

## 2. Exact SWAP-dephasing semigroup

The first example has

\[
\mathcal L=i\,\mathrm{ad}_S+\lambda(\mathcal D_{\mathbb B}-\mathcal I).
\]

SWAP is diagonal in the Bell-adapted symmetric/antisymmetric basis, while
\(\mathcal D_{\mathbb B}\) dephases in the same basis. Therefore

\[
[\mathrm{ad}_S,\mathcal D_{\mathbb B}]=0,
\qquad
\mathcal D_{\mathbb B}^2=\mathcal D_{\mathbb B},
\]

and

\[
e^{t\mathcal L}
=e^{-\lambda t}e^{it\,\mathrm{ad}_S}
+(1-e^{-\lambda t})\mathcal D_{\mathbb B}.
\]

Since

\[
|01\rangle=\frac{|\Psi_+\rangle+|\Psi_-\rangle}{\sqrt2},
\]

the coherent return probability is \(\cos^2t\), whereas complete Bell
dephasing gives \(1/2\). Thus

\[
f(t)=\frac12\left(1+e^{-\lambda t}\cos2t\right).
\]

The paper uses \(\lambda=0.5\).

## 3. Fixed HPTP processor

Write \(S=\Pi_+-\Pi_-\) and define

\[
\mathcal M(X)=\frac{I_2}{2}\operatorname{tr}X+X-\Delta(X),
\]

\[
V=\Pi_+\otimes\langle0|+\Pi_-\otimes\langle1|,
\qquad
\mathcal P(X)=2V(\mathcal I\otimes\mathcal M)(X)V^\dagger .
\]

For

\[
|\pi_t\rangle=
\frac{e^{it}|0\rangle+e^{-it}|1\rangle}{\sqrt2},
\]

the off-diagonal program coherences produce the relative SWAP phase, so

\[
\mathcal P(\rho\otimes|\pi_t\rangle\langle\pi_t|)
=e^{itS}\rho e^{-itS}.
\]

The map is Hermiticity and trace preserving but need not be completely
positive. An independent signed-channel SDP gives

\[
\mathcal P=p_+\mathcal E_+-p_-\mathcal E_-,
\quad
p_+=1.5,\quad p_-=0.5,\quad \kappa=p_++p_-=2.
\]

Sampling \(\mathcal E_+\) and \(\mathcal E_-\) with probabilities
\(p_+/\kappa\) and \(p_-/\kappa\), and attaching signs \(+\kappa\) and
\(-\kappa\), yields an unbiased physical estimator.

## 4. Error-tolerant programming cost

For one program copy, a fixed retrieval Choi matrix \(J^P\) must satisfy,
for every program state \(\pi_t\),

\[
J(\widetilde{\mathcal E}_t)
=\operatorname{tr}_{P}
\left[J^P(I\otimes\pi_t^T\otimes I)\right].
\]

The retrieval is decomposed as \(J^P=J_+-J_-\), where each branch is
subnormalized CPTP:

\[
\operatorname{tr}_{\rm out}J_\pm=p_\pm I,
\qquad J_\pm\succeq0,
\qquad p_+-p_-=1.
\]

The operational overhead is

\[
\kappa_\epsilon=\min(p_++p_-),
\qquad
\gamma_\epsilon=\log_2\kappa_\epsilon.
\]

The half-diamond error constraint is represented by the
Hermiticity-preserving Watrous SDP:

\[
Z_t\pm J(\widetilde{\mathcal E}_t-\mathcal E_t)\succeq0,
\qquad
\operatorname{tr}_{\rm out}Z_t\preceq2\epsilon I.
\]

The paper's two models use

\[
L_0=\sqrt{0.1}|0\rangle\langle1|,
\qquad H=0\ \text{or}\ Z,
\]

with \(\epsilon=0,0.005,\ldots,0.2\).

## 5. Full-grid certificate

The released script actually iterates 1000 times
\(t=0,0.01,\ldots,9.99\). The reproduction optimizes a deterministic
101-point active subset, which gives a lower bound. The resulting map is then
certified at every omitted time using a feasible diamond-norm upper bound
\(Z=|J(\Delta_t)|\); inconclusive points are solved by batched exact Watrous
SDPs.

Because the same candidate is feasible on the complete 1000-point domain, its
objective is also a full-grid upper bound. The lower and upper bounds therefore
close within the declared solver tolerance. The nominal \(t=10\) endpoint is
checked separately for every solution.

The implementation is in `code/src/programmable_lindbladian.py`; public run
entry points are in `code/scripts/`.
