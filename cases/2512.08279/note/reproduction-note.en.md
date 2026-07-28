# Reproducing PRL 137, 040403: Programmable Open Quantum Systems

## Result

Both numerical main figures are independently reproduced at the paper's
disclosed parameters, with scientific similarity 95/100.

- Main Fig. 2: the derived analytic curve agrees with direct Lindblad
  evolution to \(3.33\times10^{-16}\). The independently constructed fixed
  HPTP processor gives \(p_+=1.5\), \(p_-=0.5\), and sampling overhead
  \(\kappa=2\).
- Main Fig. 3: both 41-point SDP curves pass positivity, trace, diamond-error,
  and monotonicity checks. Every one of the 82 solutions is certified on all
  1000 source-script times.

## Physics

The retrieval operation is fixed; only its program state changes with time.
Allowing a Hermiticity- and trace-preserving retrieval map, implemented by
signed samples of physical channels, makes this possible.

For SWAP evolution plus Bell-basis dephasing, the two superoperators commute,
so the return probability closes analytically:

\[
f(t)=\frac12\left(1+e^{-t/2}\cos2t\right).
\]

The second figure measures the price of approximation. Pure damping reaches
unit overhead once the allowed channel error is about 0.11, whereas damping
plus coherent \(Z\) rotation still costs about 1.207 at error 0.2. Coherent
structure therefore creates a genuine resource burden for a fixed retrieval
map.

## Evidence boundary

The paper does not publish machine-readable curve arrays or a Monte Carlo seed.
Source curves were digitized only after independent generation. Fig. 2 is
assessed statistically; Fig. 3 gives source-curve correlations 0.99974 and
0.99998.

The audit also found that the Supplemental Liouville display has a transpose
placement inconsistent with its own vectorization identity, and that the
released Fig. 3 loop ends at \(t=9.99\) despite allocating \(t=10\). The
source-exact grid is preserved, and the omitted endpoint is separately
verified for every solution.
