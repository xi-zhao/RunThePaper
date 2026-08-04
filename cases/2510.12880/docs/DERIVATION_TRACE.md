# Derivation Trace

## Formula Lane Rule

The numerical targets remain closed until every formula below has both a source
trace and an independent algebraic check. The overlap code must implement these
cards, not infer a Hamiltonian or MPS from the appearance of Fig. 5.

## EQC001 — Spin-1 and Cartesian-basis conventions

The supplement uses the standard \(S_z\) basis,
\[
S^x=\frac{1}{\sqrt2}
\begin{pmatrix}0&1&0\\1&0&1\\0&1&0\end{pmatrix},\quad
S^y=\frac{1}{\sqrt2}
\begin{pmatrix}0&-i&0\\i&0&-i\\0&i&0\end{pmatrix},\quad
S^z=\operatorname{diag}(1,0,-1).
\]
Since a spin-1 component has eigenvalues \(-1,0,+1\),
\[
e^{i\pi S^\alpha}=I-2(S^\alpha)^2.
\]

For block diagonalization it is better to use the three zero-eigenvalue
states
\[
|x\rangle=\frac{|+1\rangle-|-1\rangle}{\sqrt2},\qquad
|y\rangle=\frac{|+1\rangle+|-1\rangle}{\sqrt2},\qquad
|z\rangle=|0\rangle.
\]
Direct multiplication gives
\[
R_x=e^{i\pi S^x}=\operatorname{diag}(+1,-1,-1),\qquad
R_y=e^{i\pi S^y}=\operatorname{diag}(-1,+1,-1)
\]
in the ordered basis \((|x\rangle,|y\rangle,|z\rangle)\).

This is the key simplification: all bond conserved quantities become diagonal
sign constraints on product configurations.

## EQC002 — Hamiltonian and exact \(w\) sectors

With bond \(j\) connecting sites \(j\) and \(j+1\bmod N\), choose X character
for even \(j\) and Y character for odd \(j\):
\[
H_\theta=\sum_{j\ {\rm even}}\left[
K S_j^xS_{j+1}^x+Q(S_j^xS_{j+1}^x)^2\right]
+\sum_{j\ {\rm odd}}\left[
K S_j^yS_{j+1}^y+Q(S_j^yS_{j+1}^y)^2\right],
\]
\[
K=\cos\theta,\qquad Q=\sin\theta.
\]
The commuting bond operators are
\[
W_j=\begin{cases}
R_{y,j}R_{y,j+1},&j\ {\rm even}\quad(\text{X bond}),\\
R_{x,j}R_{x,j+1},&j\ {\rm odd}\quad(\text{Y bond}).
\end{cases}
\]

The main-source line for \(W_{2j+1}\) omits \(\pi\) from its second
exponential. Taking that factor literally would invalidate the immediately
following claims \(W_j^2=1\) and \(w_j=\pm1\). The supplement consistently uses
two \(\pi\) rotations, so the executable expression above is the uniquely
consistent reading.

Why do the \(W_j\) commute with \(H\)? A \(\pi\) rotation about a perpendicular
axis changes \(S^\alpha\to-S^\alpha\) on both ends of its reference bond, so
their product is unchanged. On adjacent bonds, either the relevant component is
unchanged or two sign changes again cancel. Integer-spin \(\pi\) rotations about
orthogonal axes commute, so neighboring \(W\)'s commute as well.

For a Cartesian product configuration
\(\mathbf a=(a_0,\ldots,a_{N-1})\), define
\[
r_x(x,y,z)=(+1,-1,-1),\qquad
r_y(x,y,z)=(-1,+1,-1).
\]
Then \(\mathbf a\) lies in sector \(\mathbf w\) exactly when
\[
r_{\eta_j}(a_j)r_{\eta_j}(a_{j+1})=w_j,\qquad
\eta_j=\begin{cases}y,&j\text{ even}\\x,&j\text{ odd}.\end{cases}
\]
Restricting the Hamiltonian to product states satisfying these constraints is
an exact symmetry reduction, not an approximation.

## EQC003 — Projector identity at \(\theta=\pi/4\)

