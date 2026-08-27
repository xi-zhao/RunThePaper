# Runnable code for 2607.23978

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.23978/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Remaining lifecycle boundaries: numerical_scope=incomplete, parameters=mixed, causal_resolution=repair_required, science=pending, pixel=missing, paper_assessment=inconclusive.
