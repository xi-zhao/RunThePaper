# Derivation Trace

## T001: Hamiltonian-simulation gate counts

1. Normalize each Hamiltonian term and define `lambda=sum(h_j)`,
   `Lambda=max(h_j)`, and term count `L`.
2. For qDRIFT, compose the paper's one-step diamond-distance bound across `N`
   steps. Bracket in float log space, then solve the exponential inequality for
   the smallest integer `N` using 60-digit Decimal boundary checks.
3. For first-order Trotter, evaluate the appendix `a_T` and `b_T` expressions.
   Solve the deterministic and randomized inequalities for the smallest
   integer segment count `r`; total gates are `L*r`.
4. Repeat the exact procedure for Suzuki order indices `k=1,2,3,4`. Each
   segment costs `2*5^(k-1)*L`; select the smallest total independently at every
   plotted time.
5. Evaluate the complete time interval `10^2` through `10^8` at
   `epsilon=10^-3` for every molecule.

## T002: phase-estimation gate counts

The appendix optimizes the per-step errors under a fixed total failure
probability. Substitution yields the two closed resource laws

`N_qD = 133 lambda^2/(delta_E^2 P_f^3)` and
`N_T = 69 L^2 Lambda^(3/2)/(delta_E^(3/2) P_f^2)`.

We evaluate both at `delta_E=10^-4` over `P_f=10^-1...10^-5` for all three
molecules. At `P_f=0.05`, their ratios reproduce `1406,304,789` to rounding.

## Propane body-text inconsistency

At `t=6000`, the printed parameters and exact bounds give a propane speedup of
`1585.08x`. This agrees with the abstract's `1591x` after accounting for the
printed parameter rounding, but not with the body text's `591x`. Carbon dioxide
and ethane reproduce the body values `306x` and `1006x`. This is a stable
discrepancy, not a paper-error verdict. Rounded printed parameters, a single
formula implementation, and the missing fresh reviewer prevent protocol-v2
promotion beyond `inconclusive`, even though the abstract and the other two
molecular panels provide useful consistency checks.
