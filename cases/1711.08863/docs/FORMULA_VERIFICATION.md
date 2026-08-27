# Formula Verification

This document explains which formulas are allowed to feed numerical reproduction.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/<paper-id> --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQ001 | two-atom waveguide master equation | open | Source equation and symbol meanings are traced. |
| EQ002 | general connection-point sums | open | Direct point-pair sums are checked both for Fig. 2 and arbitrary unequal-rate point sets. |
| EQ003 | equal-spacing Table-I formulas | open | Closed forms agree with EQ002 to `8.9e-16`. |
| EQ004 | braided decoherence-free point | open | Direct substitution gives `g/gamma=1` and all decay coefficients zero. |
| EQ005 | general zero-decay factorization | open | Expanding `A_j A_k*` reproduces the collective cosine sum exactly; unequal-rate numerical checks agree. |
| EQ006 | protected-chain all-N rank witness | open | The even-column minor is exactly the identity, proving rank `N` and `N-1` independent controls. |
| EQ007 | all-to-all all-N rank witness | open | The first `N` columns form a unit upper-triangular minor; both printed `N=3` constructions pass. |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| None in the fixed four-item denominator | T001-T004 each have a verified formula path, generated evidence, and an isolated run attestation. | Scientific item coverage is 4/4; fresh-context review remains a separate lifecycle gate. |

The source formulas, independent derivations, executable checks, output hashes,
and isolated file-access attestation are available for all four items.  No
source pixels or author arrays enter the numerical or analytic generators.

## Paper-Audit Finding Outside the T001 Gate

Supplement Eq. (S21), `ME2AtomsMirror`, prints the `gamma_2` decay term as
`D[sigma_-^a]`; expanding its preceding collapse operator and taking the
`gamma_1=0` limit both require `D[sigma_-^b]`. This likely local symbol typo is
not a dependency of Main Fig. 2, whose Table-I coefficients remain verified.
It is formally recorded as protocol-v2 `inconclusive` in
`outputs/checks/paper_review_protocol_v2.json`; no paper-error candidate is
claimed before fresh review.
