# Numerical Methods

## Stable bound evaluation

The error bounds span more than twenty orders of magnitude. Multiplicative
expressions are evaluated in log space. Sums such as `a^2+2b` use a two-term
log-sum-exp, preventing overflow.

## High-precision minimal resource count

For each curve point, a fast IEEE-754 search doubles an upper bracket and then
bisects it. That result is only a candidate: at gate counts near `10^25`, many
adjacent integers share the same float. The v2 implementation therefore
re-brackets the candidate and proves the final `N`/`N-1` boundary with 60-digit
Decimal logarithms.

The runtime check covers, for each molecule at the audit point:

- qDRIFT;
- deterministic first-order Trotter;
- the selected best randomized higher-order Suzuki formula.

Unit regressions also freeze the high-precision propane qDRIFT boundaries at
`t=6000` and `t=10^8`. A separate panel audit recomputes the Fig. 4 closed laws
and their `P_f^-3`/`P_f^-2` slopes without importing author data.

## Grids

- Fig. 2: 121 logarithmic times from `10^2` to `10^8`, plus exact `t=6000`.
- Fig. 4: 121 logarithmic failure probabilities from `10^-1` to `10^-5`, plus
  exact `P_f=0.05`.
- Higher-order curves: exact bounds for Suzuki orders 2, 4, 6, and 8; pointwise
  minimum.

The accepted isolated v2 run completed in 24.28838 s. It used only formula code
and the declared JSON configuration; the source PDF, vector figures, author
arrays, and reference pixels were inaccessible.

## Protocol-v2 boundary

Passing numerical checks establishes reproduction evidence, not a paper verdict.
Implementation or precision failures are `reproduction_defect`; stable
disagreements remain `inconclusive`. Only a fresh inventory-first reviewer may
emit `paper_supported` or `paper_error_candidate`, and the latter additionally
requires paper-exact frozen evidence, convergence, two distinct methods,
explicit falsification, and a quantified strict-reference discrepancy record.
