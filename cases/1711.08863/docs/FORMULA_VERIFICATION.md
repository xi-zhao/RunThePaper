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
| EQ002 | general connection-point sums | open | Independently implemented from ordered point pairs. |
| EQ003 | equal-spacing Table-I formulas | open | Closed forms agree with EQ002 to `8.9e-16`. |
| EQ004 | braided decoherence-free point | open | Direct substitution gives `g/gamma=1` and all decay coefficients zero. |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| None | All numerical dependencies are verified. | No formula-level blocker. |

## Paper-Audit Finding Outside the T001 Gate

Supplement Eq. (S21), `ME2AtomsMirror`, prints the `gamma_2` decay term as
`D[sigma_-^a]`; expanding its preceding collapse operator and taking the
`gamma_1=0` limit both require `D[sigma_-^b]`. This likely local symbol typo is
not a dependency of Main Fig. 2, whose Table-I coefficients remain verified.
It is formally recorded as protocol-v2 `inconclusive` in
`outputs/checks/paper_review_protocol_v2.json`; no paper-error candidate is
claimed before fresh review.
