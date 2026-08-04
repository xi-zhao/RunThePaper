# Formula verification

Machine-readable result: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Evidence |
| --- | --- | --- | --- |
| EQ001 | Wilson action | open | source trace, cold-field normalization, local delta test |
| EQ002 | modified Z4 action | open | source trace, brute-force local delta test |
| EQ003 | monopole-suppressed Z3 action | open | source trace, brute-force local delta test |
| EQ004 | principal flux/cube charge | open | Bianchi divisibility and pure-gauge tests |
| EQ005 | susceptibility | open | source trace and variance normalization check |
| EQ006 | finite-torus correlator ratio | open | source trace and exact L=16 numerical identity |

No formula is closed. An open formula gate does not imply that Monte Carlo
statistics or paper-level coverage have passed.

Run:

```bash
python private validation harness/scripts/check_formula_gate.py case/2505.00079 --write
```
