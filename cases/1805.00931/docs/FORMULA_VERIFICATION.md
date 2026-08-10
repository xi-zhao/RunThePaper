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
| EQ001 | kicked-Ising Floquet operator | verified | Source trace, factorization, and small-chain unitarity pass. |
| EQ002 | spectral form factor | verified | Eigenvalue power sums match direct matrix powers. |
| EQ003 | Gaussian disorder average | verified | Distribution and frozen sample-moment checks pass. |
| EQ004 | finite-N COE curve | verified | Printed branch and continuous complementary branch checked. |
| EQ005 | space-time transfer representation | verified | Matrix-free action matches explicit Kronecker action. |
| EQ006 | Gaussian dephasing contraction | verified | Characteristic-function derivation and limits pass. |
| EQ007 | transfer spectral gap | verified | Projected Arnoldi agrees with full small-`t` diagonalization. |
| EQ008 | multiplicity/thermodynamic SFF | verified | Dihedral Gram ranks and exceptional sectors reproduce Table I. |
| EQ009 | numerical algorithm route | verified | Equivalent observables and deterministic checks pass. |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| None | All nine declared gates are open. | Scale, rather than formula uncertainty, blocks paper-exact Figures 2/3. |
