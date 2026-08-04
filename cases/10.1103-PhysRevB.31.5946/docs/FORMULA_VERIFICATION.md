# Formula verification

EQ001, EQ002, and EQ006 are source-traced and independently derivable. EQ003,
EQ004, and EQ005 are source-only for their full numerical use. All cards are
open for the scope they declare.

Formula closure does not close the stochastic method gate. In particular,
Fig. 15's `R` inconsistency and the missing raw MC arrays prevent paper-exact
numeric judging for frozen tasks 7–10.

```bash
python private validation harness/scripts/check_formula_gate.py case/10.1103-PhysRevB.31.5946 --write
```