Let \(A_\alpha=S_i^\alpha S_j^\alpha\). Its eigenvalues are
\(-1,0,+1\). Therefore
\[
p(A_\alpha)=\frac12(A_\alpha+A_\alpha^2)
\]
has eigenvalues \(0,0,1\), respectively. The \(+1\) eigenspace of
\(A_\alpha\) contains precisely
\(|+1_\alpha,+1_\alpha\rangle\) and
\(|-1_\alpha,-1_\alpha\rangle\), i.e. total component \(\pm2\). Hence
\[
P_{S_i^\alpha+S_j^\alpha=\pm2}
=\frac12\left[S_i^\alpha S_j^\alpha+
(S_i^\alpha S_j^\alpha)^2\right].
\]
At \(K=Q=1/\sqrt2\),
\[
H_{\pi/4}=\sqrt2\sum_jP_j\ge0.
\]
The exact ground-state problem is thus a common-kernel problem.

## EQC004 — Why the fractionalized states have zero energy

Write each physical spin as two symmetrized spin-\(\tfrac12\) objects:
\[
S_j^\alpha=\sigma_{j,L}^\alpha+\sigma_{j,R}^\alpha.
\]
On an X bond, put the two central spinons in either the singlet or \(t_x\);
both have zero total x component. On a Y bond, use the singlet or \(t_y\).
For an \(\alpha\) bond,
\[
S_j^\alpha+S_{j+1}^\alpha
=\sigma_{j,L}^\alpha+
\underbrace{\left(\sigma_{j,R}^\alpha+
\sigma_{j+1,L}^\alpha\right)}_{0}
+\sigma_{j+1,R}^\alpha.
\]
The two remaining spin-\(\tfrac12\) objects can sum only to
\(-1,0,+1\), never \(\pm2\). Every bond projector therefore annihilates the
state. The physical spin-1 projection commutes with the rotations used in this
argument, so on-site symmetrization does not spoil it.

There are two bond choices on each of \(N\) periodic bonds, giving \(2^N\)
fractionalized wavefunctions before orthogonalization.

## EQC005 — Conserved rotations become cluster stabilizers

Use \(\chi_k=\uparrow\) for a singlet and \(\chi_k=\downarrow\) for the
appropriate triplet. The supplement explicitly enumerates the local action:
\[
W_k|\chi_1,\ldots,\chi_N\rangle
=g(\chi_k)
|\ldots,\bar\chi_{k-1},\chi_k,\bar\chi_{k+1},\ldots\rangle,
\]
\[
g(\uparrow)=+1,\qquad g(\downarrow)=-1.
\]
In the bond-label qubit space, neighbor flips are \(\sigma^x\), while the
central sign is \(\sigma^z\):
\[
W_k\longleftrightarrow
\sigma^x_{k-1}\sigma^z_k\sigma^x_{k+1}.
\]
Selecting a desired eigenvalue string gives the generalized cluster
Hamiltonian
\[
H_{\mathbf w}=-\sum_k w_k
\sigma^x_{k-1}\sigma^z_k\sigma^x_{k+1}.
\]
Its ground state supplies the coefficients that combine nonorthogonal
fractionalized states into a physical state with definite \(\mathbf w\).

## EQC006 — Cluster-state MPS

For \(w=+1\), the source gives
\[
A^\uparrow_+=\frac1{\sqrt2}
\begin{pmatrix}1&1\\1&-1\end{pmatrix},\qquad
A^\downarrow_+=\frac1{\sqrt2}
\begin{pmatrix}1&1\\-1&1\end{pmatrix}.
\]
A local \(\pi\) rotation about x flips the bond-label basis
\(\uparrow\leftrightarrow\downarrow\) and changes the corresponding stabilizer
sign. Therefore
\[
A^\uparrow_-=A^\downarrow_+,\qquad
A^\downarrow_-=A^\uparrow_+.
\]
This is the exact coefficient MPS for an arbitrary \(w\) string.

## EQC007 — Physical bond-dimension-four MPS

The fractionalized bond matrices are
\[
B^\uparrow_X=B^\uparrow_Y=
\frac1{\sqrt2}\begin{pmatrix}0&1\\-1&0\end{pmatrix},
\]
\[
B^\downarrow_X=
\frac1{\sqrt2}\begin{pmatrix}1&0\\0&-1\end{pmatrix},\qquad
B^\downarrow_Y=\frac{i}{\sqrt2}I.
\]
The spin-1 symmetrization matrices are
\[
M^{+1}=\begin{pmatrix}1&0\\0&0\end{pmatrix},\quad
M^{-1}=\begin{pmatrix}0&0\\0&1\end{pmatrix},\quad
M^0=\frac1{\sqrt2}\begin{pmatrix}0&1\\1&0\end{pmatrix}.
\]
Contracting the fractionalized and cluster MPSs gives
\[
C_{\lambda,w}^{s}=
\sum_{\chi=\uparrow,\downarrow}
\left(M^sB_\lambda^\chi\right)\otimes A_w^\chi,
\qquad \lambda=X,Y.
\]
The unnormalized physical amplitude is
\[
\Psi_{\mathbf w}(s_0,\ldots,s_{N-1})
=\operatorname{Tr}\prod_{j=0}^{N-1}
C_{\lambda_j,w_j}^{s_j},
\qquad
\lambda_j=\begin{cases}X,&j\text{ even}\\Y,&j\text{ odd}.\end{cases}
\]

