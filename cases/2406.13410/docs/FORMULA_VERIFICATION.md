# Formula Verification

Machine result: `outputs/checks/formula_verification.json`.

| Formula lane | Cards | Gate | Boundary |
| --- | --- | --- | --- |
| Resonance statistics | EQ001–EQ003 | open | Analytic GOE/Poisson references; no experimental array |
| Ion energy/trap | EQ004–EQ007 | open, reconstructed method | Exact author MD inputs and code withheld |
| Density/classical TBR | EQ008–EQ009 | open | Absolute Fig. 4 height uses declared typical density |
| Polarization capture | EQ010–EQ013 | open, independently derived | Atom-dimer absolute scale not printed |
| Quantum recombination | EQ014–EQ017 | open | s-wave printed fit values; f-wave short-range coupling reconstructed |

An open formula gate means the code may evaluate the declared equation.  It
does not mean parameters are paper-exact or that a target is complete.  Those
are separate authority dimensions.

Run:

```bash
PYTHONPATH=kernel:PRAgent-workflow python PRAgent-workflow/scripts/check_formula_gate.py case/2406.13410 --write
```
