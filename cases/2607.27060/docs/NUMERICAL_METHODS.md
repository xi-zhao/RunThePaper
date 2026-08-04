# Numerical Methods

## Shared numerical object

Each target evaluates one precision function on the paper's finite \(M\) grid.
The analytic series is a direct integer evaluation of the sufficient bound.
The optimised series is found with a monotone lower-bound binary search. Gate
counts are exact integer conversions.

## Target contract

- **Parameters:** XX uses \(t=2,\epsilon=10^{-3},\lambda=7.071\),
  \(P=2,\ldots,8\), \(M=2P+3\). TFIM uses
  \(t=5,\epsilon=10^{-5},\lambda=8\), \(n=2,\ldots,6\),
  \(M=(5,8,12,15,19)\).
- **Solver:** log-domain doubling plus integer lower-bound binary search.
- **Tolerance:** none for integer selection; inequalities are evaluated in
  double-precision logarithmic form.
- **Random seed:** not applicable; the plotted error bounds are deterministic
  even for randomised product formulas.
- **Output schema:** CSV rows contain size, \(M\), the four plotted series,
  precision at each selected integer, the continuous Lambert-\(W\) threshold,
  and evaluation count.
- **Validation:** analytic sufficiency, integer minimality, Lambert-\(W\)
  agreement, gate-count identity, ordering, monotonicity, and cross-method
  resource-ranking checks.

## Authorization boundary

`code/scripts/run_target.py --target <id>` rejects direct use unless the
Harness supplies the same `PRAGENT_GUARDED_TARGET_ID` and the stage is
`final_reproduction`. One invocation writes only that target's CSV, check JSON,
and PNG.

## Complexity and performance

Every search takes \(O(\log N^{min})\) scalar log-error evaluations. The whole
frozen scope contains 48 plotted points and is local CPU work measured in
seconds; the eight scientific runs took 1.130575 wall seconds and the recorded
final computation subtotal was 12.704720 seconds. Acceleration and external
compute would add no scientific value.

## Cross-method claim result

The second-order randomised method has the smallest \(N\) at all 48 points.
Its \(2MN\) gate multiplier creates crossovers, so it has the smallest gate
count only for XX \(M\ge13\) and TFIM \(M\ge15\). This finding is checked in
`outputs/checks/cross_target_consistency.json`.