This derivation is preferable to copying the long matrix list. In the
supplement, the two lines labeled \(B^{0,\chi}=M^{+1}B^\chi\) must instead use
\(M^0B^\chi\); the printed resulting matrices and the earlier definition of
\(M^0\) confirm the correction.

For exact diagonalization in the Cartesian basis, transform the physical leg:
\[
C^x=\frac{C^{+1}-C^{-1}}{\sqrt2},\qquad
C^y=\frac{C^{+1}+C^{-1}}{\sqrt2},\qquad
C^z=C^0.
\]
The state vector is evaluated only on configurations in its exact \(w\) sector
and then normalized. Its norm may equivalently be computed from the transfer
matrix printed in the supplement.

## EQC008 — Ground-state overlap

For the normalized uniform-\(+\) MPS and the normalized lowest eigenvector in
the same sector, the plotted quantity is
\[
F_{\rm GS}(N,\theta)=
\left|\langle\psi_0(N,\theta)|\Psi_{+\cdots+}\rangle\right|^2.
\]
The caption only says “overlap,” but the visible points resolve the convention:
at \(\theta=0,N=12\), the independently derived amplitude is \(0.90043\);
its square is \(0.81077\), matching the plotted point near \(0.81\). The same
check holds for every visible curve. Cauchy-Schwarz gives
\(0\le F_{\rm GS}\le1\). At \(\theta=\pi/4\), the uniform-\(+\) sector
contains the corresponding exact zero mode, so the fidelity is one.

## EQC009 — First-excited-subspace overlap

A degenerate eigenspace has no preferred eigenvector basis, so the
basis-independent definition is
\[
F_{\rm FE}(N,\theta)=
\langle\Psi_{\rm 1flip}|P_{\rm FE}|\Psi_{\rm 1flip}\rangle.
\]
The Hamiltonian commutes with every \(W_j\). A one-flip MPS belongs to exactly
one sector, while the \(N\) reported first excited states occupy the \(N\)
one-flip sectors. Consequently,
\[
F_{\rm FE}=
\left|\langle\psi_{\rm min}^{(\rm matching\ 1flip)}
|\Psi_{\rm 1flip}\rangle\right|^2.
\]
This avoids arbitrary rotations returned by a degenerate full-space
eigensolver. The squared convention is again fixed by the plot: at
\(\theta=0,N=12\), \(0.89464^2=0.80039\), matching the source near \(0.80\).
Equality of the \(N\) one-flip sector energies is retained as a separate check.

## EQC010 — Product-state bounds

For \(\pi/4\le\theta\le\pi/2\),
\[
H_\theta=
\sqrt2\cos\theta\,H_{\pi/4}
+(\sin\theta-\cos\theta)H_{\pi/2}.
\]
Both operators on the right are positive semidefinite, and both coefficients
are nonnegative. The two alternating \(|x\rangle|y\rangle\) product states are
annihilated term by term, hence they are exact zero-energy ground states. The
unitary equivalence \(K\leftrightarrow-K\) extends the statement to
\(\pi/2\le\theta\le3\pi/4\).

At \(\theta=3\pi/2\),
\[
H=-\sum_b(S_i^\alpha S_j^\alpha)^2.
\]
Each bond term is bounded below by \(-1\). Because \(|z\rangle\) is a
\(+1\) eigenstate of both \((S^x)^2\) and \((S^y)^2\),
\(|z\rangle^{\otimes N}\) has energy \(-N\) and saturates the global bound.

## EQC011 — Why the exact degeneracy is \(2^N+1\)

The cluster MPS construction gives one nonzero state in every \(w\) sector.
Since distinct conserved-quantity strings are orthogonal, these \(2^N\) states
are linearly independent.

Both alternating product states have uniform \(w=-1\). The supplement proves
that their symmetric combination equals the fractionalized MPS already present
in that sector. Their antisymmetric combination is also a zero-energy state but
is orthogonal to the fractionalized set. Therefore
\[
\dim\ker H_{\pi/4}=2^N+1.
\]
The numerical control will count the nullity of every fixed-\(w\) block for
small even \(N\): one zero mode in every block and a second only in the uniform
\(-\) block.
