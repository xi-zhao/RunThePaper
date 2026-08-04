# Derivation Trace

## Reproduction object

The eight frozen panels do not simulate density-matrix trajectories. They
evaluate resource bounds for four Trotter-Suzuki product formulas. Each panel
plots four integer-valued series against the number of Liouvillian terms \(M\):
\(N^{analytic}\), \(N^{min}\), \(g^{analytic}\), and \(g^{min}\).

The paper parameters are used literally:

- XX chain: \(t=2\), \(\epsilon=10^{-3}\), reported
  \(\lambda=7.071\), \(P=2,\ldots,8\), and \(M=2P+3\);
- TFIM: \(t=5\), \(\epsilon=10^{-5}\), reported
  \(\lambda=8.00\), \(n=2,\ldots,6\), and
  \(M=(5,8,12,15,19)\).

## EQ-PRECISION-FUNCTIONS

Let \(x=t\lambda M>0\). Table 1 gives one \(N^{-1}\) and three
\(N^{-2}\) error functions:

\[
\hat\epsilon_{1,\mathrm{det}}=\frac{x^2}{N}e^{x/N},\quad
\hat\epsilon_{1,\mathrm{ran}}=\hat\epsilon_{2,\mathrm{det}}
=\frac{x^3}{3N^2}e^{x/N},\quad
\hat\epsilon_{2,\mathrm{ran}}
=\frac{(t\lambda)^3M^2}{N^2}e^{x/N}.
\]

For the generic form \(A N^{-p}e^{x/N}\),

\[
\frac{d}{dN}\log\hat\epsilon=-\frac{p}{N}-\frac{x}{N^2}<0.
\]

The error is therefore strictly decreasing on positive \(N\). This proves that
there is a unique smallest integer satisfying
\(\hat\epsilon(N)\le\epsilon\), which is the object found by the binary search.
The implementation compares logarithms so the initial doubling phase is not
affected by floating-point exponential overflow.

## EQ-ANALYTIC-BOUNDS

Impose \(N\ge x\), hence \(e^{x/N}\le e\). Applying this to each precision
function gives the sufficient algebraic conditions

\[
N\ge \frac{ex^2}{\epsilon},\qquad
N\ge\sqrt{\frac{ex^3}{3\epsilon}},\qquad
N\ge\sqrt{\frac{e(t\lambda)^3M^2}{\epsilon}},
\]

for first-order deterministic, first-order randomised/second-order
deterministic, and second-order randomised formulas, respectively. Taking the
maximum with \(x\) and the ceiling yields Eqs. (14), (20), (22), and (24).
Every generated row checks the original precision function at the resulting
integer rather than trusting the derivation alone.

## EQ-LAMBERT-W-CROSSCHECK

The paper uses binary search; an independent continuous solution is useful as a
check. Set \(y=x/N\). For the \(N^{-1}\) error,
\(y e^y=\epsilon/x\), so

\[
N_*=\frac{x}{W(\epsilon/x)}.
\]

For \(\hat\epsilon=A N^{-2}e^{x/N}\),

\[
\left(\frac{y}{2}\right)e^{y/2}
=\frac{x}{2}\sqrt{\frac{\epsilon}{A}},\qquad
N_*=\frac{x}{2W\!\left(\frac{x}{2}\sqrt{\epsilon/A}\right)}.
\]

All arguments are positive, so the principal branch is unambiguous. Strict
monotonicity implies \(N^{min}=\lceil N_*\rceil\). Each target checks this
identity independently of the binary-search control flow.

## EQ-GATE-COMPLEXITY

The first-order formulas contain \(M\) exponentials per step, while the
symmetric second-order formulas contain a forward and reverse \(M\)-term
product. Thus

\[
g_{1,\mathrm{det}}=g_{1,\mathrm{ran}}=MN,\qquad
g_{2,\mathrm{det}}=g_{2,\mathrm{ran}}=2MN.
\]

All gate counts use exact integer arithmetic.

## Model-parameter boundary

The plotted panels treat the paper's reported \(\lambda\) values as fixed
parameters. A separate consistency check reconstructs the local Choi-bound
calculation and records whether it reproduces those reported inputs. Any such
method-level discrepancy is reported explicitly; it does not feed source pixels
or author result data into the generated panel series.

## EQ-CHOI-DIAMOND-BOUND

For the parameter audit, each one- or two-site generator is converted to its
column-vectorized superoperator, then to an unnormalised Choi matrix. The
positive-semidefinite square roots in Eq. (32) are evaluated by Hermitian
eigendecomposition, followed by the second-factor partial trace and spectral
matrix norm. This local reconstruction is deterministic and independent of
author result files. Its result is recorded separately from all eight panel
datasets.
