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
| EQC001 | projector mismatch | open | source form factor plus Pauli identity |
| EQC002 | small-\(q\) metric | open | source expansion plus Taylor derivation |
| EQC003 | normalized jump moment | open | angular prefactor checked |
| EQC004 | topology and normalization | open | projector convention reconciles the stated bound |
| EQC005 | model and Chern discretization | open | source model plus constant-map limiting check |
| EQC006 | LLG flow | open | Pauli-commutator reduction and tangent norm identity verified |
| EQC007 | Lyapunov rule | open | commutator cancellation and projected norm-square derivation verified |
| EQC008 | paper momentum-local bath | open | same-momentum index structure independently checked |
| EQC009 | Ohmic matrix-space kernel | open | positivity and zero-coupling limits independently checked |
| EQC010 | independent density probe | open | density-operator basis change verified |
| EQC011 | calibrated spectral sum | open | Fermi-golden-rule kernel and closure checked |
| EQC012 | conditional topology bound | open | reduces to EQC003–EQC004 |
| EQC013 | texture-blind paper-bath control | open | Hilbert–Schmidt completeness checked |
| EQC014 | raw-rate and orbital-vertex limits | open | coupling, temperature, and \(q=0\) limits checked |
| EQC015 | exact extended-Hubbard field | open | functional variation, five-moment convolution, and constant-texture limit checked |
| EQC016 | extended-Hubbard \(\lambda_D\) | open | radial integral and reported value checked |
| EQC017 | trace-condition deviation | open | Pauli geometry and pointwise inequality checked |

## Closed Or Unclear Formulas

None of the seventeen declared formula cards is closed. This does **not** make
the raw-click hypothesis valid: EQC008–EQC009 show that the paper derives no
Lindblad unraveling, while EQC013–EQC014 explicitly reject a topology-only
bound on its raw activity. The open formula gate means those rejection tests
are traceable and executable.
