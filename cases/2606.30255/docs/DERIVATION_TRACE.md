# Derivation Trace

## Scope and convention

This trace was written after reading the complete ten-page paper. It derives
the four frozen theory targets without using the released coincidence counts,
measured markers, source-figure paths, or digitized source pixels as numerical
inputs.

The paper uses

\[
|m(x)\rangle=\sin x|H\rangle+\cos x|V\rangle ,
\]

where \(x\) is a polarization angle. Define Alice's directions as

\[
a=A,\qquad b=A+\phi,\qquad c=A+2\phi
\]

and Bob's as

\[
a'=B,\qquad b'=B+\phi,\qquad c'=B+2\phi .
\]

This convention immediately produces the paper's relative-angle statements:
when \(A=B\), the \(ab'\), \(bc'\), and \(ac'\) separations are
\(\phi,\phi,2\phi\); when \(B-A=-15^\circ\) and
\(\phi=30^\circ\), they are \(15^\circ,15^\circ,45^\circ\).

## 1. Classical Wigner bound

From the eight anti-correlated hidden-variable rows in Table I,

\[
P_{++}^{ab'}=p_3+p_4,\quad
P_{++}^{bc'}=p_2+p_6,\quad
P_{++}^{ac'}=p_2+p_4.
\]

Therefore

\[
W=P_{++}^{ab'}+P_{++}^{bc'}-P_{++}^{ac'}=p_3+p_6\geq0.
\]

The frozen figures test the quantum prediction for this same observable; they
do not attempt to close the perfect-anticorrelation loophole discussed by the
paper.

## 2. State and density matrix

With \(a_w=\sqrt w\), \(b_w=\sqrt{1-w}\), and the paper-fixed phase
\(\xi=\pi\), Eq. (18) becomes

\[
|\Psi(w)\rangle=a_w|HV\rangle-b_w|VH\rangle.
\]

Eq. (20) adds isotropic noise,

\[
\rho(w,v)=v|\Psi(w)\rangle\langle\Psi(w)|
          +\frac{1-v}{4}I_4.
\]

Independent checks:

- \(\langle\Psi|\Psi\rangle=w+(1-w)=1\);
- \(\operatorname{Tr}\rho=v+(1-v)=1\);
- the eigenvalues are \((1+3v)/4\) once and \((1-v)/4\) three
  times, so the four paper values \(0\leq v\leq1\) produce a positive
  semidefinite density matrix.

## 3. Born probability

For Alice angle \(x\) and Bob angle \(y\), the joint transmission projector is
\(|m(x)m(y)\rangle\langle m(x)m(y)|\). The pure-state amplitude is

\[
\begin{aligned}
\langle m(x)m(y)|\Psi(w)\rangle
 &=\sqrt w\,\sin x\cos y
   -\sqrt{1-w}\,\cos x\sin y .
\end{aligned}
\]

The independently derived scalar probability is consequently

\[
p_{++}(x,y;w,v)=v\left(
\sqrt w\,\sin x\cos y-\sqrt{1-w}\,\cos x\sin y
\right)^2+\frac{1-v}{4}.
\]

The implementation evaluates the full \(4\times4\) matrix trace
\(\operatorname{Tr}[\rho(\Pi_x\otimes\Pi_y)]\). The scalar expression above is
implemented separately as an analytic reference. Agreement between those two
paths is a scientific check, not circular reuse of one code path.

For \(w=1/2,v=1\), the expression reduces to

\[
p_{++}(x,y)=\frac12\sin^2(x-y),
\]

which is Eq. (9).

## 4. Wigner observable for the three-setting geometry

For arbitrary basis origins \(A,B\) and spacing \(\phi\),

\[
\begin{aligned}
P_{++}^{ab'} &= p_{++}(A,B+\phi),\\
P_{++}^{bc'} &= p_{++}(A+\phi,B+2\phi),\\
P_{++}^{ac'} &= p_{++}(A,B+2\phi),\\
W &=P_{++}^{ab'}+P_{++}^{bc'}-P_{++}^{ac'}.
\end{aligned}
\]

At the pure singlet and \(A=B\),

\[
W(\phi)=\sin^2\phi-\frac12\sin^2(2\phi).
\]

Thus \(W(30^\circ)=-1/8=-0.125\), the symmetric theoretical
violation limit used in Figures 3 and 4.

For \(B-A=-15^\circ\) with \(\phi=30^\circ\),

\[
W=\frac12\left[2\sin^2(15^\circ)-\sin^2(45^\circ)\right]
  =\frac{1-\sqrt3}{4}\approx-0.1830127,
\]

which is the asymmetric limit used in Figure 5.

## 5. Target-specific paper parameters

| Target | Scan | Fixed geometry | \(w\) | \(v\) | \(\xi\) | Ideal reference |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| T-FIG003 | \(\phi:0^\circ\ldots360^\circ\) | \(A=B=0^\circ\) | 0.50 | 0.98 | \(\pi\) | \(-0.125\) |
| T-FIG004 | \(\Theta:0^\circ\ldots360^\circ\) | \(A=B=\Theta,\phi=30^\circ\) | 0.36 | 0.99 | \(\pi\) | \(-0.125\) |
| T-FIG005A | \(B:0^\circ\ldots360^\circ\) | \(A=0^\circ,\phi=30^\circ\) | 0.35 | 0.89 | \(\pi\) | \((1-\sqrt3)/4\) |
| T-FIG005B | \(A:0^\circ\ldots360^\circ\) | \(B=0^\circ,\phi=30^\circ\) | 0.41 | 0.90 | \(\pi\) | \((1-\sqrt3)/4\) |

The \(0.25^\circ\) numerical grid used for rendering samples these analytic
curves densely. It changes neither the model nor any paper parameter.

## 6. Required independent checks

Each guarded target run must verify:

1. trace one, Hermiticity, and non-negative eigenvalues of \(\rho\);
2. projector normalization and \(0\leq p_{++}\leq1\);
3. matrix-trace Born probabilities against the separately evaluated scalar
   formula at every grid point;
4. \(W=P_{++}^{ab'}+P_{++}^{bc'}-P_{++}^{ac'}\);
5. \(180^\circ\) polarization periodicity;
6. target-specific extrema/limit identities and full visible theory-series
   coverage;
7. output provenance is `independent_numerics`.

## Formula status

All six dependencies in `EQUATION_CARDS.json` are `verified`. Numerical
execution remains closed until `check_formula_gate.py` passes and the generated
`DERIVATION.md` matches the current cards.
