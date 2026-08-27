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
| EQC001 | Chern equality | open | Patch transformation and closed-loop `grad log r` integral derived. |
| EQC002 | Dirac spectrum/EP positions | open | Pauli-square identity and real/imaginary degeneracy equations checked. |
| EQC003 | Domain-wall matching | open | Exponential ansatz reproduces determinant and continuity conditions. |
| EQC004 | EP dispersion/vorticity | open | Matrix characteristic polynomial and loop winding independently checked. |
| EQC005 | Cylinder Hamiltonian | open | Fourier transform of block hoppings returns Supp. Eq. (13). |
| EQC006 | Hybrid dispersion | open | Orthogonal limiting exponents derived. |
| EQC007 | Codimension/defectiveness | open | Two real constraints and rank-one normal form derived. |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| — | No formula dependency is closed. | T002 is authorized; methods MTH002/MTH003 retain their own pre-execution gates. |
