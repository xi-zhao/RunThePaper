# Numerical methods

Run from the repository root:

```bash
python case/prlb-f37350e-051/code/scripts/run_gold_audit.py
python -m pytest -q case/prlb-f37350e-051/code/tests
python case/prlb-f37350e-051/code/scripts/render_idx51_audit.py
```

The asymptotic probe uses 180 decimal digits because `x^2*l1(x)` exposes an
`O(x^-2)` remainder after cancellation of `O(x^2)` terms. Root verification
uses a deterministic scan below `x=1` followed by 300 bisection iterations.
