# Runnable code for 1811.08017

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1811.08017/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: The isolated runner recorded zero access to paper and original-figure paths. The body-text propane speedup 591x differs from the current formula result and abstract value 1591x; protocol-v2 keeps the discrepancy inconclusive. Fresh inventory-first independent scientific review is still pending; no paper_error_candidate is emitted.
