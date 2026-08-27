# Formula Verification

This case uses `EQUATION_CARDS.json` as the machine-readable formula map.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2605.25398 --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| F001 | Lambda to lambda conversion | open | Algebraic inversion is explicit. |
| F002 | Random-matrix Hamiltonian normalization | open | Code applies the same normalized Hamiltonian family. |
| F003 | Two-photon permanent probability | open | The 2x2 permanent reduction is explicit. |
| F004 | Collision-free conditional normalization | open | Probability vectors normalize over collision-free outputs. |
| F005 | Porter-Thomas dimension and reference | open | `D=C(8,2)=28` is checked. |
| F006 | Shannon entropy and Haar reference | open | Entropy formula and Haar reference are checked. |
| F007 | OTOC short-time scaling | open | Generated slopes match `t^2` and `t^4`. |
| F008 | Participation ratio | open | PR separation passes the feature check. |
| F009 | Fourth-order spectral form factor proxy | open | Local SFF feature aligns with PT/entropy time. |

## Closed Or Unclear Formulas

None in the current feature-level reproduction.
