# Target ledger

| Target | Atomic items | Observable | Paper parameters | W1 status | Direct acceptance signal |
|---|---:|---|---|---|---|
| T001 | 7 | `nu=<K>/N` after J/W: 5 -> 0 | N=50..100 by 10 | covered | monotone N ordering; N=100 fit exponent near 0.58; KZM window reproduced |
| T002 | 4 | low excitation gaps by fermion parity | N=20, J/W in [0,2] | covered, publication-capped | first accessible gap approaches 4 pi W/N near criticality and one-kink energy at J=0 |
| T003 | 4 | tau_Q,99% and fixed-time fidelity | f=0.99; tau_Q=200 hbar/W | covered | tau_Q,99% scales approximately N^1.93; fixed-time fidelity decreases with N |
| T004 | 12 | F1/F2 from A1 and A2 | N=90,70,50,30 | covered | F1 <= exact F <= F2; LZF coefficient is of order 54-59 in the stated regime |
| T005 | 18 | total kinks `<K>` | same six N values | covered | fast-quench saturation, KZM midrange power law, LZF slow-quench envelope |
| T006 | 1 | `nu_LZF / nu_KZM` at `f=0.5` | literal Eq. (15) versus following prose | uncovered | an independent derivation must resolve `0.105723838752` versus approximately `0.14` |

All targets use the open chain printed in Eq. (1). A periodic-chain mode solver is
allowed only as an independent cross-check and is not the primary result.

## T006 causal boundary

- Direct cause: a scientific-result mismatch exists inside the paper source, and
  the current case has no independent scalar artifact.
- Root cause: unresolved (`open`), not yet a paper-error verdict.
- Code-fault status: `not_excluded`, because the existing display generators do
  not test this claim.
- Next test: independent symbolic re-derivation, separate high-precision
  implementation, then fresh-context falsification review.
