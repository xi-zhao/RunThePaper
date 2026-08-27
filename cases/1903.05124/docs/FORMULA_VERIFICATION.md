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
| EQC001 | naive decoupling | open/trusted | Source exponent and algebraic threshold independently checked. |
| EQC002 | tight decoupling | open/trusted | Haar-contraction cancellation and limiting cases checked. |
| EQC003 | frame potential | open/trusted | Definition, composite-depth reduction, and Haar moments checked. |
| EQC004 | Clifford trace | open/trusted | Fixed-Pauli kernel and sign-pairing identity derived. |
| EQC005 | stabilizer entropy | open/trusted | Partial-trace rank formula derived and product/Bell limits checked. |
| EQC006 | dynamic observables | open/trusted | Timing, sign, normalization, and bounds are fixed. |
| EQC007 | half-chain scaling | open/trusted | Critical subtraction and asymptotic phases checked. |
| EQC008 | tripartite information | open/trusted | Entropy combination and scaling variable checked. |
| EQC009 | channel capacity | open/trusted | Degradability and block-diagonal entropy identity derived. |
| EQC010 | critical logarithm | open/trusted | `p=p_c` limit reduces the ansatz to a logarithmic slope. |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| — | No formula dependency is closed. | All six targets may run at exploratory scale. |

`outputs/checks/formula_verification.json` reports `10/10` cards open. Method
cards remain `reconstructed`, so exploratory execution is allowed while final
execution waits for independent implementation tests and convergence checks.
