# Derivation Trace

## Scope of the Derivation

The selected figures do not simulate a density matrix.  They evaluate resource
bounds built from four paper-stated precision guarantees.  The imported
Trotter-error guarantees are treated as theorems from Table 1; this trace
independently verifies every algebraic step used to turn them into plotted
integers and gate counts.

Let

\[
a=t\lambda M>0.
\]

For all four methods the acceptance predicate is
`epsilon_hat(t, lambda, M, N) <= epsilon`, with integer `N >= 1`.

## Shared Monotonicity Check

Each precision function has the form

\[
f(N)=C N^{-p}\exp(a/N),\qquad C>0,\quad p\in\{1,2\}.
\]

For real `N>0`,

\[
\frac{d}{dN}\log f(N)=-\frac{p}{N}-\frac{a}{N^2}<0.
\]

Thus every precision function is strictly decreasing in `N`.  This proves the
single-threshold property required by bracketing and lower-bound binary search:
once an integer passes, every larger integer passes.

## Error Functions

### EQ-ERR-DET1

Table 1 gives

\[
\hat\epsilon_{1,\mathrm{det}}=\frac{a^2}{N}e^{a/N}.
\]

It is positive, dimensionless, strictly decreasing, diverges as `N -> 0+`, and
tends to zero as `N -> infinity`.

### EQ-ERR-RAN1 and EQ-ERR-DET2

Table 1 gives the same precision function for first-order randomised and
second-order deterministic TS-PF:

\[
\hat\epsilon_{1,\mathrm{ran}}
=\hat\epsilon_{2,\mathrm{det}}
=\frac{a^3}{3N^2}e^{a/N}.
\]

The identity implies identical `N_analytic` and `N_min` sequences for those two
methods at a common parameter set.  Their gate counts differ because their
per-step exponential counts differ.

### EQ-ERR-RAN2

Table 1 gives

\[
\hat\epsilon_{2,\mathrm{ran}}
=\frac{(t\lambda)^3M^2}{N^2}e^{a/N}.
\]

This has the same strictly decreasing `N^{-2} exp(a/N)` structure.  Relative
to the previous `a^3/(3N^2)` numerator, its explicit `M^2` rather than `M^3`
scaling explains the improved large-`M` behaviour.

## Analytic Sufficient Bounds

The paper controls the exponential by imposing `N >= a`.  Then `a/N <= 1`
and `exp(a/N) <= e`.

### EQ-N-DET1

For first-order deterministic TS-PF,

\[
\hat\epsilon_{1,\mathrm{det}}
\le \frac{e a^2}{N}.
\]

Therefore `N >= e a^2 / epsilon` is sufficient.  Enforcing both conditions
and integer `N` gives

\[
N^{\mathrm{analytic}}_{1,\mathrm{det}}
=\left\lceil\max\left\{a,\frac{ea^2}{\epsilon}\right\}\right\rceil.
\]

### EQ-N-RAN1 and EQ-N-DET2

For the shared `N^{-2}` error function,

\[
\hat\epsilon\le\frac{ea^3}{3N^2}\le\epsilon
\quad\Longleftarrow\quad
N\ge\sqrt{\frac{ea^3}{3\epsilon}}.
\]

Hence

\[
N^{\mathrm{analytic}}_{1,\mathrm{ran}}
=N^{\mathrm{analytic}}_{2,\mathrm{det}}
=\left\lceil\max\left\{a,
\sqrt{\frac{ea^3}{3\epsilon}}\right\}\right\rceil.
\]

### EQ-N-RAN2

Similarly,

\[
\hat\epsilon_{2,\mathrm{ran}}
\le\frac{e(t\lambda)^3M^2}{N^2}\le\epsilon
\]

is guaranteed by

\[
N^{\mathrm{analytic}}_{2,\mathrm{ran}}
=\left\lceil\max\left\{a,
\sqrt{\frac{e(t\lambda)^3M^2}{\epsilon}}\right\}\right\rceil.
\]

Every expression is dimensionless because `t*lambda` is dimensionless, `M`
is a count, and `epsilon` is a norm tolerance.

## Integer Minimum and Search Invariant

The intended numerical object is

\[
N_{\min}=\min\{N\in\mathbb{N}_{\ge1}:\hat\epsilon(N)\le\epsilon\}.
\]

The verified implementation uses two phases:

1. start at `upper=1` and double until the predicate passes;
2. maintain a half-open logical invariant: every integer below `lower` fails,
   while `upper` passes; when `mid` passes set `upper=mid`, otherwise set
   `lower=mid+1`.

Termination at `lower == upper` returns the least passing integer.  Each output
is checked with both sides of the threshold:

- `epsilon_hat(N_min) <= epsilon`;
- `N_min == 1` or `epsilon_hat(N_min - 1) > epsilon`.

This lower-bound form implements the stated minimisation exactly and avoids the
`upper = mid - 1` off-by-one risk in a literal reading of Appendix A. The
current/pass and predecessor/fail certificates establish the result directly;
no external implementation is used as evidence.

## Gate Counts

Table 1 defines the plotted gate-complexity proxy as the number of exponentials
per Trotter step times `N`:

\[
g_{1,\mathrm{det}}=g_{1,\mathrm{ran}}=MN,
\qquad
g_{2,\mathrm{det}}=g_{2,\mathrm{ran}}=2MN.
\]

Consequently, equal `N` for first-order randomised and second-order
deterministic TS-PF implies exactly a factor of two in their gate counts.

## Parameter and Series Mapping

- Fig. 2: `t=2`, `lambda=7.071`, `epsilon=1e-3`,
  `M=[7,9,11,13,15,17,19]`.
- Fig. 3: `t=5`, `lambda=8.00`, `epsilon=1e-5`,
  `M=[5,8,12,15,19]`.

For each `(model, method, M)` row the implementation evaluates one error
function, one analytic bound, the exact integer minimum, and two gate counts.
The four visible series are written as structured data before plotting.

## Code Mapping

All cards point to the independent implementation in
`src/trotter_bounds.py`.  The guarded entry point will be
`scripts/run_target.py`, which requires an explicit frozen target and refuses
to run unless it matches `PRAGENT_GUARDED_TARGET_ID`.

## Open Scientific Boundary

The case reproduces the paper's bound-evaluation figures, not an independent
full-channel diamond-norm simulation.  The paper-reported `lambda` values are
therefore paper parameters for the selected targets.  Their local Choi-bound
construction is audited separately and cannot be replaced by values inferred
from source-figure pixels.
