# Runnable code for 1803.01876

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1803.01876/code
python scripts/run_reproduction.py --config config/implementation_closure.json --output-root outputs/public_quick_run
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: parameters=mixed, causal_resolution=repair_required, science=failed, pixel=missing, paper_assessment=inconclusive.
