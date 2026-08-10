# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Independent check |
| --- | --- | --- | --- |
| EQ001 | symmetric spin basis and ladder operators | open | spin commutator and source-typo resolution |
| EQ002 | collective Lindblad superoperator | open | trace preservation under vectorization |
| EQ003 | time propagation and FFT | open | initial condition, trace, real observable |
| EQ004 | spectrum, gaps, and decay rates | open | eigenpair residuals |
| EQ005 | stationary state and moments | open | stationarity, trace, Hermiticity, positivity |
| EQ006 | thermodynamic ODE | open | symbolic sphere-norm conservation and numeric drift |
| EQ007 | phase coordinates and conserved field | open | direct formula evaluation and independent ODE paths |

All seven cards require both a source trace and a symbolic, limiting, normalization,
or numerical sanity check. The gate currently reports `7/7` open with no failed check.

Run:

```bash
PYTHONPATH=PRAgent-workflow python PRAgent-workflow/scripts/check_formula_gate.py case/1708.05014 --write
```

## Explicit Ambiguities

- EQ001 corrects the missing `i` in the source definition of `S±`.
- EQ005 records both interpretations of Supplement Fig. S2 right rather than using
  the figure pixels to choose a numerical input.
- Quantum finite-size formulas are verified, but their current run parameters are
  reduced; formula validity does not promote those targets to paper-exact status.
