# Formula Verification

- Eq. (9) is source-traced and its unitary normalization is tested.
- Eq. (10) is independently obtained by dropping off-diagonal Pauli-basis
  terms from Eq. (9).
- At `theta=0.05`, the derived X and Z probability is
  `0.024270800923008887`, agreeing with the paper's rounded `0.0243`.
- The formula gate does not certify the proxy circuit as the unpublished
  Plaquette circuit.  Circuit equivalence is a separate open method question.

This document explains which formulas are allowed to feed numerical reproduction.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python private validation harness/scripts/check_formula_gate.py case/<paper-id> --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
