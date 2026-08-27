# Formula Verification

This case uses `EQUATION_CARDS.json` as the machine-readable formula map.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2605.25594 --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| FS001 | Eigenstate fidelity susceptibility | verified | Defines unregularized eigenstate sensitivity to perturbation. |
| FS002 | Regularized susceptibility kernel | verified | Defines finite-frequency cutoff kernel. |
| FS003 | Average and typical susceptibility | verified | Defines average and typical sensitivity observables. |
| FS004 | 3D Anderson Hamiltonian | verified | Defines open-boundary cubic Anderson model. |
| FS005 | Perturbation operators | verified | Defines perturbations used by susceptibility targets. |
| FS006 | Rescaled susceptibility | verified | Defines plotted rescaled observables. |
| FS007 | Spectral function mechanism | verified | Defines spectral-function diagnostic for mechanism figures. |
| FS008 | Perturbative Ts trend | reconstructed | Defines localized-regime perturbative trend proxy. |

## Closed Or Unclear Formulas

None in the current local feature-level reproduction.
