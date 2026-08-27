# Target Ledger

The identifiers are stable machine keys; the plain-language column is the
reader-facing name.

| Target | Plain-language meaning | Paper item | Gate | Final status | Main evidence |
| --- | --- | --- | --- | --- | --- |
| `T001` | Can signed samples of physical channels implement the fixed nonphysical processor and recover the damped SWAP oscillation? | Main Fig. 2 | 5 formulas and 3 methods verified | reproduced | `t001_final_run.json`, `fig2_swap_dephasing.png` |
| `T002` | How much sampling overhead is needed as error tolerance grows, and why is damping plus coherent \(Z\) rotation harder? | Main Fig. 3 | 7 formulas and 3 methods verified | reproduced | `t002_final_run.json`, `fig3_programming_cost.png` |
| `T008` | Does one fixed processor retrieve convex and signed channel families from declared program states? | Eq. (1) and following definitions | `EQC013`; finite complete-basis check | awaiting fresh review | `implementation_closure.json#target_checks.T008` |
| `T009` | Are the Choi normalization and compatible link contractions internally consistent? | Supplemental Choi/link preliminaries | `EQC002`, `EQC014`; finite tensor check | awaiting fresh review | `implementation_closure.json#target_checks.T009` |
| `T010` | Do the GKSL, Liouville, semigroup, spectral, and Choi conventions agree? | Supplemental GKSL/Liouville preliminaries | `EQC001`, `EQC002`; finite channel check | awaiting fresh review | `implementation_closure.json#target_checks.T010` |
| `T011` | Do the HPTP implementability-cost identities survive finite construction and falsification? | Supplemental physical implementability section | `EQC006`, `EQC010`, `EQC015`; finite cost check | awaiting fresh review | `implementation_closure.json#target_checks.T011` |

## `T001` Acceptance Result

1. Analytic and direct Liouvillian dynamics agree to
   \(3.33\times10^{-16}\): passed.
2. Fixed HPTP processor independently constructed: passed.
3. \(p_+-p_-=1\): passed.
4. \(\kappa=p_++p_-=2\): passed.
5. All sampled points statistically consistent: passed.
6. Source line/marker semantics and pixel contract: passed.

## `T002` Acceptance Result

1. Channel and Choi construction tests: passed.
2. One fixed retrieval map per epsilon and branch: passed.
3. Positivity, trace, and half-diamond constraints: passed.
4. Correct plotted quantity \(\kappa_\epsilon=2^{\gamma_\epsilon}\): passed.
5. Both source-curve landmarks and topology: passed.
6. All 1000 source times certified: passed.
7. Omitted \(t=10\) endpoint sensitivity: passed for all 82 solutions.

## `T008`-`T011` Scope-closure Result

All four fresh-review omissions now have case-local code, frozen parameters,
complete-basis or invariant checks, and one shared clean-room run contract.
Their finite checks are implementation evidence, not general theorem proofs.
In particular, `T011` preserves a strict composition-subadditivity
counterexample for independent adjudication instead of rewriting the paper's
claim on the author side.
