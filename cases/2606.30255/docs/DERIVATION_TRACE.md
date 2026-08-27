# Derivation Trace

## Scope And Basis Convention

Only the theory curves in Figures 3-5 are generated. The two-qubit basis is
ordered as

\[
(|HH\rangle,|HV\rangle,|VH\rangle,|VV\rangle).
\]

Following Eq. (7), a transmitted polarization state is

\[
|\theta\rangle=\sin\theta|H\rangle+\cos\theta|V\rangle .
\]

This convention makes \(0^\circ\) the vertical state. Since
\(\sin^2\theta+\cos^2\theta=1\), the plus-outcome projector
\(\Pi_\theta=|\theta\rangle\langle\theta|\) is normalized and rank one.

## 1. Source State And Density Matrix

The fitted pure component is Eq. (18):

\[
|\Psi(w,\xi)\rangle
=\sqrt w|HV\rangle+e^{i\xi}\sqrt{1-w}|VH\rangle .
\]

The two basis states are orthogonal, so the norm is \(w+(1-w)=1\).
The paper fixes \(\xi=\pi\), giving

\[
|\Psi(w,\pi)\rangle
=\sqrt w|HV\rangle-\sqrt{1-w}|VH\rangle .
\]

At \(w=1/2\), this is the singlet. Equation (20) adds white noise:

\[
\rho=v|\Psi\rangle\langle\Psi|+\frac{1-v}{4}I_4.
\]

The eigenvalue along \(|\Psi\rangle\) is \((1+3v)/4\), and the other
three eigenvalues are \((1-v)/4\). Thus \(0\leq v\leq1\) guarantees
Hermiticity, positive semidefiniteness, and unit trace.

## 2. General Born Probability

For Alice angle \(\alpha\) and Bob angle \(\beta\), the joint ket is
\(|\alpha,\beta\rangle=|\alpha\rangle\otimes|\beta\rangle\). Born's rule is

\[
P_{++}(\alpha,\beta)
=\langle\alpha,\beta|\rho|\alpha,\beta\rangle.
\]

For \(\xi=\pi\), the pure-state amplitude is

\[
\langle\alpha,\beta|\Psi\rangle
=\sqrt w\sin\alpha\cos\beta
-\sqrt{1-w}\cos\alpha\sin\beta .
\]

The isotropic term contributes \(1/4\), because the joint ket is normalized.
Therefore the numerical scalar form is

\[
P_{++}(\alpha,\beta)
=v\left(\sqrt w\sin\alpha\cos\beta
-\sqrt{1-w}\cos\alpha\sin\beta\right)^2
+\frac{1-v}{4}.
\]

For \(w=1/2\), the sine subtraction identity reduces this to

\[
P_{++}(\alpha,\beta)
=\frac v2\sin^2(\alpha-\beta)+\frac{1-v}{4},
\]

and the ideal \(v=1\) limit is exactly paper Eq. (9).

## 3. Wigner Value

Equation (5) defines

\[
\mathcal W=P_{++}^{ab'}+P_{++}^{bc'}-P_{++}^{ac'}.
\]

Substituting the LHV identities in Eqs. (1)-(3) gives
\(\mathcal W=p_3+p_6\geq0\). The generated theory lane evaluates the same
linear combination using the mixed-state Born probabilities above.

## 4. Analytic Extremal Checks

For an ideal singlet with symmetric setting separations
\((\phi,\phi,2\phi)\),

\[
\mathcal W(\phi)=\sin^2\phi-\frac12\sin^2(2\phi).
\]

At \(\phi=\pi/6\),

\[
\mathcal W=\frac14-\frac12\frac34=-\frac18=-0.125.
\]

For the paper's asymmetric extremal separations
\((\pi/12,\pi/12,\pi/4)\),

\[
\mathcal W
=\frac12\left[2\sin^2\left(\frac{\pi}{12}\right)
-\sin^2\left(\frac{\pi}{4}\right)\right]
=\frac{1-\sqrt3}{4}\approx-0.1830127.
\]

These two exact values provide target-independent checks and define the
visible limit lines.

## 5. Scan Geometry

Figure 1 and Sections V.A-V.C define each local three-setting basis as

\[
(a,b,c)=(\theta_A,\theta_A+\phi,\theta_A+2\phi),
\]

\[
(a',b',c')=(\theta_B,\theta_B+\phi,\theta_B+2\phi).
\]

Only three cross-party pairs enter the Wigner value:

\[
(a,b')=(\theta_A,\theta_B+\phi),\quad
(b,c')=(\theta_A+\phi,\theta_B+2\phi),\quad
(a,c')=(\theta_A,\theta_B+2\phi).
\]

- Figure 3: \(\theta_A=\theta_B=0^\circ\), scan \(\phi\).
- Figure 4: \(\phi=30^\circ\), scan the plotted central setting
  \(\Theta\), with basis starts
  \(\theta_A=\theta_B=\Theta-\phi\). The official
  `starting_angle=0` probability row distinguishes this coordinate convention
  from a start-setting interpretation without supplying any generated points.
- Figure 5 top: \(\phi=30^\circ\), fix \(\theta_A=0^\circ\), scan
  \(\theta_B\).
- Figure 5 bottom: \(\phi=30^\circ\), fix \(\theta_B=0^\circ\), scan
  \(\theta_A\).

A \(180^\circ\) shift changes a measurement ket's sign but leaves its
projector unchanged. All probability and Wigner curves must therefore be
\(180^\circ\)-periodic.

## 6. Fidelity Check

The results text compares the fitted density matrix with the singlet. At
\(\xi=\pi\),

\[
|\langle\psi^-|\Psi(w,\pi)\rangle|^2
=\frac12+\sqrt{w(1-w)}.
\]

Thus

\[
F_{\psi^-}
=v\left(\frac12+\sqrt{w(1-w)}\right)+\frac{1-v}{4}.
\]

The rounded Figure 3 parameters give \(F=0.985\), exactly as reported.
The other two-decimal fit parameters lead to small differences from the
reported fidelities; those are retained as an explicit rounding/evidence
boundary rather than removed by refitting.

## Verification Evidence

- Source trace: frozen PDF and TeX, Eqs. (5), (7)-(10), (18), (20), (21).
- Independent symbolic checks:
  `outputs/checks/formula_symbolic_checks.json`.
- Machine formula gate:
  `outputs/checks/formula_verification.json`.
- Generated equation view: `DERIVATION.md` (created from
  `EQUATION_CARDS.json`; never edited by hand).
