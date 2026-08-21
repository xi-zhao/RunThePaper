# Method Trace

| Method | Role | Independent check | Code |
| --- | --- | --- | --- |
| NUM001 | Critical-safe analytic amplitude | pseudomode ODE | `src/open_qsl/model.py` |
| NUM002 | Population total variation | doubled time grid | `src/open_qsl/model.py::averaged_norms` |
| NUM003 | Schatten norms | direct matrix SVD | `scripts/run_reproduction.py` |
| NUM004 | QSL and figure sweep | Markovian limit and hierarchy | `scripts/run_reproduction.py` |
| NUM005 | Formula discrepancy audit | exact 2x2 counterexamples | `tests/test_model.py` |

The renderer consumes the frozen CSV files and verifies their hashes before and after plotting.
