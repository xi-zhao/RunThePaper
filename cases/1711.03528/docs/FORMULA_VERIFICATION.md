# Formula Verification

This case uses `EQUATION_CARDS.json` as the machine-readable formula map.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/1711.03528 --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| PXP001 | PXP Hamiltonian | verified | Defines constrained Rydberg blockade Hamiltonian. |
| PXP002 | Z2 product state | verified | Defines the special initial density-wave state. |
| PXP003 | Particle-hole symmetry | verified | Checks chiral particle-hole symmetry of the constrained Hamiltonian. |
| PXP004 | Forward scattering approximation | verified | Defines the FSA basis and tridiagonal effective Hamiltonian. |
| PXP005 | Entanglement and revival diagnostics | verified | Defines dynamics diagnostics used by the reproduction. |
| PXP006 | Level statistics | verified | Defines level-statistics target. |

## Closed Or Unclear Formulas

None in the current local feature-level reproduction.
