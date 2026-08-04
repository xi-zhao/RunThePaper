# Formula Verification

Machine-readable gate: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Main verification |
| --- | --- | --- | --- |
| EQ001 | thermal occupation / Fig. 1 | open | source trace, particle-hole identity, limits |
| EQ002 | P/W/Q supernumbers | open | source trace, Berezin normalization, body spacing |
| EQ003 | majorization | open | nilpotent Taylor identity and body intervals |
| EQ004 | covariance moments | open | `det sigma_y=-1` and exact minima |
| EQ005 | Rényi/Shannon entropy | open | Berezin power integral and `r->1` limit |
| EQ006 | bounds/crossings | open | exact extrema and `n=1/4,1/2,3/4` substitutions |
| EQ007 | thermal loss channel | open | endpoint limits and `S_2=ln(2.5)` benchmark |

All `7/7` cards are source-traced and independently checked; none is merely
copied into code without a symbolic, limiting, normalization, or numerical
sanity gate. There are no closed formulas or method ambiguities affecting the
two figures.

Run:

```bash
python3 private validation harness/scripts/check_formula_gate.py case/2401.08523 --write
```
